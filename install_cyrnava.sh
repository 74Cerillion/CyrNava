#!/bin/sh
# Repository N2 entry point. The Python engine performs all validation/mutation.
set -eu
entry_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec /bin/sh "$entry_dir/packaging/native/install.sh" "$@"
