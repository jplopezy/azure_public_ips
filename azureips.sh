#!/usr/bin/env bash
# Backwards-compatible entry point. Azure CLI queries and output are read-only.
set -euo pipefail
exec python3 "$(dirname "$0")/azure_scope.py" "$@"
