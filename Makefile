# AXK capstone: one command per task. `make help` lists them.
SHELL := /bin/bash
export PATH := /opt/homebrew/opt/rustup/bin:$(HOME)/.cargo/bin:$(HOME)/.venvs/bench/bin:/opt/homebrew/opt/python@3.11/bin:/opt/homebrew/opt/mariadb@10.11/bin:/opt/homebrew/bin:$(PATH)

BENCH ?= $(abspath $(CURDIR)/../axk-bench)
SITE  ?= axk.localhost
SEED  ?= $(CURDIR)/axk_seed/data

.PHONY: help check-env show-db toolchain test test-contracts test-python test-ledger test-epcis test-odk test-report odk-form build demo run run-frappe seed seed-purge install-app contracts-config zip

help:            ## list tasks
	@grep -E "^[a-z-]+:.*## " $(MAKEFILE_LIST) | sed -E "s/:.*## /\t/" | column -t -s "$$(printf "\t")"

check-env:       ## read-only check of toolchain, MariaDB, Redis, app server, contracts and testnet
	@AXK_BENCH=$(BENCH) AXK_SITE=$(SITE) ./scripts/check_env.sh

show-db:         ## the five newest trades as stored in MariaDB (lot, status, transaction hashes)
	@cd $(BENCH) && bench --site $(SITE) mariadb -e 'select lot_ref, status, left(register_tx,12) as register_tx, left(inspect_tx,12) as inspect_tx, left(attest_tx,12) as attest_tx from `tabAXK Chain Trade` order by creation desc limit 5'

toolchain:       ## install Rust, the wasm target and stellar-cli (macOS, Homebrew)
	brew install rustup stellar-cli
	rustup default stable
	rustup target add wasm32v1-none

test:            ## all test suites: contracts, ledger, EPCIS, ODK, then end-to-end (end-to-end needs a server on :8000)
	cd contracts && cargo test
	python3 scripts/test_ledger.py
	python3 scripts/test_epcis.py
	python3 scripts/test_odk.py
	python3 scripts/test_trade.py

test-contracts:  ## smart contract unit tests (cargo)
	cd contracts && cargo test

test-ledger:     ## ledger object-model unit tests: records, contract clients, workflow (no server)
	python3 scripts/test_ledger.py

test-epcis:      ## GS1 EPCIS export tests (no server; schema checks need jsonschema)
	python3 scripts/test_epcis.py

test-odk:        ## ODK offline-inspection tests (no server)
	python3 scripts/test_odk.py

test-report:     ## technical report source checks (5-page body limit, output paths)
	python3 docs/report/test_generate_report.py

odk-form:        ## rebuild odk/axk_inspection.xlsx and .xml (needs openpyxl, pyxform)
	python3 odk/build_form.py

test-python:     ## end-to-end lifecycle and failure-mode tests (needs a server on :8000)
	python3 scripts/test_trade.py

build:           ## build the four contracts to wasm
	cd contracts && stellar contract build

demo:            ## deploy fresh contracts and run one verified trade on Stellar testnet
	./scripts/demo.sh

contracts-config: ## point the Frappe site at the contracts from the last demo run
	@source scripts/.demo-state.env && cd $(BENCH) && bench --site $(SITE) set-config --parse axk_stellar \
	  "{\"network\":\"testnet\",\"registry\":\"$$REGISTRY\",\"escrow\":\"$$ESCROW\",\"splitter\":\"$$SPLITTER\",\"attestation\":\"$$ATTEST\",\"token\":\"$$TOKEN\",\"stellar_bin\":\"$$(command -v stellar)\"}"

install-app:     ## link the axk_capstone Frappe app into the bench and install it on the site
	ln -sfn $(CURDIR)/frappe_app/axk_capstone $(BENCH)/apps/axk_capstone
	$(BENCH)/env/bin/pip install -q -e $(BENCH)/apps/axk_capstone
	grep -qx axk_capstone $(BENCH)/sites/apps.txt || echo axk_capstone >> $(BENCH)/sites/apps.txt
	cd $(BENCH) && bench --site $(SITE) install-app axk_capstone && bench build --app axk_capstone

seed:            ## import the synthetic five-year dataset (needs AXK's platform app; see docs/history-dataset.md)
	@test -d $(BENCH)/apps/axk_network || { echo "make seed needs the axk_network app in $(BENCH); see docs/history-dataset.md"; exit 1; }
	cp axk_seed/import_to_axk_network.py $(BENCH)/apps/axk_network/axk_network/capstone_seed.py
	cd $(BENCH) && bench --site $(SITE) execute axk_network.capstone_seed.run --kwargs "{'path': '$(SEED)'}"

seed-purge:      ## remove only the synthetic seed rows
	@test -d $(BENCH)/apps/axk_network || { echo "make seed-purge needs the axk_network app in $(BENCH)"; exit 1; }
	cd $(BENCH) && bench --site $(SITE) execute axk_network.capstone_seed.run --kwargs "{'path': '$(SEED)', 'purge': True}"

run:             ## offline UI simulation, no blockchain (Python only, http://localhost:8000)
	python3 scripts/server.py

run-frappe:      ## full stack on Stellar testnet (http://localhost:8000)
	AXK_BENCH=$(BENCH) ./scripts/run-frappe.sh

zip:             ## package the repository for submission (tracked files only)
	git archive --format=zip --prefix=axk-open-source-capstone/ -o axk-open-source-capstone.zip HEAD
	@ls -lh axk-open-source-capstone.zip
