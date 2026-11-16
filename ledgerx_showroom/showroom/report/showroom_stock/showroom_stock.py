import frappe
from frappe import _
from ledgerx_showroom.engine import logic


def execute(filters=None):
	filters = filters or {}
	f = {}
	for k in ("showroom", "status", "condition", "make"):
		if filters.get(k):
			f[k] = filters[k]
	if not filters.get("status"):
		f["status"] = ["in", ["In Preparation", "Ready for Sale", "Reserved"]]
	cols = [
		{"label": _("Car"), "fieldname": "name", "fieldtype": "Link", "options": "Car", "width": 110},
		{"label": _("Showroom"), "fieldname": "showroom", "fieldtype": "Link", "options": "Showroom", "width": 130},
		{"label": _("Make"), "fieldname": "make", "fieldtype": "Link", "options": "Car Make", "width": 100},
		{"label": _("Model"), "fieldname": "model", "fieldtype": "Data", "width": 110},
		{"label": _("Year"), "fieldname": "year", "fieldtype": "Int", "width": 60},
		{"label": _("Condition"), "fieldname": "condition", "fieldtype": "Data", "width": 80},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Chassis Number (VIN)"), "fieldname": "vin", "fieldtype": "Data", "width": 160},
		{"label": _("Days in Stock"), "fieldname": "days", "fieldtype": "Int", "width": 90},
		{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 110},
		{"label": _("Asking Price"), "fieldname": "asking_price", "fieldtype": "Currency", "width": 110},
		{"label": _("Expected Margin"), "fieldname": "expected_margin", "fieldtype": "Currency", "width": 120},
	]
	rows = frappe.get_all("Car", filters=f, fields=["name", "showroom", "make", "model", "year", "condition", "status", "vin", "purchase_date",
		"total_cost", "asking_price", "expected_margin"], order_by="purchase_date asc")
	for r in rows:
		r["days"] = logic.days_in_stock(r.purchase_date)
	return cols, rows
