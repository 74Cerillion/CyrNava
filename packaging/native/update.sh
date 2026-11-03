#!/bin/sh
set -eu
entry_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec sh "$entry_dir/install.sh" update "$@"
