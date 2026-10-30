# Hosted deployment — handover

The live system is at **https://capstone.axk.org**. It is the full stack (Frappe app + four Soroban contracts) on
**Stellar testnet**. No real money moves.

## What runs where

```
browser ──HTTPS──▶ nginx (TLS, Let's Encrypt)
                     ├─ /assets/*      static files from the bench
                     ├─ /socket.io     Frappe socket.io       127.0.0.1:9009
                     └─ everything else ─▶ gunicorn (Frappe)   127.0.0.1:8073
                                            ├─ MariaDB 10.11   site database
                                            ├─ Redis           cache :13007, queue :13008
                                            └─ stellar-cli 28  signs and submits ──▶ Stellar testnet RPC
                                                                                     (lot-registry, escrow,
                                                                                      splitter, attestation)
```

| Piece | Value |
|---|---|
| Server | Ubuntu 24.04 VM, `quantabox` (4.222.216.100) |
| Linux user | `axkdeploy` (no login password; SSH key only) |
| Bench | `/home/axkdeploy/capstone-bench` — Frappe v15, Python 3.11 |
| App code | `/home/axkdeploy/axk-open-source-capstone` (git clone of this repository), linked into `capstone-bench/apps/axk_capstone` |
| Site | `capstone.axk.org` |
| Processes | supervisor groups `capstone-bench-web`, `capstone-bench-workers`, `capstone-bench-redis` |
| Web server | nginx vhost `/etc/nginx/sites-available/capstone.axk.org.conf` |

## Who can sign

Demo mode is **off** (`axk_demo_mode: 0`). Every trade screen and every signing endpoint calls `_guard()` in
`trade_api.py`, which refuses anyone who is not logged in with the **AXK Capstone Demo** role (or System Manager).
A visitor who is not logged in gets `Sign in to use the trade screens.` The public trace page and QR verification
stay open, because checking a certificate should not need an account. Each user is also limited to
30 transactions per hour (`_throttle()`).

Admin logins are not in this repository. They are given out separately.

To add a personal reviewer login: log in as Administrator → **User** → New → set email and password → add the
role **AXK Capstone Demo** → Save.

### Demo logins

Six ready-made Website User accounts, one per trade screen plus a supervisor. Each has only the
**AXK Capstone Demo** role (no desk, no System Manager) and lands on its own screen after login.

| Email | Name | Role | Lands on |
|---|---|---|---|
| `coop@capstone.axk.org` | Claudine Uwase | Cooperative | `/trade/coop` |
| `inspector@capstone.axk.org` | Josiane Mukamana | Inspector | `/trade/inspect` |
| `logistics@capstone.axk.org` | Eric Habimana | Logistics | `/trade/logistics` |
| `port@capstone.axk.org` | Aline Ingabire | Port / Terminal | `/trade/port` |
| `buyer@capstone.axk.org` | Patrick Mugisha | Buyer | `/trade/buy` |
| `supervisor@capstone.axk.org` | Grace Uwimana | Supervisor | `/trade` |

All six share one password, kept in site config and never in git. `bench migrate` creates the accounts, or
resets them if they already exist (role, Website User, enabled, password), so run it after any config change:

```bash
cd ~/capstone-bench
bench --site capstone.axk.org set-config axk_demo_password '<at least 8 characters>'
bench --site capstone.axk.org set-config axk_demo_logins_public 1    # show the password on the login page
bench --site capstone.axk.org migrate
```

- Without `axk_demo_password` (or under 8 characters) migrate skips the accounts and prints
  `AXK demo users skipped: ...`. Existing accounts are left as they are; disable them in desk to retire them.
- `axk_demo_logins_public` controls only whether `axk_capstone.demo.demo_accounts` (the login page's
  click-to-fill list) includes the password. Set it to `0` to hide it and hand the password out separately.
- The accounts are shared, so only Administrator or a System Manager can save, rename or share a demo
  account's User record. A demo login cannot edit any User record or use `/update-password`, and no other
  account can rename itself onto a demo email. Change the password with `set-config` + `migrate`, never
  through the account itself.
- Leave **System Settings > Force User to Reset Password** at 0. The demo accounts are never reset through
  the UI, so turning it on would lock all six out until it is turned off again.
- The 30-per-hour signing limit is per account, so everyone on the same demo login shares it.
- The landing screen comes from the `get_website_user_home_page` hook. A **Role** home page or a
  **Portal Settings** default home page would take priority, so leave both empty.

## Where keys and config live

| What | Where | Protection |
|---|---|---|
| Stellar testnet keys (verifier, coop, inspector, buyer, logistics, port, members, issuer) | `/home/axkdeploy/.config/stellar/identity/axk-*.toml` | directory `700`, files `600`, owner `axkdeploy`; never in git |
| Contract IDs, network, `stellar_bin` | `sites/capstone.axk.org/site_config.json` → `axk_stellar` | file `600`; IDs are public anyway |
| DB password, `axk_demo_mode`, `host_name` | same `site_config.json` | file `600` |
| Demo login password (`axk_demo_password`), `axk_demo_logins_public` | same `site_config.json` | file `600` |
| Administrator / reviewer passwords | `/home/axkdeploy/.capstone-secrets/` | directory `700`, files `600` |
| TLS certificate | `/etc/letsencrypt/live/capstone.axk.org/` | root only; certbot renews it |

The browser never sees a private key. It asks the server to act, the server checks the login and role, and
`chain.py` signs with stellar-cli on the server.

## Deploy a new version

```bash
ssh quantabox
sudo -iu axkdeploy
cd ~/axk-open-source-capstone && git pull
cd ~/capstone-bench
bench --site capstone.axk.org migrate
bench build --app axk_capstone
sudo supervisorctl restart capstone-bench-web: capstone-bench-workers:
```

New contracts (only if the Rust code changed): run `make demo` on a machine with the keys, then put the new IDs
into `axk_stellar` with `bench --site capstone.axk.org set-config --parse axk_stellar '{…}'` and restart.

## Restart

```bash
sudo supervisorctl restart capstone-bench-web: capstone-bench-workers:   # app only
sudo supervisorctl restart capstone-bench-redis:                          # redis
sudo systemctl reload nginx                                               # after an nginx change
```

## Check health

```bash
curl -s https://capstone.axk.org/api/method/ping          # {"message":"pong"}
sudo supervisorctl status | grep capstone-bench           # all RUNNING
tail -50 /home/axkdeploy/capstone-bench/logs/web.error.log
```

In the browser: log in, open `/trade/coop`, register a lot. The response has a transaction hash, and
https://stellar.expert/explorer/testnet shows it. If signing fails, the lot keeps the reason in `last_error`
and the screen shows it.

Common causes:
- **502 from nginx** — the app is down: restart `capstone-bench-web:`.
- **"Stellar transaction refused"** — testnet RPC hiccup, or a testnet reset wiped the accounts. Run `make demo`
  again for fresh accounts and contracts, then update `axk_stellar`.
- **Certificate expired** — `sudo certbot renew`.
