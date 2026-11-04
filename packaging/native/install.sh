#!/bin/sh
# Shared Python engine; never elevates privileges or downloads dependencies.
set -eu
entry_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec /usr/bin/python3.14 -B -I "$entry_dir/../../desktop/install_engine.py" "$@"
