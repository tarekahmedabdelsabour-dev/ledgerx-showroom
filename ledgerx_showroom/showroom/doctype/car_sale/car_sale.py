import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from ledgerx_showroom.engine import accounting, logic

CAR_ITEM = "Car Sale"
EXTRAS_ITEM = "Car Extras"


class CarSale(Document):
	def validate(self):
		s = accounting.settings()
		if self.status != "Draft" and not self.is_new():
			return
		car = frappe.db.get_value("Car", self.car, ["status", "minimum_price", "booking", "showroom"], as_dict=True)
		ok_status = car.status == "Ready for Sale" or (car.status == "Reserved" and self.booking and car.booking == self.booking)
		if self.is_new() and not ok_status:
			frappe.throw(_("The car is {0}").format(_(car.status)))
		net = flt(self.price) - flt(self.discount)
		self.below_minimum = 0 if logic.price_allowed(net, car.minimum_price) else 1
		if self.below_minimum and not self.price_reason:
			frappe.throw(_("The price is below the lowest acceptable price of {0}. Write the reason (a manager approves it).").format(car.minimum_price))
		self._apply_plan(net)
		if self.financing_type == "Showroom Installments":
			self.months = int(self.months or s.default_months or 12)
			if self.markup_pct in (None, ""):
				self.markup_pct = flt(s.default_markup_pct)
		t = logic.sale_totals(self.price, self.discount, sum(flt(e.amount) for e in self.extras), s.vat_rate, self.financing_type,
			self.down_payment, self.months, self.markup_pct)
		if self.financing_type != "Cash" and t["financed"] <= 0:
			frappe.throw(_("The down payment covers the whole price: choose Cash"))
		self.extras_total, self.vat, self.cash_total = t["extras"], t["vat"], t["cash_total"]
		self.financed_amount, self.surcharge, self.grand_total, self.monthly_installment = t["financed"], t["surcharge"], t["grand_total"], t["monthly"]

	def _apply_plan(self, net):
		"""A chosen financing plan sets the type, bank, installments and (when empty) the down payment."""
		if not self.financing_plan:
			return None
		plan = frappe.get_doc("Financing Plan", self.financing_plan)
		if not plan.active:
			frappe.throw(_("The financing plan {0} is not active").format(plan.name))
		self.financing_type = plan.financing_type
		self.months = plan.months
		self.financier = plan.financier if plan.financing_type == "Bank Financing" else None
		if plan.financing_type == "Showroom Installments":
			self.markup_pct = plan.markup_pct
		if not flt(self.down_payment) and flt(plan.min_down_pct):
			self.down_payment = round(net * flt(plan.min_down_pct) / 100, 2)
		if net and flt(self.down_payment) < net * flt(plan.min_down_pct) / 100 - 0.005:
			frappe.throw(_("The plan needs a down payment of at least {0}%").format(plan.min_down_pct))
		return plan

	def _need(self, *statuses):
		if self.status not in statuses:
			frappe.throw(_("The sale is {0}").format(_(self.status)))

	@frappe.whitelist()
	def confirm(self):
		"""Invoice the customer, book the cost of the car, and mark it sold."""
		self._need("Draft")
		s = accounting.settings()
		car = frappe.get_doc("Car", self.car)
		if car.status not in ("Ready for Sale", "Reserved"):
			frappe.throw(_("The car is {0}").format(_(car.status)))
		cc = accounting.cost_center_of(car.showroom)
		t = logic.sale_totals(self.price, self.discount, sum(flt(e.amount) for e in self.extras), s.vat_rate, self.financing_type,
			self.down_payment, self.months, self.markup_pct)
		inv = frappe.new_doc("Sales Invoice")
		inv.update({"customer": self.customer, "company": s.company, "posting_date": nowdate(), "due_date": nowdate(), "cost_center": cc,
			"update_stock": 0, "ignore_pricing_rule": 1, "allocate_advances_automatically": 1,
			"selling_price_list": frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name"),
			"remarks": _("Sale of car {0} {1} ({2})").format(car.name, car.vin, self.name)})
		inv.append("items", {"item_code": CAR_ITEM, "qty": 1, "rate": t["net_car"], "cost_center": cc,
			"income_account": accounting.need(s, "sales_income_account", "Car Sales Revenue Account"),
			"description": f"{car.make} {car.model} {car.year} - {_('Chassis')} {car.vin}"})
		for e in self.extras:
			inv.append("items", {"item_code": EXTRAS_ITEM, "qty": 1, "rate": flt(e.amount), "description": e.description, "cost_center": cc,
				"income_account": s.extras_income_account or s.sales_income_account})
		if t["surcharge"]:
			inv.append("items", {"item_code": EXTRAS_ITEM, "qty": 1, "rate": t["surcharge"], "description": _("Installment markup"), "cost_center": cc,
				"income_account": accounting.need(s, "financing_income_account", "Financing Income Account")})
		if t["vat"]:
			inv.append("taxes", {"charge_type": "Actual", "account_head": accounting.need(s, "vat_account", "VAT Account"), "description": _("VAT"),
				"tax_amount": t["vat"], "cost_center": cc})
		for due, amount in logic.payment_schedule(t["grand_total"], self.financing_type, t["down"], t["financed"], t["surcharge"], self.months,
				self.first_due_date, nowdate(), self.financier_due_date):
			inv.append("payment_schedule", {"due_date": due, "payment_amount": amount, "invoice_portion": 0})
		inv.insert(ignore_permissions=True)
		inv.set_advances()  # a booking's deposit (and any other advance of this customer) is applied
		if inv.get("advances"):
			inv.save(ignore_permissions=True)
		inv.submit()

		cost = flt(car.total_cost)
		cogs = accounting.cost_of_sale(cost, car.showroom, _("Cost of car {0} sold ({1})").format(car.name, self.name)) if cost else None
		margin = logic.margin(t["net_car"], cost)
		commission = logic.commission(margin, s.commission_pct)
		self.db_set({"status": "Confirmed", "sales_invoice": inv.name, "cogs_entry": cogs, "car_cost": cost, "margin": margin, "commission_amount": commission})
		car.db_set({"status": "Sold", "sale": self.name})
		if self.booking:
			frappe.db.set_value("Car Booking", self.booking, "status", "Converted")
		if self.financing_type == "Lending Loan":
			self.make_loan_application(s, t)
		self.reload()
		return {"invoice": inv.name}

	def make_loan_application(self, s, t):
		"""A draft Loan Application in the Lending module for the financed amount; approval happens there."""
		product = (frappe.db.get_value("Financing Plan", self.financing_plan, "loan_product") if self.financing_plan else None) or s.loan_product
		if not frappe.db.exists("DocType", "Loan Application") or not product:
			frappe.msgprint(_("The sale is confirmed. Set the Loan Product in Showroom Settings (and install Lending) to create the loan application."))
			return
		app = frappe.get_doc({"doctype": "Loan Application", "applicant_type": "Customer", "applicant": self.customer, "company": s.company,
			"loan_product": product, "loan_amount": t["financed"], "repayment_method": "Repay Over Number of Periods",
			"repayment_periods": int(self.months or s.default_months or 12), "posting_date": nowdate(),
			"description": _("Car {0} - sale {1}").format(self.car, self.name)})
		app.insert(ignore_permissions=True)
		self.db_set("loan_application", app.name)

	@frappe.whitelist()
	def receive_payment(self, mode_of_payment, amount, reference=None):
		"""Down payment or an installment: any amount up to what is still due."""
		self._need("Confirmed", "Delivered")
		out = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "outstanding_amount"))
		amount = flt(amount)
		if amount <= 0 or amount > out + 0.005:
			frappe.throw(_("The amount must be above zero and not more than the {0} still due").format(out))
		return accounting.payment(self.customer, amount, accounting.money_account(mode_of_payment), self.sales_invoice,
			_("Car sale {0}").format(self.name), reference=reference)

	@frappe.whitelist()
	def receive_from_bank(self, mode_of_payment, amount, fee=0, reference=None):
		"""The bank or finance company pays the financed amount (it may keep a fee)."""
		self._need("Confirmed", "Delivered")
		if self.financing_type != "Bank Financing":
			frappe.throw(_("This sale is not financed by a bank"))
		out = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "outstanding_amount"))
		if flt(amount) <= 0 or flt(amount) > out + 0.005:
			frappe.throw(_("The amount must be above zero and not more than the {0} still due").format(out))
		return accounting.payment(self.customer, amount, accounting.money_account(mode_of_payment), self.sales_invoice,
			_("{0} - car sale {1}").format(self.financier or _("Bank"), self.name), fee=fee, reference=reference)

	@frappe.whitelist()
	def settle_from_loan(self, amount=None):
		"""The Lending module paid the loan out: clear that amount from the invoice (through the clearing account)."""
		self._need("Confirmed", "Delivered")
		s = accounting.settings()
		out = flt(frappe.db.get_value("Sales Invoice", self.sales_invoice, "outstanding_amount"))
		amount = flt(amount) or min(flt(self.financed_amount), out)
		if amount <= 0 or amount > out + 0.005:
			frappe.throw(_("The amount must be above zero and not more than the {0} still due").format(out))
		return accounting.payment(self.customer, amount, accounting.need(s, "loan_clearing_account", "Loan Clearing Account"), self.sales_invoice,
			_("Loan {0} - car sale {1}").format(self.loan or self.loan_application or "", self.name), reference=self.loan or self.name)

	@frappe.whitelist()
	def deliver(self):
		self._need("Confirmed")
		self.db_set("status", "Delivered")
		frappe.db.set_value("Car", self.car, "status", "Delivered")

	@frappe.whitelist()
	def cancel_draft(self):
		self._need("Draft")
		self.db_set("status", "Cancelled")
