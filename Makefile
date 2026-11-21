# Freehand Digitize — development and QA entry points.
#
# Recipes must use tabs. Every Python command runs through uv so the lockfile is
# authoritative; QGIS itself is provided by the host or a container, never by uv.

SHELL := /bin/bash

PLUGINNAME = freehand_digitize
QGIS_VERSION ?= 4
FLAKE8_TARGETS = core gui freehand_plugin.py __init__.py

# Keep the uv cache inside the workspace: some sandboxes expose a read-only
# $HOME cache and uv fails before resolving anything.
UV_CACHE_DIR ?= $(CURDIR)/.uvcache
export UV_CACHE_DIR

UV ?= uv
UV_RUN = $(UV) run --frozen
PYTHON ?= python3
# Interpreter used for QGIS integration tests; auto-detected when unset.
QGIS_PYTHON ?= $(shell $(UV_RUN) python scripts/find_qgis_python.py 2>/dev/null)
PYLUPDATE ?= pylupdate6
# Parent directory that exposes the plugin as ``freehand_digitize`` for tests.
TEST_PYTHONPATH ?= ..
LOCALES = en

PORTAL_ZIP ?= $(shell ls -t dist/*.zip 2>/dev/null | head -1)

.PHONY: help sync test test-qgis test-all lint format format-check flake8 mypy \
        analyzer agent-validate qgis-validate zip portal-check security-scan \
        qt6-check docker-build docker-test deploy docs-check transup transcompile \
        transclean i18n-check pre-release clean

help:
	@echo "Freehand Digitize targets:"
	@echo "  make sync            # uv lock --check + uv sync --frozen"
	@echo "  make test            # unit tests (no QGIS required)"
	@echo "  make test-qgis       # integration tests with the host QGIS"
	@echo "  make test-all        # both suites"
	@echo "  make lint            # ruff check"
	@echo "  make format          # ruff format (writes files)"
	@echo "  make flake8          # QGIS portal flake8 scope"
	@echo "  make mypy            # type-check core/"
	@echo "  make analyzer        # qgis-analyzer --max-cc 10"
	@echo "  make docs-check      # relative links in README/docs"
	@echo "  make transup         # extract .ts and apply master translations"
	@echo "  make transcompile    # compile .ts catalogs into .qm"
	@echo "  make i18n-check      # validate catalogs (unfinished/placeholders/.qm)"
	@echo "  make transclean      # remove compiled .qm files"
	@echo "  make agent-validate  # Agentic Forge validator"
	@echo "  make qgis-validate   # qgis-manage validate --strict"
	@echo "  make zip             # build and validate the plugin ZIP"
	@echo "  make security-scan   # qgis-manage security --portal"
	@echo "  make qt6-check       # pyqgis4-checker (Docker)"
	@echo "  make docker-test     # integration tests in the QGIS image"
	@echo "  make clean           # remove caches and build output"

sync:
	$(UV) lock --check
	$(UV) sync --frozen

test:
	PYTHONPATH=$(TEST_PYTHONPATH) $(UV_RUN) python -m unittest discover tests

test-qgis:
	@test -n "$(QGIS_PYTHON)" || (echo "❌ No QGIS Python found. Set QGIS_PYTHON=/path/to/python3."; exit 1)
	@QT_QPA_PLATFORM=offscreen REQUIRE_QGIS=1 PYTHONPATH=$(TEST_PYTHONPATH) $(QGIS_PYTHON) -m unittest discover -s tests/integration -t . ; \
	code=$$?; \
	if [ $$code -eq 139 ]; then \
		echo "⚠️  Tolerated QGIS teardown segfault (exit 139) after the tests."; \
	elif [ $$code -ne 0 ]; then \
		exit $$code; \
	fi

test-all: test test-qgis

lint:
	$(UV_RUN) ruff check .

format:
	$(UV_RUN) ruff format .

format-check:
	$(UV_RUN) ruff format --check .

docs-check:
	$(UV_RUN) python scripts/check_docs.py

transup:
	@for lang in $(LOCALES); do \
		echo "Extracting i18n/freehand_digitize_$$lang.ts..."; \
		$(PYLUPDATE) --no-obsolete --ts i18n/freehand_digitize_$$lang.ts \
			core/*.py gui/*.py freehand_plugin.py; \
		python3 scripts/i18n/apply_full.py $$lang scripts/i18n/master_data/$$lang.json; \
	done
	python3 scripts/i18n/update_metadata_languages.py

transcompile:
	$(UV_RUN) qgis-manage compile --type translations

transclean:
	rm -f i18n/*.qm

i18n-check:
	$(UV_RUN) python -m unittest tests.test_i18n_catalogs

flake8:
	$(UV_RUN) flake8 $(FLAKE8_TARGETS) --config .flake8

mypy:
	$(UV_RUN) mypy --config-file pyproject.toml --follow-imports=silent --explicit-package-bases core

analyzer:
	$(UV_RUN) qgis-analyzer analyze . --max-cc 10

agent-validate:
	$(UV_RUN) python .agent/tools/forge.py validate

qgis-validate:
	$(UV_RUN) qgis-manage validate --strict

zip:
	$(UV_RUN) qgis-manage package --repo-check
	@$(MAKE) --no-print-directory portal-check

portal-check:
	@test -n "$(PORTAL_ZIP)" || (echo "❌ No dist/*.zip found; run 'make zip' first."; exit 1)
	$(UV_RUN) qgis-manage validate --zip "$(PORTAL_ZIP)"

PORTAL_SECURITY_EXCLUDES = --exclude ".agent" --exclude ".agent-state" \
	--exclude ".ai-context" --exclude ".github" --exclude ".uvcache" \
	--exclude "docs" --exclude "tests" --exclude "freehandEditing" \
	--exclude "dist" --exclude ".venv"

security-scan:
	$(UV_RUN) qgis-manage security --portal --fail-on critical \
		$(PORTAL_SECURITY_EXCLUDES)

qt6-check:
	@test -n "$(PORTAL_ZIP)" || $(UV_RUN) qgis-manage package --repo-check
	@rm -rf .qgis-manage/qt6 && mkdir -p .qgis-manage/qt6
	@unzip -q "$(PORTAL_ZIP)" -d .qgis-manage/qt6
	docker run --rm --pull always --user $(shell id -u):$(shell id -g) \
		--workdir /workspace/ -v $(CURDIR)/.qgis-manage/qt6:/workspace/ \
		ghcr.io/qgis/pyqgis4-checker:main-ubuntu \
		pyqt5_to_pyqt6.py --dry_run --logfile /workspace/pyqt6_checker.log .
	@cp .qgis-manage/qt6/pyqt6_checker.log pyqt6_checker.log 2>/dev/null || true

docker-build:
	DOCKER_BUILDKIT=1 docker build -t freehand_digitize_test .

docker-test:
	docker run --rm -v $(CURDIR):/app/freehand_digitize \
		-w /app/freehand_digitize -e QT_QPA_PLATFORM=offscreen -e REQUIRE_QGIS=1 \
		-e PYTHONPATH=/app:/usr/share/qgis/python qgis/qgis:latest \
		python3 -m unittest discover tests/integration

deploy:
	$(UV_RUN) qgis-manage deploy --no-compile --qgis-version $(QGIS_VERSION)

pre-release: format-check lint docs-check i18n-check flake8 mypy analyzer agent-validate test test-qgis qgis-validate
	@echo "✅ Pre-release validation complete"

clean:
	@echo "🧹 Cleaning caches and build output (tracked files preserved)..."
	find . \( -path ./.venv -o -path ./.git -o -path ./freehandEditing \) -prune -o \
		-name "__pycache__" -type d -prune -exec rm -rf {} +
	find . \( -path ./.venv -o -path ./.git -o -path ./freehandEditing \) -prune -o \
		-name "*.pyc" -type f -exec rm -f {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .uvcache dist build .qgis-manage
