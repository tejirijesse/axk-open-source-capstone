"""Install and migrate hooks."""

import frappe

DEMO_ROLE = "AXK Capstone Demo"
MIN_DEMO_PASSWORD = 8

# Ready-made reviewer logins, one per trade screen plus a supervisor who starts on the overview.
# All share DEMO_ROLE, which is what trade_api._guard checks; the route is only where login lands.
# The password is never here: it comes from site config `axk_demo_password` (see docs/handover.md).
DEMO_USERS = [
    {"key": "coop", "email": "coop@capstone.axk.org", "first_name": "Claudine", "last_name": "Uwase",
     "label": "Cooperative", "organisation": "Koperative Twisungane", "route": "/trade/coop"},
    {"key": "inspector", "email": "inspector@capstone.axk.org", "first_name": "Josiane", "last_name": "Mukamana",
     "label": "Inspector", "organisation": "Independent inspection", "route": "/trade/inspect"},
    {"key": "logistics", "email": "logistics@capstone.axk.org", "first_name": "Eric", "last_name": "Habimana",
     "label": "Logistics", "organisation": "Swift Freight Logistics", "route": "/trade/logistics"},
    {"key": "port", "email": "port@capstone.axk.org", "first_name": "Aline", "last_name": "Ingabire",
     "label": "Port / Terminal", "organisation": "Kigali Logistics Platform & Terminal", "route": "/trade/port"},
    {"key": "buyer", "email": "buyer@capstone.axk.org", "first_name": "Patrick", "last_name": "Mugisha",
     "label": "Buyer", "organisation": "Goma Grain Traders", "route": "/trade/buy"},
    {"key": "supervisor", "email": "supervisor@capstone.axk.org", "first_name": "Grace", "last_name": "Uwimana",
     "label": "Supervisor", "organisation": "AXK programme", "route": "/trade"},
]
DEMO_EMAILS = frozenset(u["email"] for u in DEMO_USERS)


def ensure_roles():
    """Role that may use the trade screens after signing in (reviewers, supervisor).

    desk_access is forced off on every run: Frappe makes a user a System User when any of their roles has desk
    access, so this flag is what keeps the demo logins out of /app."""
    if not frappe.db.exists("Role", DEMO_ROLE):
        frappe.get_doc({"doctype": "Role", "role_name": DEMO_ROLE, "desk_access": 0}).insert(ignore_permissions=True)
    elif frappe.db.get_value("Role", DEMO_ROLE, "desk_access"):
        frappe.db.set_value("Role", DEMO_ROLE, "desk_access", 0)
    frappe.db.commit()


def demo_password():
    """The shared demo password from site config `axk_demo_password`, or None when unset or too short."""
    value = frappe.conf.get("axk_demo_password")
    value = "" if value is None else str(value)
    return value if len(value.strip()) >= MIN_DEMO_PASSWORD else None


def ensure_demo_users():
    """Create or reconcile the demo logins. Safe to run on every migrate.

    Each run puts every demo user back to: enabled Website User, exactly DEMO_ROLE, the configured password.
    Anything else found on the account (System Manager, a desk role, a changed password) is removed, because these
    logins may be published. Skips everything when `axk_demo_password` is unset."""
    pwd = demo_password()
    if not pwd:
        msg = f"AXK demo users skipped: site config axk_demo_password is unset or under {MIN_DEMO_PASSWORD} characters"
        frappe.logger("axk_capstone").info(msg)
        print(msg)
        return []

    from frappe.utils.password import update_password

    ensure_roles()
    done = []
    for spec in DEMO_USERS:
        email = spec["email"]
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.new_doc("User")
            user.email = email
        user.first_name = spec["first_name"]
        user.last_name = spec["last_name"]
        user.user_type = "Website User"
        user.enabled = 1
        user.send_welcome_email = 0
        user.role_profile_name = None  # a role profile would re-add its roles in User.validate
        user.set("roles", [{"role": DEMO_ROLE}])
        user.flags.ignore_permissions = True
        user.save()
        if user.user_type != "Website User":
            frappe.throw(f"Demo user {email} came out as {user.user_type}; refusing to set its password")
        # Straight into the password table: the reviewer password is not held to the site's password policy.
        update_password(email, pwd)
        done.append(email)
    frappe.db.commit()
    return done
