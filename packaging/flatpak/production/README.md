# Local production Flatpak — P4

This builds **io.github._74Cerillion.CyrNava**, branch **stable**, from the existing
0.1.0 application/schema 5. It does not publish, sign, install automatically,
configure a public remote, or change the development application. `local-A` and
`local-B` distinguish test builds; they are not new public versions.

## Build requirements

Linux x86_64; Flatpak/OSTree, flatpak-builder (optional manifest route), Bubblewrap
with working user namespaces, desktop-file-validate and appstreamcli; Python/pip
for assembly, Node 24 and npm 11.6.2 for the frontend. End users require none of
these build tools. Core runtime references must already be installed in the user
installation at **exact commits in toolchain.lock.json**. No automatic runtime
updates/downgrades occur. Obtain those refs from a trusted runtime supplier in an
isolated build account if needed; no particular application-distribution service
is required. Runtime extension/graphics availability is a separate host condition.

The regular Ubuntu desktop terminal can run the icon validator and native tests.
The Codex environment cannot create its required namespaces. Never use a sandbox
disabling flag or change host security policy to bypass this.

From the repository root:

```bash
backend/.venv/bin/python packaging/flatpak/production/build.py --build-id local-A
```

The existing venv is a developer convenience; any compatible Python with pip can
run this script. No venv is packaged. npm ci uses the checked-in package lock and
ignores installation scripts; Vite/TypeScript then produce local frontend assets.
Python wheels are binary-only CPython 3.13/Linux x86_64 with required SHA-256
hashes. No sdist setup code or target binary executes during cross-assembly.
Flatpak build-init copies the pinned PySide BaseApp, then install/finish/export/
bundle run with validators enabled. This is a data-assembly build, not a sandbox
verification. Final execution security must be checked inside the real Flatpak.

Each build prints a private build directory. It contains:

- `result.json`: PASS only after export and bundle creation.
- `io.github._74Cerillion.CyrNava.flatpak`: the unsigned local artifact.
- `build-inputs.json`: commits, package hashes, source hashes and tool versions.
- `package-inventory.json`: every payload file/hash and every symlink target.
- `build/metadata`: the effective assembled sandbox metadata.
- A **private local** OSTree `repo/`, not a published repository.

The fixed JSON manifest in this directory describes the same staged application,
wheels and installer for flatpak-builder users. Sources are relative to a staged
build directory, not this checkout. `build.py` is the canonical tested preparation
and assembly procedure. The alternate flatpak-builder route is NOT TESTED in
Codex and must reapply the pinned-ref checks before/after use.

If export failed solely on this session's namespace restriction, do not rebuild
unchanged inputs. From a regular Ubuntu terminal:

```bash
backend/.venv/bin/python packaging/flatpak/production/build.py --finish /absolute/path/to/printed/build-directory
```

Finish repeats the content audit, refuses post-audit payload changes, checks
pinned refs, reruns desktop/AppStream validation, then exports/bundles normally.
Previous result records are preserved. A filename alone is not successful build
evidence; require final `status: PASS` and its SHA-256.

## Install and run locally

After successful build, use the exact artifact path from result.json:

```bash
flatpak install --user --noninteractive /absolute/path/to/io.github._74Cerillion.CyrNava.flatpak
flatpak run --branch=stable io.github._74Cerillion.CyrNava
```

The launcher appears as **CyrNava**. If a shell lacks Flatpak export paths in
XDG_DATA_DIRS, log out/in to refresh the desktop session. Do not add filesystem or
network overrides. This package supports Wayland; X11 support is not claimed.
The first launch offers explicit backup import or an empty workspace.

## Update, compatible rollback and reinstall

For an explicit, reviewed local artifact on the same identity/branch:

```bash
flatpak install --user --reinstall --noninteractive /absolute/path/to/reviewed.flatpak
```

This replaces binaries, not application-private data. A/B tests must use separate
build IDs. App version stays 0.1.0 because no new public release is declared.
Future versioning should use one reviewed SemVer source for application metadata,
frontend, backend and release tags; implementing a release pipeline is P5.

Binary rollback is not database rollback. Databases newer than schema 5 are
refused; there are no reverse migrations. Restore/select a P3 verified compatible
workspace using `--manage-data`, which remains accessible without starting the
backend. Backups omit browser preferences/drafts as documented in P3; an explicit
backup import creates a new generation and can reset its browser preferences.

## Uninstall safely

```bash
flatpak uninstall --user io.github._74Cerillion.CyrNava//stable
```

Do **not** add `--delete-data`. Normal removal preserves
`~/.var/app/io.github._74Cerillion.CyrNava/`. This guide supplies no data-deletion
command. Backup/recovery material and development data are not cleaned by builds
or uninstall. Reinstallation can reuse preserved compatible production data.

## Licensing and scope

Only new AppStream metadata is CC0-1.0, explicitly approved by the owner on
30 October 2026. Original code licensing remains pending (LicenseRef-proprietary);
no new code/logo rights or commercial license are invented. Existing upstream
licenses/notices remain in the package. Public redistribution clearance, including
previously documented attribution provenance, remains outside this local test.
No Flathub submission, signing, public repository or P5/P6 work is included.

## P4 closeout

P4 was closed on 30 October 2026 by explicit owner acceptance. Direct backup/import
PASS is owner-attested; recorded machine checks and outstanding verification
limits are separated in `desktop/native/P4_REPORT.md` and
`desktop/native/evidence/p4/closeout-2026-10-30/owner-acceptance.json`.
The A/B artifacts predate the chooser source correction; enter the full
`.cyrnava` filename when using those builds. Closure does not authorize a release,
publication, real-data migration, or P5/P6.
