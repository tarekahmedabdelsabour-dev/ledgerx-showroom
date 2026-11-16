frappe.query_reports["Installments Due"] = {
	filters: [
		{ fieldname: "until", label: __("Due Until"), fieldtype: "Date", default: frappe.datetime.add_days(frappe.datetime.get_today(), 30) },
		{ fieldname: "showroom", label: __("Showroom"), fieldtype: "Link", options: "Showroom" },
	],
};
