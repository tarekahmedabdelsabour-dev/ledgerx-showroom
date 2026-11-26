app_name = "ledgerx_showroom"
app_title = "Showroom"
app_publisher = "LedgerX"
app_description = "Car showrooms: stock of new and used cars in one or many showrooms, purchase and preparation costs, bookings, sales with cash, installments, bank or loan financing, commissions"
app_email = "hello@ledgerx.local"
app_license = "mit"

required_apps = ["erpnext", "hrms", "ledgerx"]

add_to_apps_screen = [
	{
		"name": "ledgerx_showroom",
		"logo": "/assets/ledgerx_showroom/images/showroom.svg",
		"title": "Showroom",
		"route": "/desk/showroom",
		"has_permission": "ledgerx_showroom.install.check_app_permission",
	}
]

override_doctype_dashboards = {
	"Customer": "ledgerx_showroom.overrides.customer",
	"Employee": "ledgerx_showroom.overrides.employee",
	"Sales Invoice": "ledgerx_showroom.overrides.sales_invoice",
	"Journal Entry": "ledgerx_showroom.overrides.journal_entry",
	"Payment Entry": "ledgerx_showroom.overrides.payment_entry",
}

scheduler_events = {
	"cron": {
		"0 6 * * *": ["ledgerx_showroom.tasks.expire_bookings"],
		"0 4 1 * *": ["ledgerx_showroom.tasks.monthly_commissions"],
	},
}

after_install = "ledgerx_showroom.install.after_install"
after_migrate = "ledgerx_showroom.install.after_migrate"
