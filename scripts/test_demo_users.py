"""Tests for the reviewer demo logins (setup.ensure_demo_users, demo.py).

The unit tests stub frappe with an in-memory User/Role store, so they need nothing installed. The stub mirrors the
two Frappe behaviours the code depends on: User.set_system_user (a user is a System User when any role has
desk_access) and populate_role_profile_roles (a role profile re-adds its roles on save).

The live tests log in as each demo user against AXK_BASE_URL and try to escalate. They run only with
AXK_DEMO_LIVE=1 and need AXK_DEMO_PASSWORD (the value of site config axk_demo_password). Set
AXK_DEMO_EXPECT_PUBLIC=1 when axk_demo_logins_public is on.

    python3 scripts/test_demo_users.py
    AXK_DEMO_LIVE=1 AXK_BASE_URL=https://capstone.axk.org AXK_DEMO_PASSWORD=... python3 scripts/test_demo_users.py
"""

import ast
import http.cookiejar
import json
import os
import sys
import types
import unittest
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
APP = os.path.join(ROOT, "frappe_app", "axk_capstone")
sys.path.insert(0, APP)

BASE_URL = os.environ.get("AXK_BASE_URL", "http://localhost:8000")
LIVE = os.environ.get("AXK_DEMO_LIVE") == "1"
# Fixture values for the stubbed site config and attack attempts; none is a real credential.
CONF_PWD = "test-demo-pass-1"
OTHER_PWD = "test-other-pass-99"


def _read(path):
    with open(path) as fh:
        return fh.read()


# -- frappe stub ------------------------------------------------------------------------------------------------

class ValidationError(Exception):
    pass


class PermissionError_(Exception):
    pass


class RateLimitExceededError(Exception):
    pass


class Flags(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v):
        self[k] = v


class Row(types.SimpleNamespace):
    pass


class Store:
    def __init__(self):
        self.roles = {}            # name -> {"desk_access": int}
        self.role_profiles = {}    # name -> [role, ...]
        self.users = {}            # email -> FakeUser
        self.passwords = {}        # email -> password
        self.inserts = 0
        self.commits = 0
        self.log = []
        self.cache = {}


class FakeUser:
    def __init__(self, store, **fields):
        self._store = store
        self._new = True
        self.flags = Flags()
        self.email = None
        self.first_name = self.last_name = None
        self.user_type = None
        self.enabled = 1
        self.send_welcome_email = 1
        self.role_profile_name = None
        self.new_password = None
        self.roles = []
        for k, v in fields.items():
            setattr(self, k, v)

    @property
    def name(self):
        return self.email

    def get(self, field):
        return getattr(self, field, None)

    def set(self, field, rows):
        setattr(self, field, [Row(**r) for r in rows])

    def save(self):
        if self.role_profile_name:  # User.populate_role_profile_roles
            for r in self._store.role_profiles[self.role_profile_name]:
                self.roles.append(Row(role=r))
        # User.set_system_user for the standard user types
        desk = any(self._store.roles.get(r.role, {}).get("desk_access") for r in self.roles)
        self.user_type = "System User" if desk else "Website User"
        if self._new:
            if self.email in self._store.users:
                raise ValidationError(f"Duplicate user {self.email}")
            self._store.inserts += 1
            self._new = False
        self._store.users[self.email] = self
        return self

    def role_names(self):
        return [r.role for r in self.roles]


class FakeRoleDoc:
    def __init__(self, store, d):
        self._store, self._d = store, d

    def insert(self, ignore_permissions=False):
        self._store.roles[self._d["role_name"]] = {"desk_access": self._d.get("desk_access", 0)}
        return self


class FakeDB:
    def __init__(self, frappe_mod):
        self.f = frappe_mod

    @property
    def s(self):
        return self.f._store

    def exists(self, doctype, name):
        table = {"Role": self.s.roles, "User": self.s.users}[doctype]
        return name if name in table else None

    def get_value(self, doctype, name, field):
        assert doctype == "Role"
        return self.s.roles.get(name, {}).get(field)

    def set_value(self, doctype, name, field, value):
        assert doctype == "Role"
        self.s.roles[name][field] = value

    def commit(self):
        self.s.commits += 1


class FakeCache:
    def __init__(self, store):
        self.s = store

    def make_key(self, k):
        return k

    def incr(self, k):
        self.s.cache[k] = self.s.cache.get(k, 0) + 1
        return self.s.cache[k]

    def expire(self, k, ttl):
        pass


def _throw(msg, exc=None):
    raise (exc or ValidationError)(msg)


def _whitelist(**kw):
    def deco(fn):
        fn._whitelist = kw
        return fn
    return deco


def build_frappe():
    f = types.ModuleType("frappe")
    f._store = Store()
    f.conf = {}
    f.session = types.SimpleNamespace(user="Administrator")
    f._roles = []
    f.db = FakeDB(f)
    f.ValidationError = ValidationError
    f.PermissionError = PermissionError_
    f.RateLimitExceededError = RateLimitExceededError
    f.throw = _throw
    f.whitelist = _whitelist
    f.get_roles = lambda user=None: list(f._roles)
    f.cache = lambda: FakeCache(f._store)
    f.logger = lambda name=None: types.SimpleNamespace(info=lambda m: f._store.log.append(m))
    f.new_doc = lambda doctype: FakeUser(f._store)

    def get_doc(arg, name=None):
        if isinstance(arg, dict):
            assert arg["doctype"] == "Role"
            return FakeRoleDoc(f._store, arg)
        assert arg == "User"
        return f._store.users[name]
    f.get_doc = get_doc

    utils = types.ModuleType("frappe.utils")
    for n in ("cint", "flt", "get_datetime", "get_system_timezone", "getdate", "nowdate", "now_datetime"):
        setattr(utils, n, lambda *a, **k: None)
    password = types.ModuleType("frappe.utils.password")
    password.update_password = lambda user, pwd: f._store.passwords.__setitem__(user, pwd)
    utils.password = password

    user_mod = types.ModuleType("frappe.core.doctype.user.user")
    user_mod.calls = []
    user_mod.update_password = lambda *a: user_mod.calls.append(a) or "/me"
    mods = {"frappe": f, "frappe.utils": utils, "frappe.utils.password": password,
            "frappe.core": types.ModuleType("frappe.core"),
            "frappe.core.doctype": types.ModuleType("frappe.core.doctype"),
            "frappe.core.doctype.user": types.ModuleType("frappe.core.doctype.user"),
            "frappe.core.doctype.user.user": user_mod}
    f.utils = utils
    sys.modules.update(mods)
    return f, user_mod


frappe, frappe_user_mod = build_frappe()
from axk_capstone import demo, setup  # noqa: E402
from axk_capstone.setup import DEMO_ROLE, DEMO_USERS  # noqa: E402

EXPECTED_ROUTES = {"coop": "/trade/coop", "inspector": "/trade/inspect", "logistics": "/trade/logistics",
                   "port": "/trade/port", "buyer": "/trade/buy", "supervisor": "/trade"}


class Base(unittest.TestCase):
    def setUp(self):
        frappe._store = Store()
        frappe.conf.clear()
        frappe.session.user = "Administrator"
        frappe._roles = []
        frappe_user_mod.calls.clear()


class EnsureDemoUsers(Base):
    def test_creates_one_website_user_per_role(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        done = setup.ensure_demo_users()
        s = frappe._store
        self.assertEqual(set(done), {u["email"] for u in DEMO_USERS})
        self.assertEqual(s.inserts, 6)
        for spec in DEMO_USERS:
            u = s.users[spec["email"]]
            self.assertEqual(u.user_type, "Website User")
            self.assertEqual(u.role_names(), [DEMO_ROLE])
            self.assertNotIn("System Manager", u.role_names())
            self.assertTrue(u.first_name and u.last_name)
            self.assertEqual(u.enabled, 1)
            self.assertEqual(u.send_welcome_email, 0)
            self.assertTrue(u.flags.ignore_permissions)
            self.assertEqual(s.passwords[spec["email"]], CONF_PWD)
        self.assertEqual(s.roles[DEMO_ROLE]["desk_access"], 0)

    def test_idempotent(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        setup.ensure_demo_users()
        setup.ensure_demo_users()
        s = frappe._store
        self.assertEqual(s.inserts, 6)
        self.assertEqual(len(s.users), 6)
        for u in s.users.values():
            self.assertEqual(u.role_names(), [DEMO_ROLE])

    def test_rerun_strips_escalation_and_restores_password(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        setup.ensure_demo_users()
        s = frappe._store
        coop = s.users["coop@capstone.axk.org"]
        s.roles["System Manager"] = {"desk_access": 1}
        s.role_profiles["Admins"] = ["System Manager"]
        coop.roles.append(Row(role="System Manager"))
        coop.role_profile_name = "Admins"
        coop.enabled = 0
        s.passwords[coop.email] = OTHER_PWD
        setup.ensure_demo_users()
        self.assertEqual(coop.role_names(), [DEMO_ROLE])
        self.assertEqual(coop.user_type, "Website User")
        self.assertIsNone(coop.role_profile_name)
        self.assertEqual(coop.enabled, 1)
        self.assertEqual(s.passwords[coop.email], CONF_PWD)

    def test_demo_role_desk_access_is_forced_off(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        frappe._store.roles[DEMO_ROLE] = {"desk_access": 1}
        setup.ensure_demo_users()
        self.assertEqual(frappe._store.roles[DEMO_ROLE]["desk_access"], 0)
        self.assertTrue(all(u.user_type == "Website User" for u in frappe._store.users.values()))

    def test_refuses_to_set_password_if_user_ends_up_system_user(self):
        # Belt and braces: if Frappe ever made the account a System User anyway, it gets no password.
        frappe.conf["axk_demo_password"] = CONF_PWD
        original = FakeUser.save

        def save_as_system_user(self):
            original(self)
            self.user_type = "System User"
            return self
        FakeUser.save = save_as_system_user
        try:
            with self.assertRaises(ValidationError):
                setup.ensure_demo_users()
        finally:
            FakeUser.save = original
        self.assertEqual(frappe._store.passwords, {})

    def test_skips_when_password_unset(self):
        self.assertEqual(setup.ensure_demo_users(), [])
        s = frappe._store
        self.assertEqual((s.users, s.passwords, s.inserts), ({}, {}, 0))
        self.assertIn("axk_demo_password", s.log[0])

    def test_skips_when_password_blank_or_short(self):
        for value in ("", "   ", " " * 12, "short", None):
            frappe.conf["axk_demo_password"] = value
            self.assertEqual(setup.ensure_demo_users(), [])
        self.assertEqual(frappe._store.users, {})

    def test_password_comes_only_from_conf(self):
        frappe.conf["axk_demo_password"] = 12345678  # set-config --parse stores a number
        setup.ensure_demo_users()
        self.assertEqual(set(frappe._store.passwords.values()), {"12345678"})

    def test_no_password_literal_in_source(self):
        src = _read(setup.__file__) + _read(demo.__file__)
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "update_password":
                for arg in node.args[1:2]:
                    self.assertNotIsInstance(arg, ast.Constant, "update_password called with a literal")

    def test_one_account_per_screen(self):
        self.assertEqual({u["key"]: u["route"] for u in DEMO_USERS}, EXPECTED_ROUTES)
        self.assertEqual(len({u["email"] for u in DEMO_USERS}), 6)
        self.assertTrue(all(u["email"].endswith("@capstone.axk.org") for u in DEMO_USERS))


class DemoAccounts(Base):
    def test_whitelisted_for_guests(self):
        self.assertTrue(demo.demo_accounts._whitelist.get("allow_guest"))

    def test_flag_off_never_returns_password(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        for flag in (None, 0, "0", "", "false", "no"):
            frappe.conf["axk_demo_logins_public"] = flag
            rows = demo.demo_accounts()
            self.assertEqual(len(rows), 6)
            self.assertTrue(all("password" not in r for r in rows))
            self.assertNotIn(CONF_PWD, json.dumps(rows))

    def test_flag_on_returns_password(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        for flag in (1, "1", True, "true", "Yes", "on"):
            frappe.conf["axk_demo_logins_public"] = flag
            rows = demo.demo_accounts()
            self.assertTrue(all(r["password"] == CONF_PWD for r in rows), flag)

    def test_rows_carry_label_email_route(self):
        frappe.conf["axk_demo_password"] = CONF_PWD
        rows = {r["key"]: r for r in demo.demo_accounts()}
        self.assertEqual({k: r["route"] for k, r in rows.items()}, EXPECTED_ROUTES)
        self.assertEqual(rows["coop"]["email"], "coop@capstone.axk.org")
        self.assertEqual(rows["inspector"]["label"], "Inspector")
        self.assertTrue(all(r["full_name"] and r["organisation"] for r in rows.values()))

    def test_empty_when_password_unset(self):
        frappe.conf["axk_demo_logins_public"] = 1
        self.assertEqual(demo.demo_accounts(), [])


class Landing(Base):
    def test_each_demo_user_lands_on_its_screen(self):
        for u in DEMO_USERS:
            self.assertEqual(demo.landing_page(u["email"]), EXPECTED_ROUTES[u["key"]])
        self.assertEqual(demo.landing_page("COOP@capstone.axk.org "), "/trade/coop")

    def test_other_users_fall_through(self):
        for user in ("reviewer@capstone.axk.org", "Administrator", "Guest", "", None):
            self.assertIsNone(demo.landing_page(user))


class AccountFixed(Base):
    def test_demo_user_cannot_save_a_user(self):
        frappe.session.user = "coop@capstone.axk.org"
        for target in ("coop@capstone.axk.org", "buyer@capstone.axk.org"):
            for change in ({"new_password": OTHER_PWD}, {"enabled": 0}, {"first_name": "Renamed"}, {}):
                doc = FakeUser(frappe._store, email=target, **change)
                with self.assertRaises(PermissionError_, msg=(target, change)):
                    demo.block_account_changes(doc)

    def test_internal_saves_with_ignore_permissions_pass(self):
        frappe.session.user = "coop@capstone.axk.org"
        doc = FakeUser(frappe._store, email="coop@capstone.axk.org")
        doc.flags.ignore_permissions = True
        demo.block_account_changes(doc)

    def test_other_account_cannot_save_a_demo_user(self):
        for user in ("reviewer@capstone.axk.org", "Guest"):
            frappe.session.user = user
            doc = FakeUser(frappe._store, email="coop@capstone.axk.org", new_password=OTHER_PWD)
            with self.assertRaises(PermissionError_, msg=user):
                demo.block_account_changes(doc)

    def test_admins_may_save_a_demo_user(self):
        frappe.session.user = "Administrator"
        demo.block_account_changes(FakeUser(frappe._store, email="coop@capstone.axk.org", enabled=0))
        frappe.session.user, frappe._roles = "ops@capstone.axk.org", ["System Manager"]
        demo.block_account_changes(FakeUser(frappe._store, email="coop@capstone.axk.org", enabled=0))

    def test_non_demo_users_unaffected(self):
        for user in ("reviewer@capstone.axk.org", "Guest"):
            frappe.session.user = user
            demo.block_account_changes(FakeUser(frappe._store, email=user, new_password=OTHER_PWD))

    def test_demo_user_cannot_be_renamed(self):
        for user in ("coop@capstone.axk.org", "reviewer@capstone.axk.org"):
            frappe.session.user = user
            doc = FakeUser(frappe._store, email="coop@capstone.axk.org")
            with self.assertRaises(PermissionError_, msg=user):
                demo.block_rename(doc, "before_rename", "coop@capstone.axk.org", "gone@capstone.axk.org", False)
        frappe.session.user = "coop@capstone.axk.org"
        with self.assertRaises(PermissionError_):
            demo.block_rename(FakeUser(frappe._store, email="x@capstone.axk.org"), "before_rename",
                              "x@capstone.axk.org", "y@capstone.axk.org", False)

    def test_no_account_can_be_renamed_onto_a_demo_email(self):
        frappe.session.user = "reviewer@capstone.axk.org"
        for target in ("coop@capstone.axk.org", "COOP@capstone.axk.org"):
            with self.assertRaises(PermissionError_, msg=target):
                demo.block_rename(FakeUser(frappe._store, email="reviewer@capstone.axk.org"), "before_rename",
                                  "reviewer@capstone.axk.org", target, False)

    def test_rename_allowed_for_admin_and_other_records(self):
        frappe.session.user = "Administrator"
        demo.block_rename(FakeUser(frappe._store, email="coop@capstone.axk.org"), "before_rename",
                          "coop@capstone.axk.org", "c2@capstone.axk.org", False)
        frappe.session.user = "reviewer@capstone.axk.org"
        demo.block_rename(FakeUser(frappe._store, email="a@capstone.axk.org"), "before_rename",
                          "a@capstone.axk.org", "b@capstone.axk.org", False)

    def test_demo_user_record_cannot_be_shared(self):
        for user in ("coop@capstone.axk.org", "reviewer@capstone.axk.org"):
            frappe.session.user = user
            share = types.SimpleNamespace(share_doctype="User", share_name="coop@capstone.axk.org",
                                          user="reviewer@capstone.axk.org", everyone=0)
            with self.assertRaises(PermissionError_, msg=user):
                demo.block_share(share)
            share.user, share.everyone = None, 1
            with self.assertRaises(PermissionError_, msg=user):
                demo.block_share(share)

    def test_share_allowed_for_admin_and_other_doctypes(self):
        frappe.session.user = "Administrator"
        demo.block_share(types.SimpleNamespace(share_doctype="User", share_name="coop@capstone.axk.org"))
        frappe.session.user = "reviewer@capstone.axk.org"
        demo.block_share(types.SimpleNamespace(share_doctype="AXK Chain Trade", share_name="LOT-1"))
        demo.block_share(types.SimpleNamespace(share_doctype="User", share_name="reviewer@capstone.axk.org"))

    def test_update_password_override_refuses_demo_user(self):
        frappe.session.user = "port@capstone.axk.org"
        with self.assertRaises(PermissionError_):
            demo.update_password(OTHER_PWD, 0, None, CONF_PWD)
        self.assertEqual(frappe_user_mod.calls, [])

    def test_update_password_override_delegates_for_everyone_else(self):
        for user in ("Guest", "reviewer@capstone.axk.org", "Administrator"):
            frappe.session.user = user
            self.assertEqual(demo.update_password(OTHER_PWD, 1, "reset-key", None), "/me")
        self.assertEqual(frappe_user_mod.calls[0], (OTHER_PWD, 1, "reset-key", None))
        self.assertEqual(len(frappe_user_mod.calls), 3)
        self.assertEqual(demo.update_password._whitelist, {"allow_guest": True, "methods": ["POST"]})


class Hooks(unittest.TestCase):
    def test_hooks_wired(self):
        tree = ast.parse(_read(os.path.join(APP, "axk_capstone", "hooks.py")))
        hooks = {t.id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) for t in n.targets}
        for h in ("after_install", "after_migrate"):
            self.assertEqual(hooks[h], ["axk_capstone.setup.ensure_roles", "axk_capstone.setup.ensure_demo_users"])
        self.assertEqual(hooks["get_website_user_home_page"], "axk_capstone.demo.landing_page")
        self.assertEqual(hooks["doc_events"]["User"]["before_validate"], "axk_capstone.demo.block_account_changes")
        self.assertEqual(hooks["doc_events"]["User"]["before_rename"], "axk_capstone.demo.block_rename")
        self.assertEqual(hooks["doc_events"]["DocShare"]["validate"], "axk_capstone.demo.block_share")
        self.assertEqual(hooks["override_whitelisted_methods"]["frappe.core.doctype.user.user.update_password"],
                         "axk_capstone.demo.update_password")


class TradeGuard(Base):
    """A demo login passes _guard and is still throttled per user."""

    @classmethod
    def setUpClass(cls):
        from axk_capstone import trade_api
        cls.api = trade_api

    def test_demo_user_passes_guard(self):
        frappe.session.user = "coop@capstone.axk.org"
        frappe._roles = [DEMO_ROLE, "All", "Guest"]
        self.api._guard()

    def test_user_without_demo_role_is_refused(self):
        frappe.session.user = "someone@capstone.axk.org"
        frappe._roles = ["All", "Guest"]
        with self.assertRaises(PermissionError_):
            self.api._guard()

    def test_throttle_is_per_demo_user(self):
        frappe.session.user = "buyer@capstone.axk.org"
        for _ in range(self.api.SIGN_LIMIT_PER_HOUR):
            self.api._throttle()
        with self.assertRaises(RateLimitExceededError):
            self.api._throttle()
        frappe.session.user = "supervisor@capstone.axk.org"
        self.api._throttle()

    def test_every_endpoint_guards_first(self):
        tree = ast.parse(_read(self.api.__file__))
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            if not any("whitelist" in ast.unparse(d) for d in fn.decorator_list):
                continue
            body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
            self.assertEqual(ast.unparse(body[0]), "_guard()", fn.name)


# -- live -------------------------------------------------------------------------------------------------------

class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, method, data=None, http_method="POST"):
        url = f"{BASE_URL}/api/method/{method}"
        body = None
        if http_method == "GET" and data:
            url += "?" + urllib.parse.urlencode(data)
        elif data is not None:
            body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, method=http_method, headers={"Accept": "application/json"})
        try:
            with self.opener.open(req) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, json.loads(raw)
            except ValueError:
                return e.code, {"raw": raw[:200]}

    def page(self, path):
        try:
            with self.opener.open(f"{BASE_URL}{path}") as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code


@unittest.skipUnless(LIVE, "set AXK_DEMO_LIVE=1 and AXK_DEMO_PASSWORD to run against a server")
class Live(unittest.TestCase):
    PWD = os.environ.get("AXK_DEMO_PASSWORD", "")

    def login(self, email):
        c = Client()
        status, body = c.call("login", {"usr": email, "pwd": self.PWD})
        self.assertEqual(status, 200, body)
        return c, body

    def test_demo_accounts_matches_flag(self):
        status, body = Client().call("axk_capstone.demo.demo_accounts", http_method="GET")
        self.assertEqual(status, 200)
        rows = body["message"]
        self.assertEqual(len(rows), 6)
        if os.environ.get("AXK_DEMO_EXPECT_PUBLIC") == "1":
            self.assertTrue(all(r.get("password") == self.PWD for r in rows))
        else:
            self.assertTrue(all("password" not in r for r in rows))
            self.assertNotIn(self.PWD, json.dumps(body))

    def test_each_login_lands_on_its_screen_and_stays_out_of_desk(self):
        for u in DEMO_USERS:
            c, body = self.login(u["email"])
            self.assertEqual(body.get("home_page"), u["route"], u["email"])
            self.assertEqual(body.get("message"), "No App")  # Website User branch of set_user_info
            self.assertEqual(c.page("/app"), 403, u["email"])
            status, _ = c.call("axk_capstone.trade_api.overview", http_method="GET")
            self.assertEqual(status, 200, u["email"])  # _guard accepts the demo role

    def test_cannot_escalate(self):
        email = "coop@capstone.axk.org"
        c, _ = self.login(email)
        status, body = c.call("frappe.client.get", {"doctype": "User", "name": email}, "GET")
        self.assertEqual(status, 200)
        doc = body["message"]
        doc["roles"].append({"role": "System Manager", "doctype": "Has Role"})
        doc["user_type"] = "System User"
        c.call("frappe.client.save", {"doc": json.dumps(doc)})
        status, body = c.call("frappe.client.get", {"doctype": "User", "name": email}, "GET")
        self.assertEqual([r["role"] for r in body["message"]["roles"]], [DEMO_ROLE])
        self.assertEqual(body["message"]["user_type"], "Website User")
        status, _ = c.call("frappe.client.insert", {"doc": json.dumps({"doctype": "Role", "role_name": "Pwn"})})
        self.assertIn(status, (403, 417))
        status, _ = c.call("frappe.client.insert", {"doc": json.dumps(
            {"doctype": "User", "email": "pwn@capstone.axk.org", "first_name": "Pwn",
             "roles": [{"role": "System Manager"}]})})
        self.assertIn(status, (403, 417))

    def test_cannot_change_or_disable_shared_account(self):
        email = "buyer@capstone.axk.org"
        c, _ = self.login(email)
        status, _ = c.call("frappe.client.set_value",
                           {"doctype": "User", "name": email, "fieldname": "new_password", "value": OTHER_PWD})
        self.assertEqual(status, 403)
        status, _ = c.call("frappe.client.set_value",
                           {"doctype": "User", "name": email, "fieldname": "enabled", "value": 0})
        self.assertEqual(status, 403)
        status, _ = c.call("frappe.core.doctype.user.user.update_password",
                           {"new_password": OTHER_PWD, "old_password": self.PWD})
        self.assertEqual(status, 403)
        self.login(email)  # the original password still works

    def test_cannot_rename_or_share_shared_account(self):
        email = "coop@capstone.axk.org"
        c, _ = self.login(email)
        status, _ = c.call("frappe.client.rename_doc",
                           {"doctype": "User", "old_name": email, "new_name": "gone@capstone.axk.org"})
        self.assertIn(status, (403, 417))
        status, _ = c.call("frappe.share.add",
                           {"doctype": "User", "name": email, "user": "buyer@capstone.axk.org", "write": 1})
        self.assertIn(status, (403, 417))
        status, _ = c.call("frappe.share.add", {"doctype": "User", "name": email, "everyone": 1, "write": 1})
        self.assertIn(status, (403, 417))
        self.login(email)


if __name__ == "__main__":
    unittest.main(verbosity=2)
