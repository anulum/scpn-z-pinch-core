# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Z-Pinch Core — local gate entry points

VENV := .venv/bin
PYTHON := $(VENV)/python

.PHONY: venv lint typecheck test validate docs preflight

venv:
	python3 -m venv .venv
	$(VENV)/pip install --require-virtualenv -r requirements-dev.txt

lint:
	$(VENV)/ruff check .
	$(VENV)/ruff format --check .

typecheck:
	$(VENV)/mypy --strict tools tests

test:
	$(VENV)/pytest -q --cov=tools --cov-branch --cov-fail-under=100

validate:
	$(PYTHON) tools/validate_reactor_domain.py reactor-domain.json
	$(PYTHON) tools/derive_studio_descriptor.py --check
	$(PYTHON) tools/generate_capability_inventory.py --check

docs:
	$(PYTHON) tools/preflight.py --only docs

preflight:
	$(PYTHON) tools/preflight.py
