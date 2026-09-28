#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Use the existing Replit Python environment used by the gunicorn workflow.
UV_PROJECT_ENVIRONMENT="$PWD/.pythonlibs" uv sync --locked
npm ci --no-audit --no-fund

# Check runtime imports without importing the app or touching its database.
.pythonlibs/bin/python -c "import flask, gunicorn, pypdf, jwt, requests"