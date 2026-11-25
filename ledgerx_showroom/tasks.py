import frappe
from frappe.utils import add_months, get_first_day, get_last_day, getdate, nowdate


def expire_bookings():
	"""A booking past its date frees the car again (the deposit stays with the customer as an advance)."""
	for name in frappe.get_all("Car Booking", filters={"status": "Active", "valid_until": ["<", nowdate()]}, pluck="name"):
		try:
			doc = frappe.get_doc("Car Booking", name)
			doc._free_car()
			doc.db_set("status", "Expired")
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Booking expiry failed for {name}")


def monthly_commissions():
	"""On the 1st: last month's commission per salesman, as a draft Additional Salary for HR to review."""
	s = frappe.get_cached_doc("Showroom Settings")
	if not s.commission_component:
		return
	last = add_months(getdate(nowdate()), -1)
	start, end = get_first_day(last), get_last_day(last)
	rows = frappe.db.sql(
		"""select salesman, sum(commission_amount) as total from `tabCar Sale`
		where status in ('Confirmed', 'Delivered') and sale_date between %s and %s and ifnull(salesman, '') != '' group by salesman""",
		(start, end), as_dict=True)
	for r in rows:
		if not r.total or r.total <= 0:
			continue
		try:
			if frappe.db.exists("Additional Salary", {"employee": r.salesman, "salary_component": s.commission_component, "ref_doctype": "Employee",
					"ref_docname": r.salesman, "payroll_date": end, "docstatus": ["<", 2]}):
				continue
			frappe.get_doc({"doctype": "Additional Salary", "employee": r.salesman, "salary_component": s.commission_component, "amount": r.total,
				"payroll_date": end, "company": s.company, "overwrite_salary_structure_amount": 1, "ref_doctype": "Employee",
				"ref_docname": r.salesman}).insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Showroom commission failed for {r.salesman}")
