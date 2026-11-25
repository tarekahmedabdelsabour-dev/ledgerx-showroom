import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def execute(filters=None):
	"""Every unpaid installment (or financier payment) of a car sale, oldest first. Overdue ones are marked."""
	filters = filters or {}
	until = filters.get("until") or add_days(nowdate(), 30)
	args = [until]
	cond = ""
	if filters.get("showroom"):
		cond = " and s.showroom = %s"
		args.append(filters["showroom"])
	rows = frappe.db.sql(
		f"""select s.name as sale, s.customer, s.showroom, s.financing_type, i.name as invoice, p.due_date,
		(p.payment_amount - p.paid_amount) as due
		from `tabPayment Schedule` p join `tabSales Invoice` i on i.name = p.parent
		join `tabCar Sale` s on s.sales_invoice = i.name
		where p.parenttype = 'Sales Invoice' and i.docstatus = 1 and p.payment_amount - p.paid_amount > 0.005 and p.due_date <= %s {cond}
		order by p.due_date""", args, as_dict=True)
	today = getdate(nowdate())
	for r in rows:
		r["late_days"] = max((today - getdate(r.due_date)).days, 0)
	cols = [
		{"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 100},
		{"label": _("Days Late"), "fieldname": "late_days", "fieldtype": "Int", "width": 80},
		{"label": _("Amount Due"), "fieldname": "due", "fieldtype": "Currency", "width": 120},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 170},
		{"label": _("Sale"), "fieldname": "sale", "fieldtype": "Link", "options": "Car Sale", "width": 130},
		{"label": _("Showroom"), "fieldname": "showroom", "fieldtype": "Link", "options": "Showroom", "width": 120},
		{"label": _("How the Customer Pays"), "fieldname": "financing_type", "fieldtype": "Data", "width": 150},
		{"label": _("Invoice"), "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 140},
	]
	return cols, rows
