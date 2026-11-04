import os,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/"application"))
from desktop.native.application import configuration,run
configuration()
for key,value in [("XDG_DATA_HOME","data"),("XDG_CONFIG_HOME","config"),("XDG_CACHE_HOME","cache")]:
 os.environ[key]=str(root/"client"/value)
raise SystemExit(run())
