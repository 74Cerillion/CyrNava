#!/usr/bin/env bash
# One isolated acquisition/thin-build attempt. No GUI, signing or publication.
set -euo pipefail
repo=/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
here=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ "$here" != "$repo" || -L "${BASH_SOURCE[0]}" ]]; then
    echo 'STOPPED: run the reviewed wrapper from the exact CyrNava checkout.' >&2
    exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B -u "$repo/packaging/flatpak/compatibility/binary-6.11.3/build_candidate.py" "$@"
