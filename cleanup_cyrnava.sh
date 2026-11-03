#!/usr/bin/env bash
# Repository-only cleanup. The Python engine owns the preview and sole confirmation.
set -euo pipefail
repo=/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
script_dir=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ "$script_dir" != "$repo" || -L "${BASH_SOURCE[0]}" ]]; then
    echo 'STOPPED: use the audited wrapper in the exact CyrNava repository.' >&2
    exit 1
fi
for tool in python3 git du; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "STOPPED: required command is unavailable: $tool" >&2
        exit 1
    fi
done
if ! python3 -B -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
    echo 'STOPPED: Python 3.11 or newer is required.' >&2
    exit 1
fi
if [[ -L "$repo/ci" || -L "$repo/ci/cleanup_p6.py" || ! -f "$repo/ci/cleanup_p6.py" ]]; then
    echo 'STOPPED: the repository-local cleanup helper is missing or symlinked.' >&2
    exit 1
fi
exec python3 -B "$repo/ci/cleanup_p6.py" "$@"
