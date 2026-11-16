import frappe
from frappe import _
from frappe.utils import add_days, nowdate


def execute(filters=None):
	filters = filters or {}
	f = {"status": ["in", ["Confirmed", "Delivered"]], "sale_date": ["between", [filters.get("from_date") or add_days(nowdate(), -29), filters.get("to_date") or nowdate()]]}
	for k in ("showroom", "salesman", "financing_type"):
		if filters.get(k):
			f[k] = filters[k]
	cols = [
		{"label": _("Sale"), "fieldname": "name", "fieldtype": "Link", "options": "Car Sale", "width": 130},
		{"label": _("Date"), "fieldname": "sale_date", "fieldtype": "Date", "width": 95},
		{"label": _("Showroom"), "fieldname": "showroom", "fieldtype": "Link", "options": "Showroom", "width": 120},
		{"label": _("Car"), "fieldname": "car", "fieldtype": "Link", "options": "Car", "width": 100},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": _("Salesman"), "fieldname": "salesman", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("How the Customer Pays"), "fieldname": "financing_type", "fieldtype": "Data", "width": 150},
		{"label": _("Price"), "fieldname": "price", "fieldtype": "Currency", "width": 110},
		{"label": _("Car Cost"), "fieldname": "car_cost", "fieldtype": "Currency", "width": 110},
		{"label": _("Margin"), "fieldname": "margin", "fieldtype": "Currency", "width": 110},
		{"label": _("Salesman Commission"), "fieldname": "commission_amount", "fieldtype": "Currency", "width": 120},
	]
	rows = frappe.get_all("Car Sale", filters=f, fields=[c["fieldname"] for c in cols] + ["discount"], order_by="sale_date desc")
	for r in rows:
		r["price"] = (r.price or 0) - (r.discount or 0)
	return cols, rows
