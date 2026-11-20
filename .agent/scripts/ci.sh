#!/usr/bin/env bash
# Framework CI: lint, format, types, tests and agent-system validation.
set -euo pipefail

cd "$(dirname "$0")/.."

if python -m pip --version >/dev/null 2>&1; then
    python -m pip install --disable-pip-version-check -r requirements-dev.txt
else
    uv pip install --python "$(command -v python)" -r requirements-dev.txt
fi

ruff check tools tests
ruff format --check tools tests
mypy tools tests
pytest tests -q

python tools/forge.py validate
python tools/forge.py validate --graph
python tools/forge.py validate --conflicts
python tools/forge.py memory check
