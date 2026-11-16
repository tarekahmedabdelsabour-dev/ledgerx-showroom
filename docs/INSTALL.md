# Install

```
cd ~/frappe-bench-v16/apps
git clone <repo-url> ledgerx_showroom
cd ~/frappe-bench-v16
echo "" >> sites/apps.txt && echo "ledgerx_showroom" >> sites/apps.txt   # skip if bench get-app is used
./env/bin/pip install -e apps/ledgerx_showroom
ln -sfn ~/frappe-bench-v16/apps/ledgerx_showroom/ledgerx_showroom/public sites/assets/ledgerx_showroom
bench --site mysite.localhost install-app ledgerx_showroom
bench --site mysite.localhost migrate && bench --site mysite.localhost clear-cache
```
Then restart the server.

## First setup (Showroom workspace)
1. **Showroom Settings:** company, the accounts (cars inventory, cost of cars sold, car sales revenue, extras revenue, financing income, VAT, financier fees), VAT rate, default markup and number of installments, salesman commission, and the Salary Component used for commission.
2. **Showroom:** one record per branch (each gets its own cost center and warehouse).
3. **Car Make / Car Model**, then **Financing Company** for banks or finance houses.
4. Receive a car with **Car > Acquire** (purchase), add preparation costs, run the inspection checklist, then **Mark Ready**.
5. Sell with **Car Sale**. Pick how the customer pays:
   - **Cash:** one payment.
   - **Showroom Installments:** down payment plus equal monthly installments with the markup you set; the schedule lives on the Sales Invoice (see the Installments Due report).
   - **Bank Financing:** down payment from the customer, the rest is due from the financier (fees can be deducted when the money arrives).
   - **Lending Loan:** creates a loan application in the Lending module (set the Loan Product and the Loan Clearing Account in settings).
6. To limit a salesman to his own branch, add a **User Permission** on Showroom for that user.
7. Roles are created automatically: Showroom Manager, Showroom Salesman, Showroom Accountant.

## Known limits
- Single currency (the company currency).
- The Lending link creates the loan application; when Lending disburses, the money is settled to the invoice through the Loan Clearing Account instead of being booked against the invoice by Lending itself.
- Down payments and deposits are applied from the same customer's unallocated payments, so a customer with unrelated advances may see them applied.
- Untested on a live site: only the pure calculation logic has automated tests. Try a full cycle (buy, prepare, book, sell, collect, deliver) on a test company first.
