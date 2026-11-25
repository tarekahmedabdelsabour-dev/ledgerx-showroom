import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from ledgerx_showroom.engine import accounting, logic

INSPECTION = ["Engine", "Gearbox", "Suspension and Steering", "Brakes", "Body and Chassis", "Paint", "Interior", "Tires", "Air Conditioning",
	"Electrical and Lights", "Papers and Licensing"]
LOCKED = ("Reserved", "Sold", "Delivered")


class Car(Document):
	def validate(self):
		self.vin = (self.vin or "").strip().upper()
		if self.model and frappe.db.get_value("Car Model", self.model, "make") != self.make:
			frappe.throw(_("The model belongs to another make"))
		if self.year and not (1950 <= int(self.year) <= int(nowdate()[:4]) + 2):
			frappe.throw(_("Check the year"))
		if flt(self.minimum_price) and flt(self.asking_price) and flt(self.minimum_price) > flt(self.asking_price):
			frappe.throw(_("The lowest acceptable price is above the asking price"))
		self.total_cost = logic.r2(flt(self.purchase_price) + sum(flt(c.amount) for c in self.costs))
		self.expected_margin = logic.r2(flt(self.asking_price) - self.total_cost) if flt(self.asking_price) else 0
		if self.is_new() and not self.inspection and self.condition == "Used":
			for i in INSPECTION:
				self.append("inspection", {"item": _(i), "result": "Not Checked"})
		if not self.is_new():
			b = self.get_doc_before_save()
			if b and self.status in ("Sold", "Delivered") and b.status == self.status and (
					flt(b.purchase_price) != flt(self.purchase_price) or b.showroom != self.showroom):
				frappe.throw(_("A sold car can no longer be changed this way"))

	def _need(self, *statuses):
		if self.status not in statuses:
			frappe.throw(_("The car is {0}").format(_(self.status)))

	@frappe.whitelist(methods=["POST"])
	def acquire(self, paid_from=None):
		"""Record the purchase: the price enters the inventory and the money (or the debt) leaves."""
		self.check_permission("write")
		self._need("Draft")
		if flt(self.purchase_price) <= 0:
			frappe.throw(_("Enter the purchase price first"))
		self.purchase_date = self.purchase_date or nowdate()
		entry = accounting.add_to_inventory(self.purchase_price, paid_from or self.purchase_paid_from, self.showroom,
			_("Purchase of car {0} {1}").format(self.name, self.vin), self.purchase_date)
		self.db_set({"purchase_entry": entry, "purchase_paid_from": paid_from or self.purchase_paid_from, "purchase_date": self.purchase_date,
			"status": "In Preparation"})
		self.reload()

	@frappe.whitelist(methods=["POST"])
	def add_cost(self, cost_type, amount, description=None, paid_from=None):
		"""A preparation cost (repair, paint, papers...) adds to the car's cost and to the inventory."""
		self.check_permission("write")
		self._need("In Preparation", "Ready for Sale", "Reserved")
		amount = flt(amount)
		if amount <= 0:
			frappe.throw(_("The amount must be above zero"))
		entry = accounting.add_to_inventory(amount, paid_from, self.showroom, _("{0} for car {1}").format(_(cost_type), self.name))
		self.append("costs", {"cost_date": nowdate(), "cost_type": cost_type, "description": description, "amount": amount, "paid_from": paid_from, "entry": entry})
		self.save(ignore_permissions=True)
		return {"total_cost": self.total_cost}

	@frappe.whitelist(methods=["POST"])
	def mark_ready(self):
		self.check_permission("write")
		self._need("In Preparation")
		if flt(self.asking_price) <= 0:
			frappe.throw(_("Set the asking price first"))
		if self.condition == "Used" and any(i.result == "Not Checked" for i in self.inspection):
			frappe.throw(_("Finish the inspection checklist first"))
		self.db_set("status", "Ready for Sale")

	@frappe.whitelist(methods=["POST"])
	def transfer(self, to_showroom, note=None):
		self.check_permission("write")
		self._need("In Preparation", "Ready for Sale")
		if to_showroom == self.showroom:
			frappe.throw(_("The car is already in this showroom"))
		if flt(self.total_cost):
			accounting.move_inventory(self.total_cost, self.showroom, to_showroom, _("Transfer of car {0}").format(self.name))
		self.append("transfers", {"transfer_date": nowdate(), "from_showroom": self.showroom, "to_showroom": to_showroom, "note": note})
		self.showroom = to_showroom
		self.save(ignore_permissions=True)

	@frappe.whitelist(methods=["POST"])
	def withdraw(self):
		"""Take the car off sale (returned to the seller, scrapped...). Its cost stays in the inventory until you settle it by hand."""
		self.check_permission("write")
		if self.status in LOCKED:
			frappe.throw(_("The car is {0}").format(_(self.status)))
		self.db_set("status", "Withdrawn")
