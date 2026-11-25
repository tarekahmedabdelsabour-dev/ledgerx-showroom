"""Writes the workspace, sidebar and dock JSON of ledgerx_showroom. Run from the repo root."""
import json
import os
import uuid

BASE = os.path.join(os.path.dirname(__file__), "..", "ledgerx_showroom")
TS = "2026-11-17 07:00:00.000000"  # raise this whenever the workspace changes: migrate only re-reads a file that is newer than the saved one
CARDS = [  # (label, doctype, filters, function, fn_field)
	("Cars Ready for Sale", "Car", [["Car", "status", "=", "Ready for Sale"]], "Count", None),
	("Cars in Preparation", "Car", [["Car", "status", "=", "In Preparation"]], "Count", None),
	("Reserved Cars", "Car", [["Car", "status", "=", "Reserved"]], "Count", None),
	("Active Bookings", "Car Booking", [["Car Booking", "status", "=", "Active"]], "Count", None),
	("Draft Sales", "Car Sale", [["Car Sale", "status", "=", "Draft"]], "Count", None),
	("Sales Awaiting Delivery", "Car Sale", [["Car Sale", "status", "=", "Confirmed"]], "Count", None),
	("Sales This Month", "Car Sale", [["Car Sale", "sale_date", "Timespan", "this month"], ["Car Sale", "status", "in", ["Confirmed", "Delivered"]]], "Count", None),
	("Test Drives Today", "Test Drive", [["Test Drive", "creation", "Timespan", "today"]], "Count", None),
]
CHARTS = [  # (name, doctype, type, kind, extra)
	("Car Sales per Month", "Car Sale", "Bar", "series", {"based_on": "sale_date", "filters": [["Car Sale", "status", "in", ["Confirmed", "Delivered"]]]}),
	("Cars by Status", "Car", "Donut", "group", {"by": "status"}),
	("Sales by Payment Method", "Car Sale", "Donut", "group", {"by": "financing_type"}),
	("Cars by Showroom", "Car", "Bar", "group", {"by": "showroom"}),
]
GROUPS = [  # (title, icon, collapsed, [(label, kind, target, icon)])
	("Daily Work", None, 0, [
		("Car", "DocType", "Car", "car"), ("Car Booking", "DocType", "Car Booking", "calendar-check"),
		("Car Sale", "DocType", "Car Sale", "file-text"), ("Test Drive", "DocType", "Test Drive", "gauge"), ("Installments Due", "Report", "Showroom Installments Due", "alarm-clock")]),
	("Reports", "bar-chart-3", 0, [
		("Showroom Stock", "Report", "Showroom Stock", "layout-list"), ("Car Sales Margin", "Report", "Car Sales Margin", "trending-up")]),
	("Setup", "settings", 1, [
		("Showroom", "DocType", "Showroom", "store"), ("Car Make", "DocType", "Car Make", "tag"), ("Car Model", "DocType", "Car Model", "car-front"),
		("Financing Plan", "DocType", "Financing Plan", "percent"), ("Financing Company", "DocType", "Financing Company", "landmark"), ("Sale Extra", "DocType", "Sale Extra", "package-plus"),
		("Showroom Settings", "DocType", "Showroom Settings", "settings")]),
	("Related", "link-2", 1, [  # the rest of the app these documents are tied to
		("Customer", "DocType", "Customer", "users"), ("Sales Invoice", "DocType", "Sales Invoice", "receipt"),
		("Payment Entry", "DocType", "Payment Entry", "wallet"), ("Journal Entry", "DocType", "Journal Entry", "book-open"),
		("Employee", "DocType", "Employee", "user-round"), ("Additional Salary", "DocType", "Additional Salary", "banknote")]),
]
TOP = ["Car Sale", "Installments Due", "Financing Plan", "Car Booking"]


def write(path, data):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=1, ensure_ascii=False)
		fh.write("\n")


def slug(n):
	return n.lower().replace(" ", "_").replace("-", "_")


def write_cards():
	for label, dt, flt, fn, _f in CARDS:
		write(os.path.join(BASE, "showroom", "number_card", slug(label), slug(label) + ".json"), {
			"creation": TS, "docstatus": 0, "doctype": "Number Card", "document_type": dt, "filters_json": json.dumps(flt), "function": fn,
			"idx": 0, "is_public": 1, "is_standard": 1, "label": label, "modified": TS, "modified_by": "Administrator", "module": "Showroom",
			"name": label, "owner": "Administrator", "show_percentage_stats": 0, "stats_time_interval": "Daily", "type": "Document Type"})
	for name, dt, typ, kind, x in CHARTS:
		d = {"chart_name": name, "creation": TS, "docstatus": 0, "doctype": "Dashboard Chart", "document_type": dt, "dynamic_filters_json": "",
			"idx": 0, "is_public": 1, "is_standard": 1, "modified": TS, "modified_by": "Administrator", "module": "Showroom", "name": name,
			"number_of_groups": 0, "owner": "Administrator", "type": typ, "use_report_chart": 0, "y_axis": []}
		if kind == "group":
			d.update({"chart_type": "Group By", "group_by_based_on": x["by"], "group_by_type": "Count", "filters_json": "[]", "timeseries": 0})
		else:
			d.update({"chart_type": "Count", "based_on": x["based_on"], "filters_json": json.dumps(x["filters"]), "time_interval": "Monthly",
				"timeseries": 1, "timespan": "Last Year"})
		write(os.path.join(BASE, "showroom", "dashboard_chart", slug(name), slug(name) + ".json"), d)


def main():
	write_cards()
	rid = lambda: uuid.uuid4().hex[:10]
	content = [{"id": rid(), "type": "header", "data": {"text": '<span class="h4"><b>Showroom</b></span>', "col": 12}}]
	for label, *_r in CARDS:
		content.append({"id": rid(), "type": "number_card", "data": {"number_card_name": label, "col": 3}})
	for name, *_r in CHARTS:
		content.append({"id": rid(), "type": "chart", "data": {"chart_name": name, "col": 6}})
	shortcuts, links = [], []
	for label in TOP:
		content.insert(1 + len(shortcuts), {"id": rid(), "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
		kind = "Report" if label in ("Installments Due",) else "DocType"
		sc = {"label": label, "link_to": "Showroom Installments Due" if label == "Installments Due" else label, "type": kind}
		if kind == "DocType":
			sc["doc_view"] = "List"
		else:
			sc["is_query_report"] = 1
		shortcuts.append(sc)
	for title, _i, _c, items in GROUPS[1:]:
		content.append({"id": rid(), "type": "card", "data": {"card_name": title, "col": 4}})
		links.append({"type": "Card Break", "label": title, "hidden": 0, "is_query_report": 0, "link_count": len(items), "onboard": 0})
		for label, kind, target, _icon in items:
			links.append({"type": "Link", "label": label, "link_type": kind, "link_to": target, "hidden": 0, "is_query_report": 1 if kind == "Report" else 0,
				"onboard": 0, "dependencies": "", "only_for": ""})
	write(os.path.join(BASE, "showroom", "workspace", "showroom", "showroom.json"), {
		"charts": [{"chart_name": c[0], "label": c[0]} for c in CHARTS], "content": json.dumps(content), "creation": TS, "custom_blocks": [], "docstatus": 0, "doctype": "Workspace",
		"for_user": "", "hide_custom": 1, "icon": "car", "idx": 1, "is_hidden": 0, "label": "Showroom", "links": links, "title": "Showroom", "modified": TS,
		"modified_by": "Administrator", "module": "Showroom", "name": "Showroom", "number_cards": [{"label": c[0], "number_card_name": c[0]} for c in CARDS], "owner": "Administrator",
		"parent_page": "", "public": 1, "quick_lists": [], "roles": [], "sequence_id": 22.0, "shortcuts": shortcuts})
	row = lambda i, label, kind, target, icon, child: {"child": child, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": i, "indent": 0,
		"keep_closed": 0, "label": label, "link_to": target, "link_type": kind, "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Link"}
	items = [row(1, "Home", "Workspace", "Showroom", "house", 0)]
	for title, icon, closed, entries in GROUPS:
		if icon:
			items.append({"child": 0, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": len(items) + 1, "indent": 1, "keep_closed": closed,
				"label": title, "link_type": "DocType", "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Section Break"})
		for label, kind, target, ic in entries:
			items.append(row(len(items) + 1, label, kind, target, ic, 1 if icon else 0))
	write(os.path.join(BASE, "sidebar", "showroom", "showroom.json"), {"app": "ledgerx_showroom", "doctype": "Sidebar", "header_icon": "car",
		"items": items, "module": "Showroom", "name": "Showroom", "standard": 1, "title": "Showroom"})
	write(os.path.join(BASE, "dock", "showroom", "showroom.json"), {"app": "ledgerx_showroom", "creation": TS, "docstatus": 0, "doctype": "Dock", "idx": 0,
		"items": [{"added": 0, "hidden": 0, "icon": "car", "link_to": "Showroom", "link_type": "Sidebar", "title": "Showroom"}],
		"modified": TS, "modified_by": "Administrator", "name": "showroom", "owner": "Administrator", "standard": 1})


main()
