"""Shows the showroom documents in the "Connections" panel of the records they belong to."""
from frappe import _


def _group(data, label, items, fields=None):
	data.setdefault("transactions", [])
	data["transactions"].append({"label": _(label), "items": items})
	if fields:
		data.setdefault("non_standard_fieldnames", {}).update(fields)
	return data


def customer(data=None):
	return _group(data or {}, "Showroom", ["Car Booking", "Car Sale", "Test Drive"])


def employee(data=None):
	return _group(data or {}, "Showroom", ["Car Sale", "Test Drive"], {"Car Sale": "salesman", "Test Drive": "salesman"})


def sales_invoice(data=None):
	return _group(data or {}, "Showroom", ["Car Sale"], {"Car Sale": "sales_invoice"})


def journal_entry(data=None):
	return _group(data or {}, "Showroom", ["Car", "Car Sale"], {"Car": "purchase_entry", "Car Sale": "cogs_entry"})


def payment_entry(data=None):
	return _group(data or {}, "Showroom", ["Car Booking"], {"Car Booking": "deposit_entry"})
