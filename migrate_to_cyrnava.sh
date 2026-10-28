#!/usr/bin/env bash
# Run only after review/commit, Saved, and stopping the app and development tools.
set -euo pipefail
export GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
if [[ $# -eq 0 || ${1:-} == --help ]]; then
  echo 'Usage: migrate_to_cyrnava.sh REPOSITORY [--dry-run] [--data-dir PROFILE] [--backup-dir PARENT]'
  exit 0
fi
[[ $EUID -ne 0 ]] || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }
[[ -d $1 ]] || { echo 'Repository directory does not exist.' >&2; exit 1; }
command -v git >/dev/null || { echo 'Git is required.' >&2; exit 1; }
# Verify the expected owner/project before executing its local Python environment.
origin=$(git -C "$1" config --local --get-all remote.origin.url)
[[ $origin =~ ^(https://github\.com/|git@github\.com:|ssh://git@github\.com/)74Cerillion/(CyrNava|PEngage_Pentest-Engagement-Manager-)(\.git)?/?$ ]] || { echo 'Unrecognized repository origin; stopped.' >&2; exit 1; }
runtime="$1/backend/.venv/bin/python"
[[ -x $runtime ]] || { echo 'Rebuild backend/.venv with Python 3.12 and requirements.txt first.' >&2; exit 1; }
exec "$runtime" - "$@" <<'PY'
import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from uuid import uuid4

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def run(*command, cwd=None):
    return subprocess.check_output(command, cwd=cwd, text=True).strip()

def no_links(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)),
            f'Symbolic-link paths require manual review: {path}')

def outside_repository(path, repository):
    # Match the application's backup boundary. Also keep backup/profile parents
    # from containing the source tree. Choose private paths outside other repos.
    require(not path.is_relative_to(repository) and not repository.is_relative_to(path),
            f'Choose a private location separate from the repository: {path}')

def main():
    parser = argparse.ArgumentParser(description='Offline CyrNava repository migration')
    parser.add_argument('repository', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--data-dir', type=Path, help='Full existing profile, including engage')
    parser.add_argument('--backup-dir', type=Path, default=Path.home() / 'Backups/CyrNava-migration')
    args = parser.parse_args()
    require(sys.platform.startswith('linux') and sys.version_info[:2] == (3, 12), 'Ubuntu/Linux and Python 3.12 required.')
    for tool in ('git', 'tar', 'mv'):
        require(shutil.which(tool), f'Missing command: {tool}')
    source = args.repository.expanduser().absolute()
    no_links(source)
    source = source.resolve(strict=True)
    destination = source.parent / 'CyrNava'
    require(source != Path.home() and source != Path('/'), 'Refusing an unsafe repository root.')
    require((source / '.git').is_dir() and not (source / '.git').is_symlink(), 'A regular standalone .git directory is required; worktrees are not supported.')
    git = lambda *parts: run('git', '-C', str(source), *parts)
    require(Path(git('rev-parse', '--show-toplevel')).resolve() == source, 'Argument must be the repository root.')
    require(Path(git('rev-parse', '--path-format=absolute', '--git-common-dir')).resolve() == source / '.git', 'Shared Git metadata is not supported.')
    require(not (source / '.git/config').is_symlink(), 'Symlink Git configuration requires manual review.')
    branch = git('symbolic-ref', '--short', 'HEAD')
    head = git('rev-parse', 'HEAD')
    status = git('status', '--porcelain=v1', '--untracked-files=all')
    print(f'Original path: {source}\nNew path: {destination}\nBranch: {branch}\nGit status:\n{status or "clean"}', flush=True)
    require(not status, 'Uncommitted/untracked changes found. Review and commit or deliberately stash them first; this script never stages or commits.')
    require(not git('submodule', 'status'), 'Submodules require a separate migration review.')
    for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        require(not (source / '.git' / name).exists(), 'Finish the current Git operation first.')
    original = git('config', '--local', '--get-all', 'remote.origin.url')
    require('\n' not in original and git('remote', 'get-url', 'origin') == original, 'Multiple URLs or URL rewrites require manual review.')
    require(subprocess.run(['git', '-C', str(source), 'config', '--get-all', 'remote.origin.pushurl'], capture_output=True).returncode == 1, 'An explicit push URL requires manual review; authentication will not be changed.')
    match = re.fullmatch(r'(https://github\.com/|git@github\.com:|ssh://git@github\.com/)74Cerillion/(CyrNava|PEngage_Pentest-Engagement-Manager-)(?:\.git)?/?', original)
    require(match, 'Origin is not a recognized 74Cerillion CyrNava/previous-project GitHub URL.')
    updated = match[1] + '74Cerillion/CyrNava.git'
    print(f'Previous origin: {original}\nUpdated origin: {updated}', flush=True)
    package = json.loads((source / 'frontend/package.json').read_text())
    require(package.get('name') == 'cyrnava' and (source / 'desktop/install.py').is_file() and (source / 'backend/app/backup.py').is_file(), 'Rebranded CyrNava source is required. Review/commit the implementation first.')
    if source == destination and original == updated:
        print('Already migrated. Backup: not created. Application data: unchanged. Verification: clean CyrNava checkout and expected origin. No operations performed.')
        return
    require(source == destination or not os.path.lexists(destination), 'CyrNava destination already exists; nothing will be overwritten.')
    for process in Path('/proc').glob('[0-9]*'):
        if int(process.name) == os.getpid():
            continue
        try:
            cwd = (process / 'cwd').resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        require(not cwd.is_relative_to(source), f'Process {process.name} has a working directory inside the repository. Close its terminal/editor/server, then retry from outside the checkout.')
    xdg = os.environ.get('XDG_DATA_HOME', '')
    home = Path(xdg) if os.path.isabs(xdg) else Path.home() / '.local/share'
    config_path = home / 'engage-application/config.json'
    if not args.data_dir and config_path.exists():
        home = Path(json.loads(config_path.read_text())['data_home'])
        require(home.is_absolute(), 'Invalid saved data_home.')
    profile = (args.data_dir or home / 'engage').expanduser().absolute()
    no_links(profile)
    profile = profile.resolve()
    outside_repository(profile, source)
    backup_parent = args.backup_dir.expanduser().absolute()
    no_links(backup_parent)
    backup_parent = backup_parent.resolve()
    outside_repository(backup_parent, source)
    require(not backup_parent.is_relative_to(profile) and not profile.is_relative_to(backup_parent), 'Profile and backup locations must be separate.')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:8]
    backup = backup_parent / stamp
    print(f'Backup location: {backup}\nApplication data: retained in place at {profile}', flush=True)
    sys.path.insert(0, str(source / 'backend'))
    from app.backup import _publish, validate_backup, validate_profile
    with ExitStack() as stack:
        files = None
        if profile.exists():
            database = profile / 'engage.sqlite3'
            require(database.is_file() and not database.is_symlink(), 'Profile exists without a regular engage.sqlite3; manual review required.')
            lock_path = profile / '.engage.lock'
            require(lock_path.is_file() and not lock_path.is_symlink(), 'Existing profile lock required. Run and cleanly stop the current application first.')
            lock = stack.enter_context(lock_path.open('rb'))
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('Application profile is busy. Stop every backend before retrying.') from None
            require(not list(profile.glob('engage.sqlite3-*')), 'SQLite sidecars exist. Stop/recover all writers first; no unsafe copy will be made.')
            with database.open('rb') as stream:
                header = stream.read(100)
            require(header[:16] == b'SQLite format 3\0' and header[18:20] == b'\x01\x01', 'Invalid or WAL-mode SQLite profile. Obtain an offline, checkpointed rollback-journal profile under separate review; this script will not change it.')
            files = validate_profile(profile)
            print('Database integrity, relationships, templates and owned images: verified.', flush=True)
        else:
            print('No existing profile at that location; no data copy/migration required. For custom XDG locations, stop and supply --data-dir before proceeding.', flush=True)
        if args.dry_run:
            print('DRY RUN: would archive Git/source/configuration, back up any profile, rename the checkout without replacement, update origin, and verify HEAD/status. No files changed.')
            return
        # Exclude only rebuildable environments/output; retain .git and ignored configuration.
        excluded = ('./backend/.venv', './frontend/node_modules', './frontend/dist')
        needed = 16 * 1024 * 1024
        for root, directories, names in os.walk(source):
            directories[:] = [n for n in directories if './' + str((Path(root) / n).relative_to(source)) not in excluded]
            needed += sum((Path(root) / n).lstat().st_size for n in names)
        if files:
            needed += sum((profile / name).stat().st_size for name in files)
        ancestor = backup_parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        require(shutil.disk_usage(ancestor).free > needed * 1.2, 'Insufficient free space for verified backups.')
        backup.mkdir(parents=True, mode=0o700)
        archive = backup / 'repository.tar'
        subprocess.run(['tar', '-cpf', str(archive), '-C', str(source), *('--exclude=' + n for n in excluded), '.'], check=True)
        subprocess.run(['tar', '-df', str(archive), '-C', str(source)], check=True)
        with archive.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        (backup / 'repository.tar.sha256').write_text(checksum + '  repository.tar\n')
        if files:
            _publish(profile, backup / 'profile.engage-backup', files, manifest=True)
            require(validate_backup(backup / 'profile.engage-backup') == files, 'Data backup verification failed.')
        record = {'original_path': str(source), 'new_path': str(destination), 'previous_origin': original, 'updated_origin': updated, 'branch': branch, 'head': head, 'profile': str(profile), 'complete': False}
        (backup / 'migration.json').write_text(json.dumps(record, indent=2) + '\n')
        require(not git('status', '--porcelain=v1', '--untracked-files=all'), 'Source changed during backup; stopped before migration.')
        if source != destination:
            subprocess.run(['mv', '-T', '--no-clobber', '--', str(source), str(destination)], check=True)
            require(not source.exists(), 'Rename refused a destination conflict; original checkout remains intact.')
        source = destination
        subprocess.run(['git', '-C', str(source), 'remote', 'set-url', 'origin', updated], check=True)
        require(git('rev-parse', 'HEAD') == head and git('symbolic-ref', '--short', 'HEAD') == branch, 'HEAD/branch verification failed; consult the retained backup.')
        require(git('remote', 'get-url', 'origin') == updated and not git('status', '--porcelain=v1', '--untracked-files=all'), 'Final origin/status verification failed; consult the retained backup.')
        record['complete'] = True
        (backup / 'migration.json').write_text(json.dumps(record, indent=2) + '\n')
        print(f'Verification: HEAD and branch preserved; Git clean; origin updated.\nFinal path: {destination}\nBackup retained: {backup}\nApplication data: unchanged, backed up if present.\nNext: reopen VS Code, rebuild backend/.venv at its new path, then reinstall the desktop app. No push or installation was performed.', flush=True)

try:
    os.umask(0o077)
    main()
except Exception as error:
    print(f'STOPPED: {error}\nNo original application data was deleted. Retain any printed backup; review before retrying.', file=sys.stderr)
    sys.exit(1)
PY
