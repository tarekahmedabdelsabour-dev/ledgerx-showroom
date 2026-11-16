frappe.ui.form.on("Car Booking", {
	setup(frm) {
		frm.set_query("car", () => ({ filters: { status: "Ready for Sale" } }));
	},
	onload(frm) {
		if (frm.is_new() && !frm.doc.valid_until) {
			frappe.db.get_single_value("Showroom Settings", "default_booking_days").then((n) =>
				frm.set_value("valid_until", frappe.datetime.add_days(frappe.datetime.get_today(), n || 3)));
		}
	},
	car(frm) {
		if (frm.doc.car) frappe.db.get_value("Car", frm.doc.car, "asking_price").then((r) => !frm.doc.agreed_price && frm.set_value("agreed_price", r.message.asking_price));
	},
	refresh(frm) {
		if (frm.is_new() || frm.doc.status !== "Active") return;
		const cancel = (refund) => frm.call({ doc: frm.doc, method: "cancel_booking", args: { refund }, freeze: true }).then(() => frm.reload_doc());
		frm.add_custom_button(__("Sell the Car"), () => frappe.new_doc("Car Sale", { car: frm.doc.car, customer: frm.doc.customer, booking: frm.doc.name, price: frm.doc.agreed_price })).addClass("btn-primary");
		frm.add_custom_button(__("Cancel and Refund the Deposit"), () => frappe.confirm(__("Free the car and pay the deposit back?"), () => cancel(1)), __("Cancel"));
		frm.add_custom_button(__("Cancel and Keep the Deposit as Credit"), () => frappe.confirm(__("Free the car; the deposit stays with the customer as an advance?"), () => cancel(0)), __("Cancel"));
	},
});
