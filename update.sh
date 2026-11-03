#!/bin/sh
# Run from the downloaded newer source; existing stopped-client transaction engine.
set -eu
entry_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec /usr/bin/python3.14 -B -I "$entry_dir/packaging/native/source_install.py" --operation update "$@"
