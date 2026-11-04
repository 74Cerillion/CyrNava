import sys

if sys.argv[1:] == ["--manage-data"]:
    from .maintenance import run
elif not sys.argv[1:]:
    from .application import run as run_desktop

    def run():
        return run_desktop(offer_import=True)
else:
    raise SystemExit("Supported option: --manage-data")

raise SystemExit(run())
