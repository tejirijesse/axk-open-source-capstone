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

Reviewer and admin logins are not in this repository. They are given out separately.

To add a reviewer: log in as Administrator → **User** → New → set email and password → add the role
**AXK Capstone Demo** → Save.

## Where keys and config live

| What | Where | Protection |
|---|---|---|
| Stellar testnet keys (verifier, coop, inspector, buyer, logistics, port, members, issuer) | `/home/axkdeploy/.config/stellar/identity/axk-*.toml` | directory `700`, files `600`, owner `axkdeploy`; never in git |
| Contract IDs, network, `stellar_bin` | `sites/capstone.axk.org/site_config.json` → `axk_stellar` | file `600`; IDs are public anyway |
| DB password, `axk_demo_mode`, `host_name` | same `site_config.json` | file `600` |
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
