"""Pure-logic tests: python3 ledgerx_showroom/tests/test_logic.py (no site needed)."""
import importlib.util
import os
import unittest

_p = os.path.join(os.path.dirname(__file__), "..", "engine", "logic.py")
_s = importlib.util.spec_from_file_location("showroom_logic", _p)
L = importlib.util.module_from_spec(_s)
_s.loader.exec_module(L)


class T(unittest.TestCase):
	def test_add_months_clamps(self):
		self.assertEqual(str(L.add_months("2026-01-31", 1)), "2026-02-28")
		self.assertEqual(str(L.add_months("2026-11-15", 3)), "2027-02-15")
		self.assertEqual(str(L.add_months("2026-12-31", 2)), "2027-02-28")

	def test_cash_sale(self):
		t = L.sale_totals(500000, 10000, 5000, 14, "Cash", 0, 0, 0)
		self.assertEqual((t["net_car"], t["vat"], t["cash_total"], t["financed"], t["grand_total"]), (490000.0, 69300.0, 564300.0, 0.0, 564300.0))
		self.assertEqual(L.payment_schedule(t["grand_total"], "Cash", 0, 0, 0, 0, None, "2026-11-16"), [(L.to_date("2026-11-16"), 564300.0)])

	def test_showroom_installments(self):
		t = L.sale_totals(600000, 0, 0, 0, "Showroom Installments", 150000, 12, 18)
		self.assertEqual((t["financed"], t["surcharge"], t["grand_total"], t["monthly"]), (450000.0, 81000.0, 681000.0, 44250.0))
		rows = L.payment_schedule(t["grand_total"], "Showroom Installments", t["down"], t["financed"], t["surcharge"], 12, None, "2026-11-16")
		self.assertEqual(len(rows), 13)
		self.assertEqual(rows[0], (L.to_date("2026-11-16"), 150000.0))
		self.assertEqual(str(rows[1][0]), "2026-12-16")
		self.assertEqual(round(sum(a for _d, a in rows), 2), 681000.0)

	def test_rounding_goes_to_last_installment(self):
		t = L.sale_totals(100000, 0, 0, 0, "Showroom Installments", 0, 7, 10)
		rows = L.payment_schedule(t["grand_total"], "Showroom Installments", 0, t["financed"], t["surcharge"], 7, None, "2026-11-16")
		self.assertEqual(round(sum(a for _d, a in rows), 2), t["grand_total"])
		self.assertEqual(len(rows), 7)

	def test_bank_financing(self):
		t = L.sale_totals(800000, 0, 0, 14, "Bank Financing", 200000, 0, 99)
		self.assertEqual((t["surcharge"], t["financed"], t["grand_total"]), (0.0, 712000.0, 912000.0))
		rows = L.payment_schedule(t["grand_total"], "Bank Financing", t["down"], t["financed"], 0, 0, None, "2026-11-16", "2026-12-01")
		self.assertEqual([(str(d), a) for d, a in rows], [("2026-11-16", 200000.0), ("2026-12-01", 712000.0)])

	def test_down_payment_capped(self):
		t = L.sale_totals(100000, 0, 0, 0, "Bank Financing", 999999, 0, 0)
		self.assertEqual((t["down"], t["financed"]), (100000.0, 0.0))

	def test_margin_commission_stock(self):
		self.assertEqual(L.margin(490000, 430000), 60000.0)
		self.assertEqual(L.commission(60000, 2.5), 1500.0)
		self.assertEqual(L.commission(-5000, 2.5), 0.0)
		self.assertEqual(L.days_in_stock("2026-10-01", today="2026-11-16"), 46)
		self.assertEqual(L.days_in_stock("2026-10-01", until="2026-10-11", today="2026-11-16"), 10)
		self.assertTrue(L.price_allowed(100, 90))
		self.assertFalse(L.price_allowed(80, 90))
		self.assertTrue(L.price_allowed(80, 0))


if __name__ == "__main__":
	unittest.main()
