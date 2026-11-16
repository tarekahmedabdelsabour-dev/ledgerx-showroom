frappe.query_reports["Car Sales Margin"] = {
	filters: [
		{ fieldname: "from_date", label: __("From"), fieldtype: "Date", default: frappe.datetime.add_days(frappe.datetime.get_today(), -29) },
		{ fieldname: "to_date", label: __("To"), fieldtype: "Date", default: frappe.datetime.get_today() },
		{ fieldname: "showroom", label: __("Showroom"), fieldtype: "Link", options: "Showroom" },
		{ fieldname: "salesman", label: __("Salesman"), fieldtype: "Link", options: "Employee" },
		{ fieldname: "financing_type", label: __("How the Customer Pays"), fieldtype: "Select", options: "\nCash\nShowroom Installments\nBank Financing\nLending Loan" },
	],
};
