"""Install and migrate steps. Each is idempotent and a failing step never aborts a migrate."""
import json
import os

import frappe

MODULE = "Showroom"
ROLES = ["Showroom Manager", "Showroom Salesman", "Showroom Technician", "Showroom Accountant"]
ITEMS = ["Car Sale", "Car Extras"]
COMPONENT = "Showroom Commission"


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True
	return bool(set(frappe.get_roles()) & set(ROLES + ["System Manager"]))


def after_install():
	_all()


def after_migrate():
	_all()


def _all():
	for fn in (ensure_module, ensure_roles, ensure_items, ensure_component, ensure_settings, ensure_crm_fields, refresh_workspace):
		try:
			fn()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"ledgerx_showroom install step failed: {fn.__name__}")
	frappe.clear_cache()


def ensure_module():
	if not frappe.db.exists("Module Def", MODULE):
		frappe.get_doc({"doctype": "Module Def", "module_name": MODULE, "app_name": "ledgerx_showroom"}).insert(ignore_permissions=True)


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def ensure_items():
	group = "Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups"
	uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
	for code in ITEMS:
		if not frappe.db.exists("Item", code):
			frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": code, "item_group": group, "stock_uom": uom, "is_stock_item": 0,
				"is_sales_item": 1, "is_purchase_item": 0, "include_item_in_manufacturing": 0}).insert(ignore_permissions=True)


def ensure_component():
	if not frappe.db.exists("DocType", "Salary Component") or frappe.db.exists("Salary Component", COMPONENT):
		return
	frappe.get_doc({"doctype": "Salary Component", "salary_component": COMPONENT, "salary_component_abbr": "SRC", "type": "Earning",
		"is_additional_component": 1 if frappe.get_meta("Salary Component").has_field("is_additional_component") else 0}).insert(ignore_permissions=True)


def ensure_settings():
	s = frappe.get_doc("Showroom Settings")
	changed = False
	if not s.company:
		s.company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {}, "name")
		changed = bool(s.company)
	if not s.commission_component and frappe.db.exists("Salary Component", COMPONENT):
		s.commission_component, changed = COMPONENT, True
	if changed and s.company:
		s.save(ignore_permissions=True)


def ensure_crm_fields():
	"""When Frappe CRM is installed, a lead or deal can name the car the customer asks about.
	The CRM only shows a custom field once it is in a layout, so the field is also added (once) to the side panel."""
	for dt in ("CRM Lead", "CRM Deal"):
		if not frappe.db.exists("DocType", dt):
			continue
		if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": "interested_car"}):
			frappe.get_doc({"doctype": "Custom Field", "dt": dt, "fieldname": "interested_car", "label": "Car of Interest", "fieldtype": "Link",
				"options": "Car", "insert_after": "status"}).insert(ignore_permissions=True)
		_add_to_side_panel(dt)


def _add_to_side_panel(dt):
	key = "lx_showroom_panel_" + dt.replace(" ", "_").lower()
	name = f"{dt}-Side Panel"
	if frappe.db.get_default(key) or not frappe.db.exists("DocType", "CRM Fields Layout") or not frappe.db.exists("CRM Fields Layout", name):
		return  # done before (an administrator may have removed it on purpose), or the CRM has no such layout yet
	doc = frappe.get_doc("CRM Fields Layout", name)
	layout = json.loads(doc.layout) if doc.layout else []
	if any(isinstance(sec, dict) and "sections" in sec for sec in layout):
		return  # tabbed layout: leave it to the administrator
	for sec in layout:
		for col in sec.get("columns") or []:
			if "interested_car" in [(f.get("fieldname") if isinstance(f, dict) else f) for f in col.get("fields") or []]:
				frappe.db.set_default(key, "1")
				return
	layout.append({"name": "showroom_section", "label": "Showroom", "opened": True, "columns": [{"name": "showroom_column", "fields": ["interested_car"]}]})
	doc.layout = json.dumps(layout)
	doc.save(ignore_permissions=True)
	frappe.db.set_default(key, "1")


def refresh_workspace():
	"""Migrate only re-reads a workspace file that is newer than the saved one: force it."""
	base = os.path.join(frappe.get_app_path("ledgerx_showroom"), "showroom")
	for dt in ("number_card", "dashboard_chart"):
		folder = os.path.join(base, dt)
		for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
			if os.path.isdir(os.path.join(folder, name)):
				frappe.reload_doc("showroom", dt, name, force=True)
	frappe.reload_doc("showroom", "workspace", "showroom", force=True)
