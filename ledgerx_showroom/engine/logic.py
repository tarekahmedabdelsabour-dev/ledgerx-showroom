"""Pure rules of the showroom module: installments, margins, commission, days in stock.
No database and no frappe import, so everything here is unit-tested alone (tests/test_logic.py)."""
import calendar
from datetime import date, datetime


def to_date(v):
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def r2(x):
	return round(float(x or 0) + 1e-9, 2)


def add_months(d, n):
	"""Same day n months later; a 31st falls on the last day of a shorter month."""
	d = to_date(d)
	m = d.month - 1 + int(n)
	y, m = d.year + m // 12, m % 12 + 1
	return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def sale_totals(price, discount, extras, vat_rate, financing_type, down_payment, months, markup_pct):
	"""Everything the contract shows. The surcharge (markup on the financed part) is for the showroom's own
	installments only and carries no VAT. Returns a dict of rounded amounts."""
	net_car = r2(float(price or 0) - float(discount or 0))
	extras = r2(extras)
	vat = r2((net_car + extras) * float(vat_rate or 0) / 100.0)
	cash_total = r2(net_car + extras + vat)
	down = r2(min(max(float(down_payment or 0), 0), cash_total))
	financed = r2(cash_total - down) if financing_type != "Cash" else 0.0
	surcharge = r2(financed * float(markup_pct or 0) / 100.0) if financing_type == "Showroom Installments" else 0.0
	grand = r2(cash_total + surcharge)
	monthly = r2((financed + surcharge) / int(months)) if financing_type == "Showroom Installments" and int(months or 0) > 0 else 0.0
	return {"net_car": net_car, "extras": extras, "vat": vat, "cash_total": cash_total, "down": down, "financed": financed,
		"surcharge": surcharge, "grand_total": grand, "monthly": monthly}


def payment_schedule(grand_total, financing_type, down_payment, financed, surcharge, months, first_due, today, bank_due=None):
	"""Rows [(due_date, amount)] that add up to the grand total to the cent.
	Cash: one row today. Showroom installments: down payment today then equal monthly rows (the last absorbs rounding).
	Bank or loan financing: down payment today, the financed amount when the financier is expected to pay."""
	today = to_date(today)
	grand = r2(grand_total)
	if financing_type == "Cash" or r2(financed) <= 0:
		return [(today, grand)]
	rows = []
	down = r2(down_payment)
	if down > 0:
		rows.append((today, down))
	if financing_type == "Showroom Installments":
		n = int(months)
		total = r2(float(financed) + float(surcharge))
		each = r2(total / n)
		first = to_date(first_due) if first_due else add_months(today, 1)
		paid = 0.0
		for i in range(n):
			amt = each if i < n - 1 else r2(total - paid)
			paid = r2(paid + amt)
			rows.append((add_months(first, i), amt))
	else:
		rows.append((to_date(bank_due) if bank_due else add_months(today, 1), r2(financed)))
	diff = r2(grand - sum(a for _d, a in rows))
	if diff:
		rows[-1] = (rows[-1][0], r2(rows[-1][1] + diff))
	return rows


def margin(sale_price_net, cost):
	return r2(float(sale_price_net or 0) - float(cost or 0))


def commission(margin_amount, pct):
	"""Percent of the margin; no commission on a loss."""
	return r2(max(float(margin_amount or 0), 0) * float(pct or 0) / 100.0)


def days_in_stock(acquired, until=None, today=None):
	if not acquired:
		return 0
	end = to_date(until or today or date.today())
	return max((end - to_date(acquired)).days, 0)


def price_allowed(price, minimum):
	"""A price below the car's minimum needs a manager's reason."""
	return not float(minimum or 0) or float(price or 0) >= float(minimum)
