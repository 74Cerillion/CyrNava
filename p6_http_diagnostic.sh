#!/usr/bin/env bash
# Three small HTTPS comparisons. No Flatpak install/pull, build, GUI or signing.
set -euo pipefail
repo=/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
here=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ "$here" != "$repo" || -L "${BASH_SOURCE[0]}" ]]; then
    echo 'STOPPED: use the reviewed wrapper in the exact repository.' >&2
    exit 1
fi
exec python3 -B -u "$repo/packaging/flatpak/compatibility/binary-6.11.3/http_probe.py" "$@"
