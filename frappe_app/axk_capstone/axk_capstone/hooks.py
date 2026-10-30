app_name = "axk_capstone"
app_title = "AXK Capstone"
app_publisher = "AXK Capstone contributors"
app_description = "Stellar verification and settlement layer for AXK Network; chain explorer"
app_email = "156300250+tejirijesse@users.noreply.github.com"
app_license = "mit"
# No required apps beyond Frappe. The synthetic five-year history on /chain appears only
# when a site also has the seed DocTypes installed (see docs/history-dataset.md).

after_install = ["axk_capstone.setup.ensure_roles", "axk_capstone.setup.ensure_demo_users"]
after_migrate = ["axk_capstone.setup.ensure_roles", "axk_capstone.setup.ensure_demo_users"]

# Reviewer demo logins (setup.DEMO_USERS): each lands on its own trade screen, and none can edit or re-password
# the shared account. Login uses LoginManager.set_user_info -> get_home_page -> this hook for Website Users.
get_website_user_home_page = "axk_capstone.demo.landing_page"
doc_events = {
    "User": {"before_validate": "axk_capstone.demo.block_account_changes",
             "before_rename": "axk_capstone.demo.block_rename"},
    "DocShare": {"validate": "axk_capstone.demo.block_share"},
}
override_whitelisted_methods = {
    "frappe.core.doctype.user.user.update_password": "axk_capstone.demo.update_password",
}
