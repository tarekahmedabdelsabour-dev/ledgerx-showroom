frappe.query_reports["Showroom Stock"] = {
	filters: [
		{ fieldname: "showroom", label: __("Showroom"), fieldtype: "Link", options: "Showroom" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nDraft\nIn Preparation\nReady for Sale\nReserved\nSold\nDelivered\nWithdrawn" },
		{ fieldname: "condition", label: __("Condition"), fieldtype: "Select", options: "\nNew\nUsed" },
		{ fieldname: "make", label: __("Make"), fieldtype: "Link", options: "Car Make" },
	],
};
