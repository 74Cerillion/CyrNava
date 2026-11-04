# Native Ubuntu installation and manual maintenance

**Current public target: source-first GitHub repository with an online installer.**
Use repository-root `bash install.sh` and `bash update.sh` from a reviewed versioned
source snapshot. The source adapter reuses the native transaction engine; dependencies are
recipient-acquired, frontend is built locally, and no bundled-wheel public ZIP is
required. See the [current installation guide](../../docs/native-installation.md)
for supported prerequisites, installation, policy setup and manual updates.

## Historical offline installer and acceptance records

The instructions below apply to the retained offline exported kits and original
accepted N2/N3 packages. Their `install.sh` is the exported kit entry point, not
the new repository-root source installer. They remain available through the
existing `install_cyrnava.sh` / `update_cyrnava.sh` archive interfaces.

## Retained archive maintenance interfaces

After independently authenticating a future release's installer/key, the normal
interface is:

```text
sh update_cyrnava.sh --archive RELEASE.zip --manifest manifest.json \
  --signature manifest.json.asc --key TRUSTED-PUBLIC-KEY \
  --fingerprint EXISTING-FULL-TRUSTED-PRIMARY-FINGERPRINT --root INSTALLATION-ROOT
sh uninstall_cyrnava.sh --root INSTALLATION-ROOT
sh install_cyrnava.sh reinstall --root INSTALLATION-ROOT --reuse-preserved-data
```

The exported kit's `update.sh`/`uninstall.sh` delegate to that same engine without
the repository wrappers. `install.sh rollback --root INSTALLATION-ROOT` explicitly
selects only a verified compatible prior binary. For exact same-artifact reinstall,
use `update.sh --reinstall` with the original authenticated package arguments.
The existing normal installation root/data mapping and trusted primary key remain
mandatory; a different key cannot be introduced from an update archive.

Finish saving and close all application/backend processes. The engine refuses
busy locks, changed code/providers/menu entries, incompatible schema/Qt/data
consumers and insufficient checkpoint space. It performs no downloads or sudo.
It stages full local wheel payloads in final version locations, validates every
stopped workspace, copies/verifies the entire native profile, then changes one
active selection. Existing workspace selection, origin/port, Qt preference/draft
storage and earlier releases remain. It does not initialize/migrate a real DB.

This initial boundary supports schema 5 and unchanged accepted application/data
consumers and dependency stack. Future application/storage/Qt changes need reviewed
compatibility support; a version string alone grants none. Interrupted transactions
block launch until explicit `install.sh recover --root INSTALLATION-ROOT` verifies
unchanged data/targets and restores coherent activation. No automatic database
rollback or data replacement occurs.

Uninstall removes managed menu/launch activation only. It **retains version payloads,
checkpoints, logs and all user data**, and makes no disk-reclaim claim. Explicit
reinstall reuses the verified retained bytes/data; changed data requires separate
recovery review. There is no purge option. Host policy removal is a separate,
explicit exact-profile administrative operation while the installation can still
be verified; the uninstaller never invokes it or changes global settings.

The existing **Backup and recovery** UI creates portable `.cyrnava` backups and
imports into new workspaces. Those backups intentionally exclude browser
preferences/drafts/pending uploads; new workspaces get separate Qt profiles.
Stopped native checkpoints retain those full-profile bytes, and normal updates/
reinstall do not reset appearance or select a different workspace. Never replace
current data with a backup automatically or promise reverse schema migration.

## Retained archive installer contract

The normal installer consumes a full archive and its signed manifest, an
independently trusted public key and full primary fingerprint. The manifest must
be a release for the exact platform/app identity. It refuses a candidate, a missing
signature, wrong/expired/revoked key, changed archive, unsafe files, existing
installation/profile or colliding desktop identity. It performs no downloads or
sudo actions. A full release ships a complete wheelhouse and built frontend; the
recipient needs no Git, Node, compiler or browser-based launcher.

System prerequisites include Ubuntu's Python 3.14 with venv/ensurepip, GPG, libc's
`ldd`, GNOME/GIO and the OS GUI libraries required by the measured wheels. Import,
installed-file and ELF checks detect missing dependencies before activation. The
installer does not install apt packages or relax host settings on the user's behalf.
No future runtime/interpreter compatibility is promised beyond the locked target.

The new candidate's desktop command enters `cyrnava-native`, whose exact-path
AppArmor profile must already be loaded. Both the ELF and Python engine reject a
missing/wrong profile. `apparmor_support.py` provides separate, explicitly pinned
host policy preparation/loading/removal; the installer never performs it silently.
The namespace allowance covers the named application process family and is not an
outer filesystem/network sandbox or protection against same-user replacement of
the writable installation. Ubuntu's global restrictions remain enabled.

For a later authenticated release, after independently authenticating the installer
and public key, the supported argument shape is:

```text
sh install.sh install --archive RELEASE.zip --manifest manifest.json \
  --signature manifest.json.asc --key OWNER-TRUSTED-PUBLIC-KEY \
  --fingerprint FULL-TRUSTED-PRIMARY-FINGERPRINT \
  --root ABSOLUTE-XDG-DATA-HOME/cyrnava-application
```

This is an interface reference, not a command for the current unsigned candidate.
Normal activation creates a stable program-root launcher, versioned payload/env,
`current.json` and native Desktop Entry. Data remains outside replaceable releases
at `$XDG_DATA_HOME/cyrnava/native`. Existing source/Flatpak data is never adopted.
Child-only verified Ubuntu schema selection handles the observed inherited GTK
schema issue. No loader-path fix, sandbox-disable flag or broad permission is used.

## Interrupted first installation

An incomplete transaction blocks launch. Review its private logs, then run the
same engine's `recover --root ABSOLUTE-ROOT` (`--disposable` only for an explicitly
isolated repository test root). Recovery removes only exact hash-matching activation
and menu files created by that first transaction; it preserves release bytes and
diagnostics. Changed files are not deleted. An existing successful installation
is never treated as an interrupted one. Update, rollback and uninstall use the
same transaction engine and the maintenance interfaces described above.
