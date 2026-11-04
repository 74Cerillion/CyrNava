# Native Ubuntu installation and manual maintenance

## Current source-first native installation

Use the reviewed **v0.1.0** source checkout or source ZIP from
[GitHub Releases](https://github.com/74Cerillion/CyrNava/releases), followed by
`bash install.sh`. N1–N4 are owner-accepted. The source-first installation and
compatible update passed [CI 41648248846](https://github.com/74Cerillion/CyrNava/actions/runs/41648248846)
for commit `383970f4af683aad154eb1bccaafdd5a932d8b76`; the final publication commit
must also complete required CI. The older offline artifact and CI 41621033436
retain their original scope.

Supported target: Ubuntu 26.04 x86_64 / GNOME Wayland, ordinary system
`/usr/bin/python3.14`, Node 24.x and npm 11.x for installation/build only,
and the unchanged pinned Qt/PySide/Shiboken/WebEngine 6.11.3 family.
The reviewed development tools are Node 24.19.0 and npm 11.6.2.
No Node/npm server or external browser is needed after installation.

### Obtain and review an immutable source version

Use tag `v0.1.0` or its exact reviewed release commit. A source ZIP has
no Git history; installation does not require `.git`. A Git clone can be checked
out detached at the selected commit. Do not install from an automatically moving
branch, fetch changes during installation, or copy in an old built frontend.

Initial trust is in the repository/source you chose to execute. The included
per-file inventory detects changed/missing build inputs and binds the locks; a
hash stored beside an untrusted installer does not independently authenticate
that installer. A signed tag can add authenticity when an owner-approved key
and verification procedure actually exist; no such identity is invented here.
Do not refresh the source inventory merely to bypass an unexpected mismatch.

From that source directory:

```bash
bash install.sh --check-prerequisites
bash install.sh
```

The first command checks source/locks, platform/interpreter and required tools.
Neither command silently uses sudo or installs host packages. Missing prerequisites
are reported before preparation. Node/npm, compiler, readelf/ldd, GSettings/GIO,
desktop-file-utils, AppArmor/parser and Python venv/ensurepip must be available.
The installed Qt provider check also refuses missing native graphics/font/NSS/
sound libraries and conflicting Qt providers before activation.

If Ubuntu prerequisites are missing, review this proposed administrative action
and explicitly approve/execute it yourself; the installer does not run it:

```text
sudo apt-get update
sudo apt-get install --no-install-recommends python3.14-venv build-essential desktop-file-utils apparmor-utils libglib2.0-bin libnss3 libnspr4 libasound2t64 libegl1 libopengl0 libxkbcommon-x11-0 libxcb-cursor0 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libfontconfig1
```

Obtain supported Node/npm versions through a reviewed official installation
method if the existing Ubuntu-provided versions do not meet the check. Do not
automatically upgrade global npm/Python or disable host security to proceed.

### What installation does

The adapter verifies its source inventory and unchanged dependency locks, copies
only consumed sources into a new private working directory, runs locked
`npm ci` with dependency lifecycle scripts disabled, then explicitly builds the
existing frontend with pre/post build hooks disabled. npm package URLs must be
official HTTPS registry URLs with SHA-512 integrity.

The shared native engine creates the final version's private venv. Pip acquires
the exact 19 approved wheels from their pinned official PyPI file URLs over TLS,
using isolated/hash-required/binary-only acquisition without dependency resolution,
mirrors or caches. Every filename, byte count and SHA-256 is checked. Local
installation of that verified closure is followed by pip check, installed-file/
Qt-provider/ELF validation and real authenticated synthetic backend persistence
checks. A small existing native C bootstrap is compiled; Qt/Chromium is not built.

The wheel-free intermediate ZIP is an internal local staging format reused by
the accepted engine. It is not the public release asset. Downloaded wheels,
node_modules, generated frontend, private venv and logs must stay out of the
public source payload. See [dependency scope](native-source-obligations.md).

Default program root is `$XDG_DATA_HOME/cyrnava-application` (normally
`~/.local/share/cyrnava-application`); data stays separately at
`$XDG_DATA_HOME/cyrnava/native`. First install refuses existing profiles or
colliding desktop identities rather than adopting personal data. Previous
source/browser/Flatpak profiles require a separately reviewed migration or
explicit backup import. No data migration is performed by installation.

Preparation has bounded time/storage checks and preserves failed attempts.
The source path uses a separate measured budget; the historical offline package's
5 GiB build floor and its recorded failures are unchanged. Retain sufficient
space for a private environment, build dependencies and a full stopped-profile
checkpoint. Do not delete personal backups to pass a precondition.

### AppArmor and first desktop launch

A successful headless installation is not a renderer or GNOME-launch PASS.
The exact application-specific enforce policy must be reviewed and explicitly
loaded from a normal owner terminal before the native entry can launch. The
installer never loads it or changes Ubuntu's global namespace restrictions.

`packaging/native/policy_setup.py prepare` uses the actual installed manifest
SHA-256 and a fresh output directory to render/check the exact policy without
loading it. Review the generated bytes/profile/digest. A later `load --owner-host`
requires the matching reviewed manifest/policy hashes, another fresh output and
explicit administrator approval. Do not reuse accepted N2/N3/N4 test roots or
policy hashes for another installation. For a normal default installation, run
the following blocks from the reviewed source directory in a normal GNOME
Terminal. Stop if any block fails. These commands are for first installation;
publication does not require reloading the already accepted owner's policy.

Identify the program root and exact installed manifest, then prepare the policy
without loading it:

```bash
CYRNAVA_PROGRAM_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/cyrnava-application"
CYRNAVA_MANIFEST_SHA256="$(/usr/bin/python3.14 -B -I - "$CYRNAVA_PROGRAM_ROOT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
name = json.loads((root / 'current.json').read_text())['release']
if not isinstance(name, str) or name in {'', '.', '..'} or '/' in name or '\\' in name:
    raise SystemExit('Invalid installed release name; stop')
print(hashlib.sha256((root / 'releases' / name / 'manifest.json').read_bytes()).hexdigest())
PY
)"
CYRNAVA_POLICY_REVIEW="$(mktemp -d /tmp/cyrnava-policy.XXXXXXXX)"
/usr/bin/python3.14 -B -I packaging/native/policy_setup.py prepare \
  --root "$CYRNAVA_PROGRAM_ROOT" --manifest-sha256 "$CYRNAVA_MANIFEST_SHA256" \
  --output "$CYRNAVA_POLICY_REVIEW/prepare"
```

Expected: `status: PREPARED`, `parser: PASS`, `host_policy: NOT MODIFIED`.
The temporary parent is private; its `prepare` and `load` children must be fresh.
If a different program root was deliberately selected, use that actual root.

Read the generated result and policy. The following prints the prepared file
path and opens that exact policy for review (`q` exits the viewer):

```bash
cat "$CYRNAVA_POLICY_REVIEW/prepare/result.json"
CYRNAVA_POLICY_NAME="$(/usr/bin/python3.14 -B -I - "$CYRNAVA_POLICY_REVIEW/prepare/result.json" <<'PY'
import json
import sys
from pathlib import Path
record = json.loads(Path(sys.argv[1]).read_text())
assert record['status'] == 'PREPARED' and record['parser'] == 'PASS'
print(record['profile'])
PY
)"
printf '%s\n' "$CYRNAVA_POLICY_REVIEW/prepare/$CYRNAVA_POLICY_NAME"
less "$CYRNAVA_POLICY_REVIEW/prepare/$CYRNAVA_POLICY_NAME"
```

Check that the profile and program root match this installation and that the
policy grants the reviewed application-specific permissions. Only after that
review, paste the `policy_sha256` you reviewed when prompted below. Loading the
exact policy is a separate privileged action and may request your Ubuntu
password. It does not change global namespace restrictions:

```bash
read -r -p 'Reviewed policy_sha256: ' CYRNAVA_POLICY_SHA256
/usr/bin/python3.14 -B -I packaging/native/policy_setup.py load --owner-host \
  --root "$CYRNAVA_PROGRAM_ROOT" --manifest-sha256 "$CYRNAVA_MANIFEST_SHA256" \
  --policy-sha256 "$CYRNAVA_POLICY_SHA256" --output "$CYRNAVA_POLICY_REVIEW/load"
```

Expected: `status: PASS`, `host_policy: LOAD`, and the same kernel profile in
`enforce` mode. Keep any `operation.private.log` private if a step fails; do not
disable renderer sandboxing or weaken host policy as a workaround.

After the required policy is confirmed, open **CyrNava** in GNOME Applications.
Renderer sandboxing, authenticated local backend, private data and ordinary-user
access remain the established design. No sandbox-disable flags or blanket host
permission changes are supported.

### Manual source updates, recovery and uninstall

Download/review the newer immutable source version. Save uploads/notes and close
all CyrNava GUI/backend processes, then from the newer source directory:

```bash
bash update.sh --check-prerequisites
bash update.sh
```

The updater prepares the new source, frontend and pinned environment separately,
then uses the accepted N3 stopped-client audit/checkpoint/journal/activation engine.
It refuses active locks, changed installed code/providers, incompatible schema or
consumer inputs, trust-mode transitions, changed same-version updates and
insufficient space. The current source-update boundary keeps application,
frontend, dependency and bootstrap source contracts identical; arbitrary new
application/schema/Qt versions require reviewed compatibility support.
Different locally generated frontend output bytes are accepted only within that
unchanged input contract. No automatic update service is installed.

An offline signed-archive installation is not silently switched to source trust.
Use its retained installer or a separately reviewed transition. Same-version
reinstallation is explicit and must retain exact artifact identity; it is not an
integrity-repair bypass.

For interruption, preserve private logs and use the shared engine's explicit
`bash ./install_cyrnava.sh recover --root ABSOLUTE-ROOT` after review. Existing
`bash ./uninstall_cyrnava.sh --root ABSOLUTE-ROOT` removes managed activation only;
data, checkpoints and version payloads remain. Explicit retained reinstall uses
`bash ./install_cyrnava.sh reinstall --root ABSOLUTE-ROOT --reuse-preserved-data`.
Rollback is an explicit compatible-code operation, not database rollback.

Use [Backup and recovery](../BACKUP_RESTORE.md) for portable copies. Imports create
new workspaces and intentionally exclude browser appearance/drafts. Normal updates
and reinstall preserve the selected workspace, origin and existing Qt profile.
The app works offline after dependencies and installation are complete.

## Historical offline signed-package guide

The retained guide below describes the tested offline exported kit, not the
current repository-root `install.sh` / `update.sh`. Its signatures, wheelhouse
and source-delivery requirements do not become extra source-first release gates.

Release preparation, 3 November 2026. No public native release is published yet.
These instructions describe the signed **release** kit, not the unsigned development
candidates. Do not install a candidate into your normal profile.

## Supported configuration and prerequisites

Ubuntu 26.04 LTS x86_64, GNOME Wayland, system `/usr/bin/python3.14` with venv support.
Qt/PySide/Shiboken/WebEngine 6.11.3 and Python application dependencies are carried
as exact hash-locked wheels; installation uses `--no-index`, never startup upgrades.
The recipient needs Python/venv, GnuPG, AppArmor/parser, desktop-file-utils and the
normal Ubuntu Wayland/X11 compatibility, font, EGL/OpenGL, NSS/NSPR and sound libraries.
The provider audit refuses missing native libraries before activation. Node, Git,
a compiler, Flatpak, an SDK and an external browser are not recipient requirements.
Use GNOME Terminal outside a confined editor for the separately reviewed policy step.

Internet is needed to obtain the authenticated release and any missing Ubuntu
packages. Unlike Flatpak there is no runtime remote to add. After prerequisites and
installation, notes, editing, images and backups work offline. The application has
ordinary-user filesystem/network access; local-backend authentication, path/image
checks, private data and Chromium renderer sandboxing remain mandatory.

Capacity checks include expanded payload, private environment, previous release and
a complete stopped-profile checkpoint. Do not delete backups to force an install.

## Authenticate before executing downloaded code

Obtain the maintainer's full primary signing fingerprint through an independently
trusted channel. A key bundled beside a download is not, by itself, trusted.
The publication set must include package ZIP, manifest and detached signature,
installer ZIP, `SHA256SUMS` and its detached signature, public key, source ZIP,
dependency notices and the matching covered-source delivery materials.

In a fresh verification GnuPG home, inspect/import the public key, compare its full
primary fingerprint, verify `SHA256SUMS.asc` over `SHA256SUMS`, then run
`sha256sum --check SHA256SUMS` in that download directory. Extract the now-authenticated
installer kit. Do not execute its shell/Python code before this verification.
The exact signing fingerprint/asset URLs are deliberately absent until owner approval;
there is no working public download or release signature to claim yet.

## Install a signed release

The following is a parameterized release-kit example, not today's candidate command:

```bash
app_root="${XDG_DATA_HOME:-$HOME/.local/share}/cyrnava-application"
sh install.sh install --archive CyrNava-0.1.0-ubuntu-x86_64.zip \
  --manifest manifest.json --signature manifest.json.asc \
  --key maintainer-public.asc --fingerprint FULL_APPROVED_PRIMARY_FINGERPRINT \
  --root "$app_root"
```

Installation is per-user and never calls sudo. It verifies signature/hash/platform,
extracts strictly, installs the offline locked dependency closure in its final version
directory, checks providers/ELF/backend, and creates the normal CyrNava desktop entry.
It refuses existing data on first install rather than silently adopting it.

Before first launch on a new installation root, `policy_setup.py prepare` generates
the exact application attachment for review. Its explicit `load --owner-host` step
requires the reviewed manifest and policy hashes and separate owner approval. Only
that profile is added; global namespace restrictions and other profiles stay intact.
No broad Python allowance, automatic root operation or sandbox-disable flag is used.
The exact root/manifest/policy command must be issued for the actual signed package;
the old disposable N2/N3 commands do not apply to a normal installation.

Then open **CyrNava** in GNOME Applications. The release window/menu name is CyrNava;
development candidates intentionally use a distinct identity/profile. Never point
the development launcher at normal data. Close normally after Saved/uploads finish.

## Manual updates and reinstall

Download and independently authenticate the new full release set first. Save and
close all CyrNava GUI/backend processes, then run the authenticated new kit:

```bash
sh update.sh --archive NEW_RELEASE.zip --manifest manifest.json \
  --signature manifest.json.asc --key maintainer-public.asc \
  --fingerprint SAME_TRUSTED_PRIMARY_FINGERPRINT --root "$app_root"
```

The initial supported boundary is schema 5 and identical application/storage/browser
consumers and dependency family. Changed schema/Qt/application consumers require an
explicitly reviewed compatibility extension; do not bypass a refusal. Updates retain
old binaries, whole-profile checkpoints, selected workspace, origin and Qt storage.
Same-artifact repair requires the explicit `--reinstall` update option. After a
data-preserving uninstall, use `sh install.sh reinstall --root "$app_root"
--reuse-preserved-data` deliberately; it refuses changed preserved data/code.

An interrupted transaction blocks launch. Preserve its output and use the verified
engine's `recover --root "$app_root"` after review. Recovery refuses changed targets
or data. Binary rollback is explicit and only permitted with identical data/Qt
consumers; it is not database rollback and cannot repair incompatible browser data.
Use the application's verified portable backup/recovery instead of guessing at DB files.

## Backup and removal

Use **Backup and recovery** to export a portable backup, verify it and retain a copy
outside the installation. Import creates a new workspace and retains the old one.
Notes/folders/images move; browser appearance preferences and drafts are excluded.
An imported workspace starts with its own appearance state; a normal reinstall
must preserve the preference then selected there. See [backup guide](../BACKUP_RESTORE.md).

`sh uninstall.sh --root "$app_root"` removes only managed activation/menu files.
Data, backups, checkpoints, all version payloads and the exact host policy remain.
This is intentional recovery preservation, not disk reclamation. Any later removal
of data or host policy is a separate exact-path decision. No purge is supplied.

## Maintainer trust and maintenance

Use one owner-controlled release key, protect its private material with a strong
passphrase/offline backup, keep an offline revocation certificate, and test restoration.
Publish the primary fingerprint independently. Key replacement requires explicit
authenticated transition/revocation communication; an update must not substitute
a new key automatically. No key or signing operation is created by N4 tooling.
Ship tested full-package security updates for bundled Qt/Chromium/Python/frontend
dependencies. Ubuntu updates host libraries/interpreter, not private bundled wheels.
No automatic updater, public server or cloud account is required.
