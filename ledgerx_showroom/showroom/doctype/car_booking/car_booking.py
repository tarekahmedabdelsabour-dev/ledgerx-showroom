import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate

from ledgerx_showroom.engine import accounting


class CarBooking(Document):
	def validate(self):
		if getdate(self.valid_until) < getdate(nowdate()) and self.is_new():
			frappe.throw(_("The booking date has passed"))
		if flt(self.deposit) and not self.mode_of_payment:
			frappe.throw(_("Choose how the deposit was paid"))

	def after_insert(self):
		car = frappe.get_doc("Car", self.car)
		if car.status != "Ready for Sale":
			frappe.throw(_("The car is {0}: only a car that is ready for sale can be booked").format(_(car.status)))
		if flt(self.deposit):
			pe = accounting.payment(self.customer, self.deposit, accounting.money_account(self.mode_of_payment),
				remarks=_("Deposit for car {0}").format(self.car), reference=self.name)
			self.db_set("deposit_entry", pe)
		car.db_set({"status": "Reserved", "booking": self.name})

	def _free_car(self):
		if frappe.db.get_value("Car", self.car, "status") == "Reserved":
			frappe.db.set_value("Car", self.car, {"status": "Ready for Sale", "booking": None})

	@frappe.whitelist(methods=["POST"])
	def cancel_booking(self, refund=0):
		"""Free the car. The deposit is paid back, or stays with the customer as an advance (to be kept by the showroom by hand)."""
		self.check_permission("write")
		if self.status != "Active":
			frappe.throw(_("The booking is {0}").format(_(self.status)))
		if int(refund) and flt(self.deposit):
			accounting.payment(self.customer, self.deposit, accounting.money_account(self.mode_of_payment), refund=True,
				remarks=_("Deposit refund for car {0}").format(self.car), reference=self.name)
		self._free_car()
		self.db_set("status", "Cancelled")
