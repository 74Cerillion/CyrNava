#!/bin/sh
# User-selected versioned GitHub source; no implicit elevation or moving HEAD.
set -eu
entry_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec /usr/bin/python3.14 -B -I "$entry_dir/packaging/native/source_install.py" --operation install "$@"
