frappe.ui.form.on("Car Sale", {
	setup(frm) {
		frm.set_query("car", () => ({ filters: { status: ["in", ["Ready for Sale", "Reserved"]] } }));
	},
	car(frm) {
		if (!frm.doc.car) return;
		frappe.db.get_value("Car", frm.doc.car, ["asking_price", "booking"]).then((r) => {
			if (!frm.doc.price) frm.set_value("price", r.message.asking_price);
			if (r.message.booking && !frm.doc.booking) frm.set_value("booking", r.message.booking);
		});
	},
	financing_plan(frm) {
		if (!frm.doc.financing_plan) return;
		frappe.db.get_doc("Financing Plan", frm.doc.financing_plan).then((p) => {
			const net = (frm.doc.price || 0) - (frm.doc.discount || 0);
			frm.set_value({ financing_type: p.financing_type, months: p.months,
				financier: p.financing_type === "Bank Financing" ? p.financier : "",
				markup_pct: p.financing_type === "Showroom Installments" ? p.markup_pct : 0 });
			if (!frm.doc.down_payment && p.min_down_pct) frm.set_value("down_payment", flt(net * p.min_down_pct / 100, 2));
		});
	},
	show_schedule(frm) {
		const w = frm.fields_dict.schedule_html && frm.fields_dict.schedule_html.$wrapper;
		if (!w) return;
		if (!frm.doc.sales_invoice) { w.html(`<p class="text-muted">${__("The schedule appears once the sale is confirmed.")}</p>`); return; }
		frappe.db.get_doc("Sales Invoice", frm.doc.sales_invoice).then((inv) => {
			const today = frappe.datetime.get_today();
			const rows = (inv.payment_schedule || []).map((r) => {
				const due = flt(r.payment_amount) - flt(r.paid_amount);
				const late = due > 0.005 && r.due_date < today;
				return `<tr><td>${frappe.datetime.str_to_user(r.due_date)}</td><td>${format_currency(r.payment_amount)}</td><td>${format_currency(r.paid_amount)}</td>
					<td>${due > 0.005 ? format_currency(due) : "✓"}</td><td>${late ? `<span class="indicator-pill red">${__("Late")}</span>` : ""}</td></tr>`;
			}).join("");
			w.html(`<table class="table table-bordered"><thead><tr><th>${__("Due Date")}</th><th>${__("Amount")}</th><th>${__("Paid")}</th><th>${__("Still Due")}</th><th></th></tr></thead><tbody>${rows}</tbody></table>`);
		});
	},
	financing_type(frm) {
		if (frm.doc.financing_type === "Showroom Installments") {
			frappe.db.get_value("Showroom Settings", null, ["default_months", "default_markup_pct"]).then((r) => {
				if (!frm.doc.months) frm.set_value("months", r.message.default_months);
				if (!frm.doc.markup_pct) frm.set_value("markup_pct", r.message.default_markup_pct);
			});
		}
	},
	refresh(frm) {
		frm.events.show_schedule(frm);
		if (frm.is_new()) return;
		const s = frm.doc.status;
		const act = (method, args, done) => frm.call({ doc: frm.doc, method, args: args || {}, freeze: true }).then((r) => { frm.reload_doc(); if (done) done(r.message); });
		const ask = (title, fields, method, label) => {
			const d = new frappe.ui.Dialog({ title, fields, primary_action_label: label || __("Save"), primary_action(v) { d.hide(); act(method, v); } });
			d.show();
		};
		const mop = { fieldname: "mode_of_payment", fieldtype: "Link", options: "Mode of Payment", label: __("Mode of Payment"), reqd: 1 };
		if (s === "Draft") {
			frm.add_custom_button(__("Confirm the Sale"), () => frappe.confirm(__("Create the invoice and mark the car as sold?"), () => act("confirm"))).addClass("btn-primary");
			frm.add_custom_button(__("Cancel Draft"), () => act("cancel_draft"), __("More"));
		}
		if (["Confirmed", "Delivered"].includes(s)) {
			frm.add_custom_button(__("Receive Payment"), () => ask(__("Receive Payment"), [mop,
				{ fieldname: "amount", fieldtype: "Currency", label: __("Amount"), reqd: 1 },
				{ fieldname: "reference", fieldtype: "Data", label: __("Reference") }], "receive_payment"), __("Money"));
			if (frm.doc.financing_type === "Bank Financing") {
				frm.add_custom_button(__("Receive from the Bank"), () => ask(__("Receive from the Bank"), [mop,
					{ fieldname: "amount", fieldtype: "Currency", label: __("Financed Amount"), reqd: 1, default: frm.doc.financed_amount },
					{ fieldname: "fee", fieldtype: "Currency", label: __("Fee the Bank Kept"), default: 0 },
					{ fieldname: "reference", fieldtype: "Data", label: __("Reference") }], "receive_from_bank"), __("Money"));
			}
			if (frm.doc.financing_type === "Lending Loan") {
				frm.add_custom_button(__("Loan Paid Out: Settle the Invoice"), () => ask(__("Settle from the Loan"), [
					{ fieldname: "amount", fieldtype: "Currency", label: __("Amount"), default: frm.doc.financed_amount }], "settle_from_loan"), __("Money"));
			}
			frm.add_custom_button(__("Open Invoice"), () => frappe.set_route("Form", "Sales Invoice", frm.doc.sales_invoice));
		}
		if (s === "Confirmed") frm.add_custom_button(__("Deliver the Car"), () => act("deliver")).addClass("btn-primary");
		if (frm.doc.loan_application) frm.add_custom_button(__("Open Loan Application"), () => frappe.set_route("Form", "Loan Application", frm.doc.loan_application));
		const ind = { Draft: "gray", Confirmed: "blue", Delivered: "green", Cancelled: "red" };
		frm.page.set_indicator(__(s), ind[s] || "gray");
	},
});
