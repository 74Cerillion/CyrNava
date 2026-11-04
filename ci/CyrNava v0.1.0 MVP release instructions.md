# CyrNava v0.1.0 MVP release instructions

Prepared for 74Cerillion on 3 November 2026; release preparation completed locally on 4 November 2026. **The approved version is v0.1.0.**
The earlier reference to v1.0.0 was a typo; do not rename the application to 1.0.0.

This is an owner-operated publication guide. Creating this document did not
commit, push, merge, tag, run CI or publish anything. The commands below perform
those actions only when you deliberately execute them. Read each section before
running its commands, use one section at a time, and stop on any unexpected
result. Do not paste this whole document into a terminal.

## Resume here — 4 November 2026

Local release wording, the normal-install AppArmor instructions, the final
installer ID `0.1.0`, and their source-integrity entries are prepared. No commit,
push, merge, tag or publication has been performed for this batch. The next
owner action is **section 4: review, commit and push the exact eight-file batch**.
Sections 1 and 3 are read-only checks of this prepared state. Section 2 records
what was prepared; do not repeat the old documentation/version edits.

## Starting point

- Repository: <https://github.com/74Cerillion/CyrNava> (already public).
- Integration branch: `desktop/p2-production-integration`.
- Last verified commit: `383970f4af683aad154eb1bccaafdd5a932d8b76`.
- Accepted hosted run: [41648248846](https://github.com/74Cerillion/CyrNava/actions/runs/41648248846).
- N1–N4: owner-accepted. The public GitHub Release has not been published.
- Distribution: versioned source, `bash install.sh`, official pinned dependency
  downloads, and local frontend compilation. Application use is offline after
  installation. The original code is MIT, Copyright (c) 2026 74Cerillion.
- Target: Ubuntu 26.04 x86_64, GNOME Wayland, system Python 3.14 and the verified
  Qt/PySide/Shiboken/WebEngine 6.11.3 family. Node 24/npm 11 are install/build tools.

You need the owner's GitHub account with repository write access, the existing
Ubuntu terminal, Git, Python 3.14, and a browser. The final download check uses
curl. This route does not require installing GitHub CLI or creating signing keys.

There are three deliberate external-action points: pushing the final preparation
commit, merging the PR into `main`, and pushing the tag/publishing the Release.
Their instructions below are not permission for an assistant to execute them.

## 1. Open the right repository and check the starting state

Open **Terminal** on Ubuntu. Run:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
git branch --show-current
git rev-parse HEAD
git status --short
git diff --cached --name-only
git remote -v
```

Expected: the integration branch and commit above, an empty staging area, and
origin `https://github.com/74Cerillion/CyrNava.git`. The local changes must be
exactly the eight prepared paths listed in section 4, with nothing staged.
Preserve them. If another path is modified/staged, or HEAD differs, stop for
reconciliation; do not reset, stash, clean or overwrite work to make a check pass.

Refresh remote references; this does not merge or change your working files:

```bash
git fetch origin --tags
git rev-parse origin/desktop/p2-production-integration
git tag --list v0.1.0
git ls-remote --tags origin refs/tags/v0.1.0 'refs/tags/v0.1.0^{}'
```

The remote integration commit should still match the starting commit. The two
tag commands should print nothing. If the tag already exists, stop and inspect
it; never replace or force-push a release tag.

## 2. Review the release materials already prepared

In VS Code, choose **File → Open Folder**, select the CyrNava directory above,
and click **Open**. Use **Ctrl+P**, type a path below and press **Enter** to inspect
it. The following changes are already saved; review rather than redo them.

| Prepared file | Result |
| --- | --- |
| `README.md` | v0.1.0 MVP, N1–N4 accepted, native source-first entry points and installation link; stale current license/acceptance statements removed. |
| `docs/native-installation.md` | Reviewed source-first route, actual accepted CI identity, prerequisites, normal-install AppArmor prepare/review/load commands and unchanged maintenance restrictions. |
| `docs/native-release-notes-v0.1.0.md` | Active source-first scope and accepted evidence; historical offline findings preserved. |
| `docs/native-source-obligations.md` | Corrected current acceptance and already completed trace review wording; notices and historical binary-distribution findings preserved. |
| `CHANGELOG.md` | Current 0.1.0 entry; older candidate entries explicitly historical. |
| `packaging/native/source-release.json` | Preserved the local final installer ID 0.1.0; updated only the four intended consumed documentation hashes. |
| `ci/N4_REPORT.md` | Accepted hosted result, owner acceptance and local release-preparation checkpoint. |
| `ci/CyrNava v0.1.0 MVP release instructions.md` | This current handoff and publication procedure. |

Application/installer/updater code, dependencies, locks, notices, LICENSE,
AppArmor implementation, renderer isolation and accepted artifacts remain
unchanged. The application/frontend version was already 0.1.0. No new build or
GUI test was performed during this local documentation preparation.

## 3. Verify the prepared source inventory — read-only

Run from the repository root:

```bash
/usr/bin/python3.14 -B -I - <<'PYTHON'
import importlib.util
from pathlib import Path
root = Path.cwd()
spec = importlib.util.spec_from_file_location(
    'release_source_check', root / 'packaging/native/source_install.py'
)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
metadata, files = source.verified_source(root)
assert metadata['release_version'] == '0.1.0'
print('Source integrity: PASS')
print('Declared hashes:', len(metadata['source_files']))
print('Release:', metadata['release_version'])
PYTHON
```

Expected: PASS, 166 declared hashes and release 0.1.0. This does not install,
download, compile, launch or change anything. If verification fails, stop; do not
refresh the inventory to accept an unexpected change. The preparation is done,
so there is no inventory-writing command to repeat.

## 4. Review, commit and push the exact preparation batch

Run this check before staging. It allows only the eight preparation files and
requires the staging area to be empty:

```bash
/usr/bin/python3.14 -B -I - <<'PY'
import subprocess
expected = {
    'README.md', 'CHANGELOG.md',
    'docs/native-installation.md',
    'docs/native-release-notes-v0.1.0.md',
    'docs/native-source-obligations.md',
    'packaging/native/source-release.json',
    'ci/N4_REPORT.md',
    'ci/CyrNava v0.1.0 MVP release instructions.md',
}
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'])
records = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z']).split(b'\0')
records = [entry for entry in records if entry]
assert all(entry[:2] in (b' M', b'??') for entry in records), 'Unexpected change type'
actual = {entry[3:].decode() for entry in records}
assert actual == expected, 'Changed-file set differs: ' + repr(sorted(actual ^ expected))
print('Preparation paths: PASS (exactly eight)')
PY
git diff --check
git diff --stat
git diff -- README.md CHANGELOG.md docs/native-installation.md docs/native-release-notes-v0.1.0.md docs/native-source-obligations.md packaging/native/source-release.json ci/N4_REPORT.md
```

Read the diff. Open this guide in the editor to review the untracked file too.
No environments, wheelhouses, generated installations, private logs, credentials,
user notes or backups belong in this batch. Previously approved tracked
historical evidence stays in place; this is not a cleanup exercise.

Stage only these paths:

```bash
git add -- README.md CHANGELOG.md docs/native-installation.md docs/native-release-notes-v0.1.0.md docs/native-source-obligations.md packaging/native/source-release.json ci/N4_REPORT.md 'ci/CyrNava v0.1.0 MVP release instructions.md'
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
```

The staged list must contain exactly the same eight paths. If it differs, stop
before committing. When the reviewed list is correct:

```bash
git -c commit.gpgsign=false commit -m 'chore(release): prepare CyrNava v0.1.0 source release'
git status --short
CYRNAVA_PREP_SHA="$(git rev-parse HEAD)"
printf '%s\n' "$CYRNAVA_PREP_SHA"
```

Expected: a clean working tree. Keep this terminal open; later commands reuse its
variables. The commit is not represented as cryptographically signed.

**External action — push the reviewed preparation commit:**

```bash
git push origin HEAD:refs/heads/desktop/p2-production-integration
git ls-remote --heads origin refs/heads/desktop/p2-production-integration
```

The remote SHA must equal `CYRNAVA_PREP_SHA`. If the push fails, stop. Do not
force-push, rebase, automatically retry, or create another corrective commit.

## 5. Check the new integration CI run

1. Open <https://github.com/74Cerillion/CyrNava/actions> and sign in if needed.
2. Choose **CyrNava CI**. Open the new push run for the integration branch and
   preparation commit from section 4. Do not use the older accepted run as a
   substitute for this new source identity.
3. Wait until the run finishes. Confirm green results for all five jobs:
   **Workflow validation**, **Backend and security**, **Frontend and browser**,
   **Native Ubuntu source installation and update**, and **CI required**.
4. Open the native job, then its **Verify clean no-Git source installation and
   data-preserving online update** step. Inspect the final JSON record.
5. Require final `status: PASS` and the correct `source_commit`. Under `steps`,
   require both online operations to have status PASS. In the
   `online-source-update` entry, require `profile_bytes_unchanged: true` and
   `old_release_retained: true`.
6. With final installer ID 0.1.0, the current driver should exercise the distinct
   synthetic fixture **0.1.0 → 0.1.1**. That fixture does not publish v0.1.1 and
   does not widen compatibility. Same-artifact reinstall is not a substitute.
7. If desired, use the run's **Artifacts** area to inspect the safe
   `source-install-diagnostics-…` ZIP: `result.json` and `source-snapshot.json`.

Some negative tests intentionally display refused/BLOCKED observations. Judge
the completed job conclusions and final installation/update result, rather than
searching the whole test log for one word. CI does not perform a native GUI
rehearsal; the unchanged application's accepted owner-host evidence is retained.

If any required job or operation fails, keep that run and diagnostic, stop and
review its exact failure. Do not bypass a check or keep retrying.

## 6. Create and review the pull request into main

[GitHub's PR instructions](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request)
describe the controls used here.

1. Open <https://github.com/74Cerillion/CyrNava/pulls>.
2. Click **New pull request**. Select **base: main** and
   **compare: desktop/p2-production-integration**.
3. Inspect the comparison. If GitHub reports conflicts, stop for review instead
   of resolving them by deleting work or changing the tested implementation.
4. Click **Create pull request**. Use the title
   **Release CyrNava v0.1.0 — source-first native desktop**.
5. In the description, state N1–N4 are accepted, link the preparation CI run,
   and describe the supported Ubuntu source-first installation, verified
   distinct-version compatible update and unchanged data. This is a release
   integration, not a new application feature.
6. Submit with **Create pull request**. In **Files changed**, review the intended
   implementation plus final preparation changes. The full PR includes earlier
   accepted commits; the eight-file restriction applies to the last preparation
   commit, not the entire integration history.
7. Wait for the PR's required checks to pass. Satisfy any existing review rules;
   do not turn off branch protections or override failed checks.

**External action — merge the approved PR:**

8. Open the PR's **Conversation** page. At the merge control, choose
   **Create a merge commit** if a dropdown is shown, then **Merge pull request**
   and **Confirm merge**. Preserve the accepted commits rather than squashing or
   rebasing this history. If that merge method is unavailable, stop for review.
9. Keep the integration branch; do not select a branch-deletion action.

The merge controls and repository-rule behavior are documented in
[GitHub's merge guide](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request).

## 7. Pin and verify the final main commit

Return to the same terminal. Run:

```bash
git status --short
git fetch origin --tags
git switch main
git pull --ff-only origin main
CYRNAVA_RELEASE_SHA="$(git rev-parse HEAD)"
printf '%s\n' "$CYRNAVA_RELEASE_SHA"
git merge-base --is-ancestor "$CYRNAVA_PREP_SHA" "$CYRNAVA_RELEASE_SHA"
git ls-remote --heads origin refs/heads/main
```

Start with a clean working tree. The ancestry check should succeed silently;
the remote main SHA must equal `CYRNAVA_RELEASE_SHA`. If fast-forward or ancestry
checks fail, stop; do not reset or rewrite history. If you changed terminals,
restore `CYRNAVA_PREP_SHA` from the exact preparation commit recorded in section
4 before continuing; never guess it.

In GitHub **Actions → CyrNava CI**, open the ordinary **main push** run for this
exact `CYRNAVA_RELEASE_SHA`. Wait for all five jobs and the native final JSON
checks from section 5 to pass. The PR run alone is not evidence for a different
main merge commit. Reuse the read-only verifier in section 3 to confirm final
source integrity and installer release ID 0.1.0 locally.

If main advances after you record this SHA, keep the tag pinned to the exact
approved successful commit; do not silently substitute a newer commit.

## 8. Create and push the exact release tag

Only continue once the exact main commit above has passed CI and is approved for
release. Check that no local or remote v0.1.0 tag appeared meanwhile:

```bash
git tag --list v0.1.0
git ls-remote --tags origin refs/tags/v0.1.0 'refs/tags/v0.1.0^{}'
```

Both should print nothing. Then create the annotated tag at the recorded commit:

```bash
git -c tag.gpgsign=false tag -a v0.1.0 "$CYRNAVA_RELEASE_SHA" -m 'CyrNava v0.1.0 MVP'
git rev-parse 'v0.1.0^{commit}'
```

The printed commit must equal `CYRNAVA_RELEASE_SHA`. This is an **unsigned**
annotated tag. Do not claim a verified production signature or create new keys
as part of these instructions.

**External action — publish the tag:**

```bash
git push origin refs/tags/v0.1.0
git ls-remote --tags origin refs/tags/v0.1.0 'refs/tags/v0.1.0^{}'
```

The `^{}` line is the peeled commit and must match the approved release SHA.
Do not use `--force` or `--tags`; push only this tag. The repository's current CI
workflow runs on branch pushes/PRs; tag creation is not a replacement CI run.

## 9. Draft the GitHub Release

These controls follow [GitHub's release guide](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

1. Open <https://github.com/74Cerillion/CyrNava/releases> and choose
   **Draft a new release**. An empty Releases page may offer **Create a new
   release** instead.
2. Open **Choose a tag** and select the existing **v0.1.0** tag. Do not create a
   second tag from a moving branch. Check the displayed commit against section 8.
3. Enter **CyrNava v0.1.0 — MVP** as the release title.
4. Paste the following starting description, then preview and review it:

```markdown
## CyrNava v0.1.0

A native, local-first knowledge workspace for folders, rich-text notes and images.

Supported target: Ubuntu 26.04 x86_64 / GNOME Wayland, system Python 3.14,
and the pinned Qt/PySide/WebEngine 6.11.3 stack. Installation/build uses
Node 24 and npm 11. Initial dependency acquisition needs internet access;
normal application operation is offline afterward.

### Install

Download **Source code (zip)** below and extract it, or check out tag **v0.1.0**.
Read the [installation guide](https://github.com/74Cerillion/CyrNava/blob/v0.1.0/docs/native-installation.md)
for Ubuntu prerequisites. From the source directory, run:

    bash install.sh --check-prerequisites
    bash install.sh

Before first desktop launch, follow that guide to review and explicitly load
the exact installation-specific AppArmor policy. The installer does not do
that privileged step automatically. Then open CyrNava from GNOME Applications.

### Data and manual updates

Save notes/uploads, close CyrNava and retain a verified backup before maintenance.
Run `bash update.sh` from a reviewed newer compatible source release.
The current update contract preserves existing workspace/profile data and
requires compatible application, schema and dependency inputs.

[Backup and recovery](https://github.com/74Cerillion/CyrNava/blob/v0.1.0/BACKUP_RESTORE.md)
· [Third-party notices](https://github.com/74Cerillion/CyrNava/blob/v0.1.0/docs/native-third-party-notices.txt)
· [Source/dependency scope](https://github.com/74Cerillion/CyrNava/blob/v0.1.0/docs/native-source-obligations.md)

Original code: MIT, Copyright (c) 2026 74Cerillion.
```

5. Keep the custom asset-upload area empty. GitHub supplies source ZIP/tar.gz
   downloads for the tag. Do not attach local installations, wheelhouses, private
   logs, signing material, personal data or the historical offline package.
6. For this approved MVP release, leave **This is a pre-release** unchecked.
   Select **Set as latest release** if that option is shown.
7. Click **Save draft**. Review the rendered notes, version, commit, download
   scope, prerequisite/AppArmor instructions, license and documentation links.
   Saving a draft is not the final public release announcement.

## 10. Publish, then check the public download

**Publication action:** after approving the saved draft, open it from Releases,
edit it if needed, and click **Publish release**. Do not proceed if you are still
unsure about the selected commit or release notes.

1. Open <https://github.com/74Cerillion/CyrNava/releases/tag/v0.1.0> in a private
   browser window, signed out. Confirm the public title, notes, tag and source
   download links are visible and correct.
2. Under **Assets**, confirm **Source code (zip)** and **Source code (tar.gz)**
   are offered. The ZIP is source, not an already installed executable.
3. Return to the terminal used above and download the ZIP into a fresh temporary
   directory. This check does not install or launch CyrNava:

```bash
CYRNAVA_DOWNLOAD="$(mktemp -d /tmp/cyrnava-public-download.XXXXXX)"
curl --fail --location --proto '=https' --proto-redir '=https' --max-time 180 \
  https://github.com/74Cerillion/CyrNava/archive/refs/tags/v0.1.0.zip \
  --output "$CYRNAVA_DOWNLOAD/CyrNava-v0.1.0-source.zip"
sha256sum "$CYRNAVA_DOWNLOAD/CyrNava-v0.1.0-source.zip"
```

4. Verify every archived tracked file against the exact release commit. This
   reads the ZIP without extracting or executing its contents:

```bash
/usr/bin/python3.14 -B -I - "$CYRNAVA_DOWNLOAD/CyrNava-v0.1.0-source.zip" "$CYRNAVA_RELEASE_SHA" <<'PY'
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

archive_path, commit = Path(sys.argv[1]), sys.argv[2]
assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit)
tag_commit = subprocess.check_output(
    ['git', 'rev-parse', 'v0.1.0^{commit}'], text=True
).strip()
assert tag_commit == commit, 'Local tag differs from approved release commit'
records = subprocess.check_output(['git', 'ls-tree', '-rz', commit]).split(b'\0')
expected = {}
for record in filter(None, records):
    fields, name = record.split(b'\t', 1)
    mode, kind, oid = fields.split()
    assert kind == b'blob', 'Unexpected submodule/tree entry; review required'
    expected[name.decode()] = oid.decode()
with zipfile.ZipFile(archive_path) as archive:
    members = [item for item in archive.infolist() if not item.is_dir()]
    names = [PurePosixPath(item.filename) for item in members]
    assert all(not name.is_absolute() and '..' not in name.parts for name in names)
    roots = {name.parts[0] for name in names}
    assert len(roots) == 1, 'Unexpected archive layout'
    actual = {'/'.join(name.parts[1:]): item for name, item in zip(names, members)}
    assert len(actual) == len(members), 'Duplicate archive paths'
    assert set(actual) == set(expected), 'Archive file inventory differs from Git'
    for name, oid in expected.items():
        content = subprocess.check_output(['git', 'cat-file', 'blob', oid])
        assert archive.read(actual[name]) == content, 'Archive bytes differ: ' + name
    metadata = json.loads(archive.read(actual['packaging/native/source-release.json']))
    assert metadata['release_version'] == '0.1.0'
    for name, digest in metadata['source_files'].items():
        assert hashlib.sha256(archive.read(actual[name])).hexdigest() == digest, name
with archive_path.open('rb') as stream:
    checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
print('Published source verification: PASS')
print('Release commit:', commit)
print('Tracked files verified:', len(expected))
print('Downloaded ZIP SHA-256:', checksum)
PY
```

Expected: **Published source verification: PASS**. Record the release URL, exact
commit, final main CI URL and downloaded ZIP hash with the release record. A ZIP
checksum identifies the downloaded bytes; it is not a digital signature or an
independent trust anchor. If verification fails, retain the download and report
the discrepancy; do not move the tag or silently replace the release.

Publication is complete when the public release is visible, its source matches
the approved successful commit, and its installation/notices links work. This
guide does not require another application build, dependency download,
installation, GUI rehearsal, AppArmor reload or new infrastructure for that
final publication check. Preserve the accepted application/evidence and stop.
