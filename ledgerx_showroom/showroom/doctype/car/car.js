frappe.ui.form.on("Car", {
	setup(frm) {
		frm.set_query("model", () => ({ filters: frm.doc.make ? { make: frm.doc.make } : {} }));
	},
	refresh(frm) {
		if (frm.is_new()) return;
		const act = (method, args, done) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); if (done) done(r.message || {}); });
		const s = frm.doc.status;
		const ask = (title, fields, method, extra) => {
			const d = new frappe.ui.Dialog({ title, fields, primary_action_label: __("Save"), primary_action(v) { d.hide(); act(method, Object.assign({}, extra || {}, v)); } });
			d.show();
		};
		if (s === "Draft") {
			frm.add_custom_button(__("Record Purchase"), () => ask(__("Record Purchase"), [
				{ fieldname: "paid_from", fieldtype: "Link", options: "Account", label: __("Paid From"), default: frm.doc.purchase_paid_from,
					description: __("Cash, bank, or the payable account of the seller") }], "acquire")).addClass("btn-primary");
		}
		if (["In Preparation", "Ready for Sale", "Reserved"].includes(s)) {
			frm.add_custom_button(__("Add Cost"), () => ask(__("Add Cost"), [
				{ fieldname: "cost_type", fieldtype: "Select", label: __("Type"), reqd: 1, options: "Inspection\nRepair\nPaint\nParts\nPapers and Licensing\nTransport\nCleaning\nOther", default: "Repair" },
				{ fieldname: "amount", fieldtype: "Currency", label: __("Amount"), reqd: 1 },
				{ fieldname: "description", fieldtype: "Data", label: __("Description") },
				{ fieldname: "paid_from", fieldtype: "Link", options: "Account", label: __("Paid From") }], "add_cost"));
		}
		if (s === "In Preparation") {
			frm.add_custom_button(__("Mark Ready for Sale"), () => act("mark_ready")).addClass("btn-primary");
		}
		if (["In Preparation", "Ready for Sale"].includes(s)) {
			frm.add_custom_button(__("Transfer to Another Showroom"), () => ask(__("Transfer"), [
				{ fieldname: "to_showroom", fieldtype: "Link", options: "Showroom", label: __("To"), reqd: 1, get_query: () => ({ filters: { name: ["!=", frm.doc.showroom] } }) },
				{ fieldname: "note", fieldtype: "Data", label: __("Note") }], "transfer"));
		}
		if (s === "Ready for Sale") {
			frm.add_custom_button(__("Book the Car"), () => frappe.new_doc("Car Booking", { car: frm.doc.name }), __("Sell"));
			frm.add_custom_button(__("Sell the Car"), () => frappe.new_doc("Car Sale", { car: frm.doc.name, price: frm.doc.asking_price }), __("Sell"));
			frm.add_custom_button(__("Test Drive"), () => frappe.new_doc("Test Drive", { car: frm.doc.name }), __("Sell"));
		}
		if (s === "Reserved" && frm.doc.booking) {
			frm.add_custom_button(__("Sell the Car"), () => frappe.new_doc("Car Sale", { car: frm.doc.name, booking: frm.doc.booking, price: frm.doc.asking_price }));
		}
		if (frm.doc.sale) frm.add_custom_button(__("Open Sale"), () => frappe.set_route("Form", "Car Sale", frm.doc.sale));
		if (!["Reserved", "Sold", "Delivered", "Withdrawn"].includes(s)) {
			frm.add_custom_button(__("Withdraw from Sale"), () => frappe.confirm(__("Take this car off sale?"), () => act("withdraw")), __("More"));
		}
		const ind = { Draft: "gray", "In Preparation": "orange", "Ready for Sale": "green", Reserved: "blue", Sold: "purple", Delivered: "darkgrey", Withdrawn: "red" };
		frm.page.set_indicator(__(s), ind[s] || "gray");
	},
});
