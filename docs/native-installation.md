# Native Ubuntu installation and manual maintenance

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
