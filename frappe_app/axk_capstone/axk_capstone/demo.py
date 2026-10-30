"""Reviewer demo logins at runtime: the login-page account list, where each login lands, and keeping the shared
accounts unchangeable by the reviewers using them. The accounts themselves are created by setup.ensure_demo_users."""

import frappe

from axk_capstone.setup import DEMO_EMAILS, DEMO_USERS, demo_password

FIXED = "Demo accounts are shared and cannot be changed. Ask the site administrator."
_BY_EMAIL = {u["email"]: u for u in DEMO_USERS}
_TRUTHY = {"1", "true", "yes", "on"}


def logins_public():
    """True when site config `axk_demo_logins_public` is set: a deliberate choice to print the demo password on
    the login page (testnet demo only). Accepts 1 / "1" / true / "yes" / "on", as set-config may store either."""
    return str(frappe.conf.get("axk_demo_logins_public") or "").strip().lower() in _TRUTHY


@frappe.whitelist(allow_guest=True)
def demo_accounts():
    """Demo logins for the login page's click-to-fill: role label, name, organisation, email and landing route.

    Empty when `axk_demo_password` is unset (the accounts were never created). The password is included only
    when `axk_demo_logins_public` is on; otherwise reviewers get it separately."""
    pwd = demo_password()
    if not pwd:
        return []
    public = logins_public()
    out = []
    for u in DEMO_USERS:
        row = {"key": u["key"], "label": u["label"], "full_name": f"{u['first_name']} {u['last_name']}",
               "organisation": u["organisation"], "email": u["email"], "route": u["route"]}
        if public:
            row["password"] = pwd
        out.append(row)
    return out


def landing_page(user):
    """`get_website_user_home_page` hook: a demo login lands on its own screen. None leaves every other user
    on Frappe's normal home page resolution."""
    u = _BY_EMAIL.get((user or "").strip().lower())
    return u["route"] if u else None


def _admin():
    return frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()


def _fixed(name):
    """True when a non-admin session is touching a demo account, or is itself a demo login."""
    return not _admin() and ((name or "").lower() in DEMO_EMAILS or frappe.session.user in DEMO_EMAILS)


def block_account_changes(doc, method=None):
    """User `before_validate`: only an admin may save a demo account, and a demo login may not save any User.
    Frappe lets a user write their own User record at permlevel 0 (`new_password`, `enabled`) and share it onward,
    so keying on the session alone would let a second account edit the shared login. Keyed on the record too.
    Frappe's own internal saves pass ignore_permissions and are left alone."""
    if _fixed(doc.name) and not doc.flags.ignore_permissions:
        frappe.throw(FIXED, frappe.PermissionError)


def block_rename(doc, method=None, old=None, new=None, merge=False):
    """User `before_rename`: User allows rename and after_rename rewrites the email, so renaming a shared login
    would take it away from every reviewer until the next migrate. Renaming another account onto a demo email
    is refused too, so nobody can claim one before migrate creates it."""
    if _fixed(old or doc.name) or (not _admin() and (new or "").lower() in DEMO_EMAILS):
        frappe.throw(FIXED, frappe.PermissionError)


def block_share(doc, method=None):
    """DocShare `validate`: a demo account's User record cannot be shared, which would hand write access on it to
    another account (or to everyone)."""
    if doc.share_doctype == "User" and _fixed(doc.share_name):
        frappe.throw(FIXED, frappe.PermissionError)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
    """Override of frappe.core.doctype.user.user.update_password (the /update-password page). Refuses a signed-in
    demo user and hands every other call to Frappe unchanged (positional: new, logout_all_sessions, key, old)."""
    if frappe.session.user in DEMO_EMAILS:
        frappe.throw(FIXED, frappe.PermissionError)
    from frappe.core.doctype.user.user import update_password as frappe_update_password

    return frappe_update_password(new_password, logout_all_sessions, key, old_password)
