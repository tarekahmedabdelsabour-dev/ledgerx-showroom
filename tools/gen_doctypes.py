"""Builds every DocType JSON of ledgerx_showroom from the compact table below.
Run from the repo root:  python3 tools/gen_doctypes.py   (rewrites ledgerx_showroom/hotels/doctype/*)"""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "ledgerx_showroom", "showroom", "doctype")
TS = "2026-11-16 08:00:00.000000"
MODULE = "Showroom"

MGR, SAL, TEC, ACC = "Showroom Manager", "Showroom Salesman", "Showroom Technician", "Showroom Accountant"


def f(name, ftype, label=None, **kw):
	d = {"fieldname": name, "fieldtype": ftype}
	if ftype not in ("Section Break", "Column Break", "Tab Break"):
		d["label"] = label or name.replace("_", " ").title()
	elif label:
		d["label"] = label
	d.update(kw)
	return d


def sec(name, label=None, **kw):
	return f(name, "Section Break", label, **kw)


def col(name):
	return f(name, "Column Break")


def perms(*rows):
	out = []
	for role, mode in rows:
		p = {"role": role, "read": 1, "report": 1, "print": 1, "export": 1}
		if mode in ("rw", "rwc", "all"):
			p["write"] = 1
		if mode in ("rwc", "all"):
			p["create"] = 1
		if mode == "all":
			p["delete"] = 1
		out.append(p)
	out.append({"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "print": 1, "export": 1})
	return out


DT = {}


def doctype(name, fields, **kw):
	DT[name] = {"name": name, "fields": fields, **kw}


CUR = {"options": "currency"}

ACCT = lambda n, l, **k: f(n, "Link", l, options="Account", **k)

doctype("Showroom Settings", [
	f("company", "Link", "Company", options="Company", reqd=1),
	f("default_paid_from", "Link", "Default Account Money Is Paid From", options="Account", description="Cash or bank account used for purchases and preparation costs unless another is chosen."),
	col("cb1"),
	f("default_booking_days", "Int", "Booking Holds the Car For (days)", default=3),
	sec("sb_acc", "Accounts"),
	ACCT("inventory_account", "Cars Inventory Account", reqd=1, description="Asset account that holds the cost of cars in stock."),
	ACCT("cogs_account", "Cost of Cars Sold Account", reqd=1),
	ACCT("sales_income_account", "Car Sales Revenue Account", reqd=1),
	col("cb2"),
	ACCT("extras_income_account", "Extras Revenue Account", description="Plates, papers, accessories. Empty: the car sales account."),
	ACCT("financing_income_account", "Financing Income Account", description="The markup charged on the showroom's own installments."),
	ACCT("vat_account", "VAT Account"),
	f("vat_rate", "Percent", "VAT on Cars (%)", default=0),
	sec("sb_fin", "Financing"),
	ACCT("bank_fee_account", "Financier Fees Account", description="Fees the bank or finance company keeps from what it pays."),
	ACCT("loan_clearing_account", "Loan Clearing Account", description="Set this account as the Disbursement Account of the loan product, so a loan paid out to settle a car invoice nets to zero."),
	f("loan_product", "Data", "Loan Product (Lending)", description="Name of the loan product used for loan-financed sales. Leave empty if the Lending module is not used."),
	col("cb3"),
	f("default_markup_pct", "Percent", "Default Markup on Installments (%)", default=0, description="A flat percentage of the financed amount, for the showroom's own installments."),
	f("default_months", "Int", "Default Number of Installments", default=12),
	sec("sb_com", "Commission"),
	f("commission_pct", "Percent", "Salesman Commission (% of the margin)", default=0),
	f("commission_component", "Link", "Salary Component for Commission", options="Salary Component", description="Created on install. Monthly drafts of Additional Salary use it."),
], issingle=1, icon="fa fa-cog", perms=perms((MGR, "rw"), (ACC, "r")))

doctype("Showroom", [
	f("showroom_name", "Data", "Showroom", reqd=1, unique=1, in_list_view=1),
	f("company", "Link", "Company", options="Company"),
	f("cost_center", "Link", "Cost Center", options="Cost Center", reqd=1, description="Every purchase, cost and sale of this showroom is posted to it, so each showroom has its own profit."),
	f("active", "Check", "Active", default=1),
	col("cb1"),
	f("manager", "Link", "Manager", options="Employee"),
	f("city", "Data", "City", in_list_view=1),
	f("phone", "Data", "Phone"),
	f("address", "Small Text", "Address"),
], autoname="field:showroom_name", title_field="showroom_name", icon="fa fa-building", perms=perms((MGR, "all"), (SAL, "r"), (TEC, "r"), (ACC, "r")))

doctype("Car Make", [f("make_name", "Data", "Make", reqd=1, unique=1, in_list_view=1)], autoname="field:make_name", icon="fa fa-tag",
	perms=perms((MGR, "all"), (SAL, "r"), (TEC, "r"), (ACC, "r")))

doctype("Car Model", [
	f("make", "Link", "Make", options="Car Make", reqd=1, in_list_view=1, in_standard_filter=1),
	f("model_name", "Data", "Model", reqd=1, in_list_view=1),
	f("body_type", "Select", "Body", options="\nSedan\nHatchback\nSUV\nCrossover\nCoupe\nVan\nPickup\nBus\nOther"),
], autoname="format:{make}-{model_name}", title_field="model_name", icon="fa fa-car", perms=perms((MGR, "all"), (SAL, "r"), (TEC, "r")))

doctype("Financing Company", [
	f("company_name", "Data", "Name", reqd=1, unique=1, in_list_view=1),
	f("contact", "Data", "Contact Person"),
	f("phone", "Data", "Phone"),
	f("fee_pct", "Percent", "Usual Fee (%)", default=0),
	f("notes", "Small Text", "Notes"),
], autoname="field:company_name", icon="fa fa-university", perms=perms((MGR, "all"), (SAL, "r"), (ACC, "rw")))

doctype("Financing Plan", [
	f("plan_name", "Data", "Plan Name", reqd=1, unique=1, in_list_view=1, description="For example: Own installments 24 months, Banque Misr 60 months, CIB 48 months."),
	f("financing_type", "Select", "Type", options="Showroom Installments\nBank Financing\nLending Loan", default="Showroom Installments", reqd=1, in_list_view=1,
		description="Showroom Installments: the showroom collects. Bank Financing: a bank or finance company pays the showroom. Lending Loan: a loan in the Lending module."),
	f("active", "Check", "Active", default=1),
	col("cb1"),
	f("financier", "Link", "Bank or Finance Company", options="Financing Company", depends_on="eval:doc.financing_type=='Bank Financing'", in_list_view=1),
	f("loan_product", "Data", "Loan Product (Lending)", depends_on="eval:doc.financing_type=='Lending Loan'", description="Leave empty to use the one in Showroom Settings."),
	sec("sb_terms", "Terms"),
	f("months", "Int", "Number of Installments", default=12, in_list_view=1),
	f("min_down_pct", "Percent", "Minimum Down Payment (%)", default=0, in_list_view=1),
	f("markup_pct", "Percent", "Markup on the Financed Amount (%)", default=0, depends_on="eval:doc.financing_type=='Showroom Installments'", description="Charged by the showroom itself."),
	f("notes", "Small Text", "Notes"),
], autoname="field:plan_name", icon="fa fa-percent", perms=perms((MGR, "all"), (SAL, "r"), (ACC, "rw")))

# ---------------------------------------------------------------- the car
doctype("Car Cost", [
	f("cost_date", "Date", "Date", reqd=1, in_list_view=1, default="Today"),
	f("cost_type", "Select", "Type", options="Inspection\nRepair\nPaint\nParts\nPapers and Licensing\nTransport\nCleaning\nOther", default="Repair", in_list_view=1),
	f("description", "Data", "Description", in_list_view=1),
	f("amount", "Currency", "Amount", reqd=1, in_list_view=1),
	f("paid_from", "Link", "Paid From", options="Account"),
	f("entry", "Link", "Journal Entry", options="Journal Entry", read_only=1),
], istable=1)

doctype("Car Inspection Item", [
	f("item", "Data", "Check", reqd=1, in_list_view=1),
	f("result", "Select", "Result", options="OK\nNeeds Work\nBad\nNot Checked", default="Not Checked", in_list_view=1),
	f("notes", "Data", "Notes", in_list_view=1),
], istable=1)

doctype("Car Transfer Log", [
	f("transfer_date", "Date", "Date", in_list_view=1),
	f("from_showroom", "Link", "From", options="Showroom", in_list_view=1),
	f("to_showroom", "Link", "To", options="Showroom", in_list_view=1),
	f("note", "Data", "Note"),
], istable=1)

doctype("Car", [
	f("vin", "Data", "Chassis Number (VIN)", reqd=1, unique=1, in_list_view=1),
	f("plate_no", "Data", "Plate Number", in_list_view=1),
	f("condition", "Select", "Condition", options="New\nUsed", default="Used", reqd=1, in_standard_filter=1, in_list_view=1),
	f("status", "Select", "Status", options="Draft\nIn Preparation\nReady for Sale\nReserved\nSold\nDelivered\nWithdrawn", default="Draft", read_only=1, in_standard_filter=1, in_list_view=1, no_copy=1),
	f("showroom", "Link", "Showroom", options="Showroom", reqd=1, in_standard_filter=1, in_list_view=1),
	sec("sb_car", "The Car"),
	f("make", "Link", "Make", options="Car Make", reqd=1, in_standard_filter=1),
	f("model", "Link", "Model", options="Car Model", reqd=1),
	f("year", "Int", "Year", reqd=1),
	f("color", "Data", "Color"),
	col("cb1"),
	f("mileage", "Int", "Mileage (km)", default=0),
	f("fuel", "Select", "Fuel", options="\nPetrol\nDiesel\nHybrid\nElectric\nNatural Gas"),
	f("transmission", "Select", "Transmission", options="\nAutomatic\nManual"),
	f("engine_cc", "Int", "Engine (cc)"),
	f("image", "Attach Image", "Photo"),
	sec("sb_buy", "Purchase"),
	f("purchase_date", "Date", "Purchase Date"),
	f("purchase_price", "Currency", "Purchase Price"),
	f("purchase_paid_from", "Link", "Paid From", options="Account"),
	f("purchase_entry", "Link", "Purchase Entry", options="Journal Entry", read_only=1, no_copy=1),
	col("cb2"),
	f("seller_name", "Data", "Bought From", description="The dealer, importer, or the person who sold the used car."),
	f("seller_id", "Data", "Seller ID Number"),
	f("seller_phone", "Data", "Seller Phone"),
	sec("sb_cost", "Cost and Price"),
	f("costs", "Table", "Preparation Costs", options="Car Cost"),
	col("cb3"),
	f("total_cost", "Currency", "Total Cost", read_only=1, in_list_view=1),
	f("asking_price", "Currency", "Asking Price", in_list_view=1),
	f("minimum_price", "Currency", "Lowest Price a Salesman May Accept"),
	f("expected_margin", "Currency", "Expected Margin", read_only=1),
	sec("sb_insp", "Inspection"),
	f("inspection", "Table", "Inspection Checklist", options="Car Inspection Item"),
	sec("sb_docs", "Papers"),
	f("license_expiry", "Date", "License Expiry"),
	f("insurance_expiry", "Date", "Insurance Expiry"),
	col("cb4"),
	f("notes", "Small Text", "Notes"),
	sec("sb_moves", "Showroom Transfers"),
	f("transfers", "Table", "Transfers", options="Car Transfer Log", read_only=1),
	sec("sb_sale", "Sale"),
	f("sale", "Link", "Car Sale", options="Car Sale", read_only=1, no_copy=1),
	f("booking", "Link", "Car Booking", options="Car Booking", read_only=1, no_copy=1),
], autoname="format:CAR-{#####}", title_field="vin", show_title_field_in_link=1, search_fields="vin,plate_no,make,model", icon="fa fa-car",
	track_changes=1, perms=perms((MGR, "all"), (SAL, "r"), (TEC, "rw"), (ACC, "r")))

# ---------------------------------------------------------------- booking and sale
doctype("Car Booking", [
	f("car", "Link", "Car", options="Car", reqd=1, in_list_view=1, in_standard_filter=1),
	f("customer", "Link", "Customer", options="Customer", reqd=1, in_list_view=1),
	f("showroom", "Link", "Showroom", options="Showroom", fetch_from="car.showroom", read_only=1),
	f("status", "Select", "Status", options="Active\nConverted\nCancelled\nExpired", default="Active", read_only=1, in_list_view=1, in_standard_filter=1, no_copy=1),
	col("cb1"),
	f("agreed_price", "Currency", "Agreed Price"),
	f("deposit", "Currency", "Deposit"),
	f("mode_of_payment", "Link", "Deposit Paid By", options="Mode of Payment", depends_on="deposit"),
	f("valid_until", "Date", "Holds the Car Until", reqd=1, in_list_view=1),
	f("deposit_entry", "Link", "Deposit Payment Entry", options="Payment Entry", read_only=1, no_copy=1),
	f("notes", "Small Text", "Notes"),
], autoname="BKG-.YYYY.-.#####", title_field="customer", icon="fa fa-bookmark", track_changes=1, perms=perms((MGR, "all"), (SAL, "rwc"), (ACC, "r")))

doctype("Sale Extra", [
	f("description", "Data", "Description", reqd=1, in_list_view=1),
	f("amount", "Currency", "Amount", reqd=1, in_list_view=1),
], istable=1)

doctype("Car Sale", [
	f("customer", "Link", "Customer", options="Customer", reqd=1, in_list_view=1, in_standard_filter=1),
	f("car", "Link", "Car", options="Car", reqd=1, in_list_view=1, in_standard_filter=1),
	f("showroom", "Link", "Showroom", options="Showroom", fetch_from="car.showroom", read_only=1, in_standard_filter=1),
	f("sale_date", "Date", "Date", default="Today", reqd=1, in_list_view=1),
	col("cb1"),
	f("status", "Select", "Status", options="Draft\nConfirmed\nDelivered\nCancelled", default="Draft", read_only=1, in_list_view=1, in_standard_filter=1, no_copy=1),
	f("salesman", "Link", "Salesman", options="Employee", in_standard_filter=1),
	f("booking", "Link", "Booking", options="Car Booking", description="A booking's deposit is applied to the invoice."),
	sec("sb_price", "Price"),
	f("price", "Currency", "Agreed Price", reqd=1),
	f("discount", "Currency", "Discount"),
	f("price_reason", "Small Text", "Reason for a Price Below the Minimum", depends_on="eval:doc.below_minimum"),
	f("below_minimum", "Check", "Below the Minimum", read_only=1, hidden=1),
	col("cb2"),
	f("extras", "Table", "Extras (plates, papers, accessories)", options="Sale Extra"),
	sec("sb_fin", "Payment"),
	f("financing_plan", "Link", "Financing Plan", options="Financing Plan", description="Optional: picks the type, bank, installments and down payment for you."),
	f("financing_type", "Select", "How the Customer Pays", options="Cash\nShowroom Installments\nBank Financing\nLending Loan", default="Cash", reqd=1),
	f("down_payment", "Currency", "Down Payment", depends_on="eval:doc.financing_type!='Cash'"),
	f("months", "Int", "Number of Installments", depends_on="eval:doc.financing_type=='Showroom Installments'"),
	f("markup_pct", "Percent", "Markup on the Financed Amount (%)", depends_on="eval:doc.financing_type=='Showroom Installments'"),
	f("first_due_date", "Date", "First Installment Date", depends_on="eval:doc.financing_type=='Showroom Installments'"),
	col("cb3"),
	f("financier", "Link", "Bank or Finance Company", options="Financing Company", depends_on="eval:doc.financing_type=='Bank Financing'"),
	f("financier_due_date", "Date", "Financier Expected to Pay On", depends_on="eval:['Bank Financing','Lending Loan'].includes(doc.financing_type)"),
	f("loan_application", "Data", "Loan Application", read_only=1, depends_on="eval:doc.financing_type=='Lending Loan'"),
	f("loan", "Data", "Loan", depends_on="eval:doc.financing_type=='Lending Loan'", description="The loan once approved in the Lending module."),
	sec("sb_sched", "Installment Schedule"),
	f("schedule_html", "HTML", "Schedule"),
	sec("sb_tot", "Totals"),
	f("extras_total", "Currency", "Extras", read_only=1),
	f("vat", "Currency", "VAT", read_only=1),
	f("cash_total", "Currency", "Total in Cash", read_only=1),
	f("financed_amount", "Currency", "Financed Amount", read_only=1),
	col("cb4"),
	f("surcharge", "Currency", "Installment Markup", read_only=1),
	f("grand_total", "Currency", "Invoice Total", read_only=1, in_list_view=1),
	f("monthly_installment", "Currency", "Installment", read_only=1),
	sec("sb_acc", "Accounting and Commission"),
	f("sales_invoice", "Link", "Sales Invoice", options="Sales Invoice", read_only=1, no_copy=1),
	f("cogs_entry", "Link", "Cost of Sale Entry", options="Journal Entry", read_only=1, no_copy=1),
	f("credit_note", "Link", "Credit Note", options="Sales Invoice", read_only=1, no_copy=1),
	f("cogs_reversal_entry", "Link", "Cost of Sale Reversal Entry", options="Journal Entry", read_only=1, no_copy=1),
	f("car_cost", "Currency", "Car Cost", read_only=1),
	col("cb5"),
	f("margin", "Currency", "Margin", read_only=1),
	f("commission_amount", "Currency", "Salesman Commission", read_only=1),
], autoname="CSL-.YYYY.-.#####", title_field="customer", icon="fa fa-handshake-o", track_changes=1, perms=perms((MGR, "all"), (SAL, "rwc"), (ACC, "rw")))

doctype("Test Drive", [
	f("car", "Link", "Car", options="Car", reqd=1, in_list_view=1),
	f("customer", "Link", "Customer", options="Customer"),
	f("lead_name", "Data", "Name (when not yet a customer)", in_list_view=1),
	f("phone", "Data", "Phone"),
	col("cb1"),
	f("drive_date", "Datetime", "When", default="Now", reqd=1, in_list_view=1),
	f("salesman", "Link", "Salesman", options="Employee"),
	f("outcome", "Select", "Outcome", options="Scheduled\nInterested\nNot Interested\nBooked", default="Scheduled", in_list_view=1, in_standard_filter=1),
	f("notes", "Small Text", "Notes"),
], autoname="format:TD-{#####}", title_field="lead_name", icon="fa fa-road", perms=perms((MGR, "all"), (SAL, "rwc")))

def build():
	os.makedirs(ROOT, exist_ok=True)
	for name, d in DT.items():
		fields = d["fields"]
		order = [x["fieldname"] for x in fields]
		istable = d.get("istable", 0)
		out = {
			"actions": [], "creation": TS, "doctype": "DocType", "engine": "InnoDB", "field_order": order, "fields": fields,
			"links": [], "modified": TS, "modified_by": "Administrator", "module": MODULE, "name": name, "owner": "Administrator",
			"sort_field": "creation", "sort_order": "DESC", "states": [],
			"permissions": [] if istable else d.get("perms", []),
		}
		for k in ("autoname", "title_field", "icon", "track_changes", "issingle", "istable", "show_title_field_in_link", "search_fields"):
			if k in d:
				out[k] = d[k]
		if not istable and "track_changes" not in d and name not in ("Room Night Lock", "Production Scan", "Class Attendance"):
			out["track_changes"] = 1  # who changed what, when
		if "autoname" not in d and not istable and not d.get("issingle"):
			out["autoname"] = "hash"
		out["allow_rename"] = 0
		slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
		folder = os.path.join(ROOT, slug)
		os.makedirs(folder, exist_ok=True)
		open(os.path.join(folder, "__init__.py"), "a").close()
		with open(os.path.join(folder, slug + ".json"), "w", encoding="utf-8") as fh:
			json.dump(out, fh, indent=1, ensure_ascii=False)
			fh.write("\n")
		py = os.path.join(folder, slug + ".py")
		if not os.path.exists(py):
			cls = "".join(w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", name))
			with open(py, "w") as fh:
				fh.write(f"from frappe.model.document import Document\n\n\nclass {cls}(Document):\n\tpass\n")


if __name__ == "__main__":
	build()
	print(len(DT), "doctypes")
