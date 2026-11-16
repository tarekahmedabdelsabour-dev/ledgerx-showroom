"""Journal entries and payments for the showroom, all on ERPNext's own documents.

Inventory is kept in one asset account: the purchase price and every preparation cost go IN (debit inventory),
the sale takes the car's whole cost OUT (debit cost of cars sold, credit inventory). Each showroom is a cost center."""
import frappe
from frappe import _
from frappe.utils import flt, nowdate

from ledgerx_showroom.engine import logic


def settings():
	return frappe.get_cached_doc("Showroom Settings")


def need(s, field, label):
	if not s.get(field):
		frappe.throw(_("Set {0} in Showroom Settings first").format(_(label)))
	return s.get(field)


def cost_center_of(showroom):
	return frappe.db.get_value("Showroom", showroom, "cost_center")


def journal(rows, remark, posting_date=None):
	"""rows: dicts with account, debit, credit, cost_center. Submits and returns the Journal Entry name."""
	s = settings()
	je = frappe.new_doc("Journal Entry")
	je.update({"voucher_type": "Journal Entry", "company": need(s, "company", "Company"), "posting_date": posting_date or nowdate(), "user_remark": remark})
	for r in rows:
		je.append("accounts", {"account": r["account"], "debit_in_account_currency": flt(r.get("debit")),
			"credit_in_account_currency": flt(r.get("credit")), "cost_center": r.get("cost_center")})
	je.insert(ignore_permissions=True)
	je.submit()
	return je.name


def add_to_inventory(amount, paid_from, showroom, remark, posting_date=None):
	"""A purchase or a preparation cost: cash/bank/payable goes down, the cars inventory goes up."""
	s = settings()
	paid_from = paid_from or need(s, "default_paid_from", "Default Account Money Is Paid From")
	cc = cost_center_of(showroom)
	return journal([
		{"account": need(s, "inventory_account", "Cars Inventory Account"), "debit": amount, "cost_center": cc},
		{"account": paid_from, "credit": amount, "cost_center": cc},
	], remark, posting_date)


def move_inventory(amount, from_showroom, to_showroom, remark):
	"""A car moves between showrooms: its cost leaves one cost center and enters the other."""
	s = settings()
	acc = need(s, "inventory_account", "Cars Inventory Account")
	return journal([
		{"account": acc, "debit": amount, "cost_center": cost_center_of(to_showroom)},
		{"account": acc, "credit": amount, "cost_center": cost_center_of(from_showroom)},
	], remark)


def cost_of_sale(amount, showroom, remark):
	s = settings()
	cc = cost_center_of(showroom)
	return journal([
		{"account": need(s, "cogs_account", "Cost of Cars Sold Account"), "debit": amount, "cost_center": cc},
		{"account": need(s, "inventory_account", "Cars Inventory Account"), "credit": amount, "cost_center": cc},
	], remark)


def _receivable(customer):
	from erpnext.accounts.party import get_party_account

	return get_party_account("Customer", customer, settings().company)


def money_account(mode_of_payment):
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

	acc = (get_bank_cash_account(mode_of_payment, settings().company) or {}).get("account")
	if not acc:
		frappe.throw(_("Mode of Payment {0} has no account for the company").format(mode_of_payment))
	return acc


def payment(customer, amount, account, invoice=None, remarks="", refund=False, fee=0, reference=None):
	"""Receive money from a customer (or pay it back). With an invoice the amount is allocated to it;
	`fee` is what a financier keeps from the transfer (booked to the financier fees account)."""
	s = settings()
	company = s.company
	receivable = _receivable(customer)
	amount, fee = flt(amount), flt(fee)
	pe = frappe.new_doc("Payment Entry")
	pe.update({"payment_type": "Pay" if refund else "Receive", "company": company, "posting_date": nowdate(), "party_type": "Customer",
		"party": customer, "remarks": remarks, "reference_no": reference or remarks[:40] or "-", "reference_date": nowdate()})
	if refund:
		pe.update({"paid_from": account, "paid_to": receivable, "paid_amount": amount, "received_amount": amount})
	else:
		pe.update({"paid_from": receivable, "paid_to": account, "paid_amount": amount, "received_amount": logic.r2(amount - fee)})
		if fee:
			pe.append("deductions", {"account": need(s, "bank_fee_account", "Financier Fees Account"), "cost_center": None, "amount": fee})
	if invoice:
		pe.append("references", {"reference_doctype": "Sales Invoice", "reference_name": invoice, "allocated_amount": amount})
	pe.insert(ignore_permissions=True)
	pe.submit()
	return pe.name
