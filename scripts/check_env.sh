#!/usr/bin/env bash
# One screen that shows the development environment is set up: toolchain, database, cache, app server,
# installed apps, contracts and Stellar testnet. Read-only: it starts, changes and signs nothing.
#   make check-env            (BENCH and SITE as in the Makefile)
set -uo pipefail

BENCH="${AXK_BENCH:-$(cd "$(dirname "$0")/../.." && pwd)/axk-bench}"
SITE="${AXK_SITE:-axk.localhost}"
URL="${AXK_URL:-http://localhost:8000}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="/opt/homebrew/opt/rustup/bin:$HOME/.cargo/bin:$HOME/.venvs/bench/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/mariadb@10.11/bin:/opt/homebrew/bin:$PATH"

FAILS=0
ok()   { printf "  \033[32m✓\033[0m %-22s %s\n" "$1" "$2"; }
bad()  { printf "  \033[31m✕\033[0m %-22s %s\n" "$1" "$2"; FAILS=$((FAILS + 1)); }
section() { printf "\n\033[1m%s\033[0m\n" "$1"; }
first() { "$@" 2>/dev/null | head -1; }

section "Repository"
ok "Commit" "$(git -C "$REPO" log -1 --format='%h %s' 2>/dev/null)"
ok "Remote" "$(git -C "$REPO" remote get-url origin 2>/dev/null)"

section "Toolchain"
v=$(first rustc --version) && [ -n "$v" ] && ok "Rust" "$v" || bad "Rust" "not found (make toolchain)"
rustup target list --installed 2>/dev/null | grep -q wasm32v1-none && ok "wasm target" "wasm32v1-none" || bad "wasm target" "missing (rustup target add wasm32v1-none)"
v=$(first stellar --version) && [ -n "$v" ] && ok "stellar-cli" "$v" || bad "stellar-cli" "not found (make toolchain)"
v=$(first python3 --version) && ok "Python" "$v"
v=$(first bench --version) && [ -n "$v" ] && ok "Frappe bench CLI" "$v" || bad "Frappe bench CLI" "not found"

section "Database and cache"
if brew services list 2>/dev/null | grep -E "^mariadb" | grep -q started; then
  ok "MariaDB" "$(first mariadb --version | sed -E 's/.*Distrib ([^,]+).*/\1/;s/.*from ([0-9.]+-MariaDB).*/\1/') · running"
else
  bad "MariaDB" "not running (brew services start mariadb@10.11)"
fi
for pair in "cache:13000" "queue:11000"; do
  name=${pair%%:*}; port=${pair##*:}
  [ "$(redis-cli -p "$port" ping 2>/dev/null)" = "PONG" ] && ok "Redis $name" "port $port · PONG" || bad "Redis $name" "port $port not answering (make run-frappe)"
done

section "Application server"
[ -d "$BENCH" ] && ok "Bench" "$BENCH" || bad "Bench" "not found at $BENCH (set AXK_BENCH)"
if [ -d "$BENCH" ]; then
  (cd "$BENCH" && bench version 2>/dev/null | grep -E "^(frappe|axk_capstone) " | while read -r app ver; do ok "App $app" "$ver"; done)
  link=$(readlink "$BENCH/apps/axk_capstone" 2>/dev/null)
  [ "$link" = "$REPO/frappe_app/axk_capstone" ] && ok "axk_capstone source" "this repository" || bad "axk_capstone source" "bench uses ${link:-?}"
fi
[ "$(curl -s -m 5 "$URL/api/method/ping" 2>/dev/null)" = '{"message":"pong"}' ] && ok "Web server" "$URL · pong" || bad "Web server" "$URL not answering (make run-frappe)"
net=$(curl -s -m 10 "$URL/api/method/axk_capstone.trade_api.overview" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['message']['network'])" 2>/dev/null)
[ -n "$net" ] && ok "Trade API" "network: $net" || bad "Trade API" "no answer from axk_capstone.trade_api.overview"

section "Contracts (Stellar testnet)"
if [ -f "$REPO/scripts/.demo-state.env" ]; then
  # shellcheck disable=SC1091
  source "$REPO/scripts/.demo-state.env"
  for c in REGISTRY ESCROW SPLITTER ATTEST TOKEN; do
    id="${!c:-}"; [ -n "$id" ] && ok "$c" "$id" || bad "$c" "missing (make demo)"
  done
else
  bad "Contract IDs" "scripts/.demo-state.env missing (make demo, then make contracts-config)"
fi
h=$(curl -s -m 10 -X POST -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"getLatestLedger"}' https://soroban-testnet.stellar.org 2>/dev/null \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['sequence'])" 2>/dev/null)
[ -n "$h" ] && ok "Soroban RPC" "testnet reachable · latest ledger $h" || bad "Soroban RPC" "testnet not reachable"

printf "\n"
if [ "$FAILS" -eq 0 ]; then printf "\033[32mEnvironment ready.\033[0m\n"; else printf "\033[31m%s check(s) failed.\033[0m\n" "$FAILS"; fi
exit $(( FAILS > 0 ))
