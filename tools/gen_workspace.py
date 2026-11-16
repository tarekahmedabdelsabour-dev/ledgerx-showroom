"""Writes the workspace, sidebar and dock JSON of ledgerx_showroom. Run from the repo root."""
import json
import os
import uuid

BASE = os.path.join(os.path.dirname(__file__), "..", "ledgerx_showroom")
TS = "2026-11-16 22:00:00.000000"  # raise this whenever the workspace changes: migrate only re-reads a file that is newer than the saved one
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
ITEMS = [  # (label, kind, target, icon)
	("Car", "DocType", "Car", "car"),
	("Car Booking", "DocType", "Car Booking", "calendar-check"),
	("Car Sale", "DocType", "Car Sale", "file-text"),
	("Test Drive", "DocType", "Test Drive", "gauge"),
	("Showroom", "DocType", "Showroom", "store"),
	("Car Make", "DocType", "Car Make", "tag"),
	("Car Model", "DocType", "Car Model", "car-front"),
	("Financing Company", "DocType", "Financing Company", "landmark"),
	("Sale Extra", "DocType", "Sale Extra", "package-plus"),
	("Showroom Settings", "DocType", "Showroom Settings", "settings"),
	("Showroom Stock", "Report", "Showroom Stock", "layout-list"),
	("Car Sales Margin", "Report", "Car Sales Margin", "trending-up"),
	("Installments Due", "Report", "Installments Due", "alarm-clock"),
]


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
	content = [{"id": uuid.uuid4().hex[:10], "type": "header", "data": {"text": '<span class="h4"><b>Showroom</b></span>', "col": 12}}]
	for label, *_r in CARDS:
		content.append({"id": uuid.uuid4().hex[:10], "type": "number_card", "data": {"number_card_name": label, "col": 3}})
	for name, *_r in CHARTS:
		content.append({"id": uuid.uuid4().hex[:10], "type": "chart", "data": {"chart_name": name, "col": 6}})
	shortcuts = []
	for label, kind, target, _icon in ITEMS:
		content.append({"id": uuid.uuid4().hex[:10], "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
		s = {"label": label, "link_to": target, "type": kind}
		if kind == "DocType":
			s["doc_view"] = "List"
		shortcuts.append(s)
	write(os.path.join(BASE, "showroom", "workspace", "showroom", "showroom.json"), {
		"charts": [{"chart_name": c[0], "label": c[0]} for c in CHARTS], "content": json.dumps(content), "creation": TS, "custom_blocks": [], "docstatus": 0, "doctype": "Workspace",
		"for_user": "", "hide_custom": 1, "icon": "car", "idx": 1, "is_hidden": 0, "label": "Showroom", "links": [], "title": "Showroom", "modified": TS,
		"modified_by": "Administrator", "module": "Showroom", "name": "Showroom", "number_cards": [{"label": c[0], "number_card_name": c[0]} for c in CARDS], "owner": "Administrator",
		"parent_page": "", "public": 1, "quick_lists": [], "roles": [], "sequence_id": 22.0, "shortcuts": shortcuts})
	items = [{"child": 0, "collapsible": 1, "doctype": "Sidebar Item", "icon": "house", "idx": 1, "indent": 0, "keep_closed": 0, "label": "Home",
		"link_to": "Showroom", "link_type": "Workspace", "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Link"}]
	for i, (label, kind, target, icon) in enumerate(ITEMS, start=2):
		items.append({"child": 0, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": i, "indent": 0, "keep_closed": 0,
			"label": label, "link_to": target, "link_type": kind, "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Link"})
	write(os.path.join(BASE, "sidebar", "showroom", "showroom.json"), {"app": "ledgerx_showroom", "doctype": "Sidebar", "header_icon": "car",
		"items": items, "module": "Showroom", "name": "Showroom", "standard": 1, "title": "Showroom"})
	write(os.path.join(BASE, "dock", "showroom", "showroom.json"), {"app": "ledgerx_showroom", "creation": TS, "docstatus": 0, "doctype": "Dock", "idx": 0,
		"items": [{"added": 0, "hidden": 0, "icon": "car", "link_to": "Showroom", "link_type": "Sidebar", "title": "Showroom"}],
		"modified": TS, "modified_by": "Administrator", "name": "showroom", "owner": "Administrator", "standard": 1})


main()
