"""P5B data-only promotion, disposable signing and local publication primitives.

No production key import, application build, installation or network publication.
"""

import base64
import configparser
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
APP_ID = "io.github._74Cerillion.CyrNava"
REF = f"app/{APP_ID}/x86_64/stable"
UID = "CYRNAVA P5B STAGING ONLY <staging@invalid.example>"
BUNDLE = APP_ID + ".flatpak"
MEMBERS = {
    BUNDLE,
    "SHA256SUMS",
    "result.json",
    "build-inputs.json",
    "package-inventory.json",
    "provenance.json",
}
SHA = re.compile(r"[a-f0-9]{64}")
FINGERPRINT = re.compile(r"[A-F0-9]{40}(?:[A-F0-9]{24})?")


class Rejected(ValueError):
    """An authored non-sensitive failure; never contains subprocess output."""


def require(condition, message):
    if not condition:
        raise Rejected(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON member")
        result[key] = value
    return result


def read_json(path):
    safe_path(path)
    require(Path(path).stat().st_size <= 4 * 1024**2, "Metadata exceeds size limit")
    return json.loads(Path(path).read_text(), object_pairs_hook=_pairs)


def safe_path(path):
    path = Path(path).absolute()
    require(".." not in path.parts, "Parent traversal path refused")
    require(
        not any(p.is_symlink() for p in (path, *path.parents)), "Symlink path refused"
    )
    return path


def outside_source(path):
    path = safe_path(path)
    require(
        not path.is_relative_to(ROOT), "Staging output must be outside the source tree"
    )
    return path


def call(*args, timeout=300, env=None):
    try:
        return subprocess.run(
            [str(a) for a in args],
            check=True,
            capture_output=True,
            timeout=timeout,
            env=env,
        ).stdout
    except (OSError, subprocess.SubprocessError) as error:
        # Commands may receive signing paths; never print argv, stderr or environment.
        raise Rejected(
            f"Operation failed: {Path(str(args[0])).name} ({type(error).__name__})"
        ) from None


def p5a():
    spec = importlib.util.spec_from_file_location("p5b_p5a", ROOT / "ci/flatpak.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy():
    value = read_json(HERE / "policy.json")
    require(value["production_enabled"] is False, "Production publication is disabled")
    require(
        sha(ROOT / ".github/workflows/ci.yml") == value["ci_workflow_sha256"],
        "Accepted CI workflow changed; policy review required",
    )
    require(
        sha(ROOT / "packaging/flatpak/production/toolchain.lock.json")
        == value["toolchain_sha256"],
        "Accepted P4 lock changed",
    )
    require(
        all(
            sha(ROOT / name) == digest
            for name, digest in value["auditor_sha256"].items()
        ),
        "Accepted production auditor changed; policy review required",
    )
    return value


def approval(source, version, channel, authorization_ref):
    require(channel == "staging", "Only disposable staging is authorized")
    value = policy()
    require(
        re.fullmatch(r"[a-f0-9]{40}", source) is not None,
        "Full immutable source SHA required",
    )
    require(version == value["version"], "Version change requires owner approval")
    entries = [
        entry
        for entry in value["approved_staging_sources"]
        if entry["source_commit"] == source
    ]
    require(len(entries) == 1, "Source is not approved for staging")
    entry = entries[0]
    require(
        authorization_ref == entry["authorization_ref"], "Missing staging authorization"
    )
    return entry


def ci_eligibility(run, jobs, artifact, workflow_bytes, entry):
    value = policy()
    require(
        run.get("id") == entry["ci_run_id"]
        and run.get("run_attempt") == entry["ci_run_attempt"],
        "Wrong verification run or attempt",
    )
    require(
        run.get("head_sha") == entry["source_commit"]
        and run.get("head_branch") == value["workflow_branch"],
        "Wrong CI source",
    )
    require(
        run.get("event") == "push"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success",
        "Successful push CI required",
    )
    require(
        run.get("workflow_id") == value["ci_workflow_id"]
        and run.get("path") == value["ci_workflow_path"]
        and run.get("repository", {}).get("id") == value["repository_id"],
        "Unexpected CI workflow or repository",
    )
    expected = {
        "Workflow validation",
        "Backend and security",
        "Frontend and browser",
        "Production Flatpak and bundle audit",
        "CI required",
    }
    require(
        len(jobs) == 5
        and {j.get("name") for j in jobs} == expected
        and all(
            j.get("conclusion") == "success" and j.get("status") == "completed"
            for j in jobs
        ),
        "Required CI jobs missing or failed",
    )
    require(
        hashlib.sha256(workflow_bytes).hexdigest() == value["ci_workflow_sha256"],
        "Unreviewed CI workflow content",
    )
    require(
        artifact.get("id") == entry["artifact_id"]
        and not artifact.get("expired", True)
        and artifact.get("digest") == "sha256:" + entry["artifact_zip_sha256"]
        and artifact.get("name")
        == f"CyrNava-linux-x86_64-{entry['source_commit']}-{entry['ci_run_attempt']}",
        "Wrong, expired or unverified CI artifact",
    )
    require(
        artifact.get("workflow_run", {}).get("id") == entry["ci_run_id"]
        and artifact.get("workflow_run", {}).get("head_sha") == entry["source_commit"],
        "Artifact provenance does not match verification",
    )
    return True


def extract_artifact(archive, destination, entry):
    safe_path(archive)
    require(
        Path(archive).stat().st_size < 1024**3
        and sha(archive) == entry["artifact_zip_sha256"],
        "Artifact archive hash/size mismatch",
    )
    destination = safe_path(destination)
    destination.mkdir(mode=0o700)
    with zipfile.ZipFile(archive) as stream:
        items = stream.infolist()
        require(
            len(items) == len(MEMBERS) and {i.filename for i in items} == MEMBERS,
            "Unexpected, duplicate or unsafe archive members",
        )
        require(
            sum(i.file_size for i in items) < 1024**3, "Archive expansion exceeds limit"
        )
        for item in items:
            mode = stat.S_IFMT(item.external_attr >> 16)
            require(
                mode in (0, stat.S_IFREG) and not item.is_dir(), "Unsafe archive object"
            )
            limit = 512 * 1024**2 if item.filename == BUNDLE else 4 * 1024**2
            require(item.file_size <= limit, "Archive member exceeds limit")
            with (
                stream.open(item) as source,
                (destination / item.filename).open("xb") as target,
            ):
                shutil.copyfileobj(source, target)
    return validate_candidate(destination, entry)


def validate_candidate(directory, entry):
    directory = safe_path(directory)
    require(
        {p.name for p in directory.iterdir()} == MEMBERS, "Unexpected candidate content"
    )
    for name in MEMBERS:
        require(safe_path(directory / name).is_file(), "Candidate file missing")
    bundle = directory / BUNDLE
    digest = sha(bundle)
    inputs = read_json(directory / "build-inputs.json")
    inventory = read_json(directory / "package-inventory.json")
    provenance = read_json(directory / "provenance.json")
    result = read_json(directory / "result.json")
    require(
        digest == entry["bundle_sha256"]
        and sha(directory / "build-inputs.json") == entry["inputs_sha256"]
        and sha(directory / "package-inventory.json") == entry["inventory_sha256"],
        "Candidate differs from reviewed artifact",
    )
    require(
        (directory / "SHA256SUMS").read_text() == digest + "  " + BUNDLE + "\n",
        "Checksum list mismatch",
    )
    require(
        all(x.get("app_id") == APP_ID for x in (inputs, provenance, result)),
        "Incorrect application identity",
    )
    lock = read_json(ROOT / "packaging/flatpak/production/toolchain.lock.json")
    require(
        inputs.get("runtime_lock") == provenance.get("runtime") == lock,
        "Runtime locks differ",
    )
    require(
        inputs.get("git_commit")
        == provenance.get("source_commit")
        == entry["source_commit"]
        and inputs.get("version") == provenance.get("version") == policy()["version"],
        "Source/version inconsistency",
    )
    require(
        provenance.get("workflow_run_id") == str(entry["ci_run_id"])
        and provenance.get("workflow_run_attempt") == str(entry["ci_run_attempt"]),
        "Missing CI provenance",
    )
    require(
        provenance.get("status")
        == result.get("status")
        == inventory.get("status")
        == "PASS",
        "Candidate audit/build failed",
    )
    require(
        provenance.get("sha256") == result.get("sha256") == digest
        and provenance.get("artifact_bytes")
        == result.get("bytes")
        == bundle.stat().st_size,
        "Candidate hash/size inconsistency",
    )
    require(
        provenance.get("ostree_commit")
        == result.get("ostree_commit")
        == entry["ostree_commit"],
        "Unexpected exported OSTree commit",
    )
    return {
        "source_commit": entry["source_commit"],
        "bundle_sha256": digest,
        "ci_run_id": entry["ci_run_id"],
        "ci_artifact_id": entry["artifact_id"],
        "ostree_commit": entry["ostree_commit"],
        "version": inputs["version"],
    }


def gpg(home, *args):
    return call(
        "gpg",
        "--no-options",
        "--homedir",
        home,
        "--batch",
        "--no-auto-key-retrieve",
        *args,
    )


def make_key(home):
    home = outside_source(home)
    home.mkdir(mode=0o700)
    gpg(
        home,
        "--pinentry-mode",
        "loopback",
        "--passphrase",
        "",
        "--quick-generate-key",
        UID,
        "rsa2048",
        "sign",
        "1d",
    )
    text = gpg(home, "--with-colons", "--list-keys").decode()
    fingerprint = next(
        line.split(":")[9] for line in text.splitlines() if line.startswith("fpr:")
    )
    (home / ".p5b-staging-only").write_bytes(
        encode({"fingerprint": fingerprint, "uid": UID})
    )
    return fingerprint


def staging_key(home, fingerprint):
    home = outside_source(home)
    require(
        stat.S_IMODE(home.stat().st_mode) == 0o700
        and home.stat().st_uid == os.getuid(),
        "Signing directory must be private and owner-controlled",
    )
    require(
        FINGERPRINT.fullmatch(fingerprint) is not None,
        "Full signing fingerprint required",
    )
    require(
        read_json(home / ".p5b-staging-only")
        == {"fingerprint": fingerprint, "uid": UID},
        "Only marked disposable staging keys are allowed",
    )
    listing = gpg(home, "--with-colons", "--list-secret-keys", fingerprint).decode()
    require(
        UID in listing
        and any(line.startswith("sec:") for line in listing.splitlines()),
        "Missing disposable signing credentials",
    )
    return home


def sign(home, fingerprint, path):
    staging_key(home, fingerprint)
    gpg(
        home,
        "--pinentry-mode",
        "loopback",
        "--passphrase",
        "",
        "--local-user",
        fingerprint,
        "--output",
        str(path) + ".sig",
        "--detach-sign",
        path,
    )


def export_key(home, fingerprint):
    staging_key(home, fingerprint)
    return gpg(home, "--export-options", "export-minimal", "--export", fingerprint)


def verify_signature(public_key, fingerprint, path, signature, parent):
    require(
        FINGERPRINT.fullmatch(fingerprint) is not None,
        "Expected key fingerprint required",
    )
    with tempfile.TemporaryDirectory(prefix="verify-key-", dir=parent) as temporary:
        home = Path(temporary)
        home.chmod(0o700)
        packets = gpg(home, "--list-packets", safe_path(public_key))
        require(
            b":secret key packet:" not in packets
            and b":secret sub key packet:" not in packets,
            "Private signing material supplied as a public trust anchor",
        )
        gpg(home, "--import", safe_path(public_key))
        listing = gpg(home, "--with-colons", "--list-keys").decode().splitlines()
        require(
            sum(line.startswith("pub:") for line in listing) == 1
            and any(
                line.startswith("fpr:") and line.split(":")[9] == fingerprint
                for line in listing
            ),
            "Unexpected public signing identity",
        )
        status = gpg(
            home, "--status-fd", "1", "--verify", safe_path(signature), safe_path(path)
        ).decode()
        require(
            any(
                line.startswith("[GNUPG:] VALIDSIG ")
                and (line.split()[2] == fingerprint or line.split()[-1] == fingerprint)
                for line in status.splitlines()
            ),
            "No valid expected signature",
        )


def descriptors(public, url, public_key):
    parsed = urllib.parse.urlsplit(url)
    require(
        not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment,
        "Credentials/query/fragment forbidden in repository URL",
    )
    require(
        (
            parsed.scheme == "file"
            and parsed.netloc in ("", "localhost")
            and parsed.path.startswith("/")
        )
        or (
            parsed.scheme == "https"
            and parsed.hostname
            and parsed.hostname.endswith(".invalid")
        ),
        "P5B descriptor URLs must be local or reserved staging-only HTTPS",
    )
    require("\n" not in url and "\r" not in url, "Unsafe descriptor URL")
    key = base64.b64encode(public_key).decode()
    for name, section, values in (
        (
            "cyrnava-staging.flatpakrepo",
            "Flatpak Repo",
            {
                "Title": "CyrNava STAGING ONLY",
                "Url": url,
                "DefaultBranch": "stable",
                "GPGKey": key,
            },
        ),
        (
            "cyrnava-staging.flatpakref",
            "Flatpak Ref",
            {
                "Title": "CyrNava STAGING ONLY",
                "Name": APP_ID,
                "Branch": "stable",
                "IsRuntime": "false",
                "Url": url,
                "GPGKey": key,
                "RuntimeRepo": "https://dl.flathub.org/repo/flathub.flatpakrepo",
            },
        ),
    ):
        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str
        config[section] = values
        with (public / name).open("x") as stream:
            config.write(stream)


def tree_manifest(root):
    root = safe_path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Publication symlinks refused")
        if path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        require(
            path.is_file()
            and not {
                "private-keys-v1.d",
                "openpgp-revocs.d",
                ".gnupg",
                "private",
                "candidate",
            }.intersection(path.relative_to(root).parts),
            "Unsafe publication object",
        )
        require(
            path.stat().st_size <= 512 * 1024**2,
            "Publication file exceeds resource bound",
        )
        with path.open("rb") as stream:
            require(
                b"PRIVATE KEY" not in stream.read(4096),
                "Private key marker in public tree",
            )
        if rel not in ("manifest.json", "manifest.json.sig"):
            result[rel] = {"sha256": sha(path), "bytes": path.stat().st_size}
    require(
        len(result) <= 50000
        and sum(v["bytes"] for v in result.values()) <= 4 * 1024**3,
        "Publication tree exceeds resource bound",
    )
    return result


def seal(public, home, fingerprint):
    (public / "manifest.json").write_bytes(
        encode({"format": 1, "purpose": "p5b-staging", "files": tree_manifest(public)})
    )
    sign(home, fingerprint, public / "manifest.json")


def verify_seal(public, public_key, fingerprint, parent):
    verify_signature(
        public_key,
        fingerprint,
        public / "manifest.json",
        public / "manifest.json.sig",
        parent,
    )
    value = read_json(public / "manifest.json")
    require(
        value.get("format") == 1
        and value.get("purpose") == "p5b-staging"
        and value.get("files") == tree_manifest(public),
        "Missing, modified or unlisted repository object",
    )
    return value


def repository_refs(repo):
    refs = call("ostree", "--repo=" + str(repo), "refs").decode().splitlines()
    require(
        REF in refs
        and all(
            r == REF or r in ("appstream/x86_64", "appstream2/x86_64") for r in refs
        ),
        "Unexpected or missing repository refs",
    )
    require(any(r.startswith("appstream") for r in refs), "AppStream ref missing")
    return refs


def verify_repository(repo, public_key, parent):
    require(
        (repo / "summary").is_file() and (repo / "summary.sig").is_file(),
        "Signed repository summary required",
    )
    refs = repository_refs(repo)
    call("ostree", "--repo=" + str(repo), "fsck")
    with tempfile.TemporaryDirectory(prefix="verify-repo-", dir=parent) as temporary:
        client = Path(temporary) / "repo"
        call("ostree", "init", "--mode=archive", "--repo=" + str(client))
        call(
            "ostree",
            "--repo=" + str(client),
            "remote",
            "add",
            "--gpg-import=" + str(public_key),
            "--set=gpg-verify=true",
            "--set=gpg-verify-summary=true",
            "stage",
            repo.as_uri(),
        )
        call("ostree", "--repo=" + str(client), "remote", "summary", "stage")
        call(
            "ostree",
            "--repo=" + str(client),
            "pull",
            "--untrusted",
            "--disable-static-deltas",
            "stage",
            *refs,
        )
        call("ostree", "--repo=" + str(client), "fsck")
    return refs


def verify_descriptors(public, parent, entry):
    # This adds a remote only in a disposable installation; it does not install
    # or run the application, nor consult the owner's application profile.
    client = parent / "descriptor-client"
    client.mkdir(mode=0o700)
    env = {
        **os.environ,
        "FLATPAK_USER_DIR": str(client / "flatpak"),
        "XDG_DATA_HOME": str(client / "data"),
        "XDG_CONFIG_HOME": str(client / "config"),
        "XDG_CACHE_HOME": str(client / "cache"),
    }
    call(
        "flatpak",
        "remote-add",
        "--user",
        "--from",
        "p5b-staging",
        public / "cyrnava-staging.flatpakrepo",
        env=env,
    )
    actual = (
        call(
            "flatpak",
            "remote-info",
            "--user",
            "--arch=x86_64",
            "--show-commit",
            "p5b-staging",
            APP_ID + "//stable",
            env=env,
        )
        .decode()
        .strip()
    )
    require(
        actual == entry["ostree_commit"],
        "Descriptor remote resolved to an unexpected commit",
    )


def generate_repository(candidate, public, private, entry, url, *, deltas=False):
    started = time.monotonic()
    home = private / "key"
    fingerprint = make_key(home)
    public.mkdir(mode=0o755)
    repo = public / "repo"
    # Reuse the P5A exporter audit. No source rebuilding and no application launch.
    audit = private / "payload-audit"
    audit.mkdir()
    # The accepted auditor compares package provenance to a real Git checkout.
    # Use a disposable detached checkout of the approved immutable source, not
    # the later release-tooling commit. Do not execute application code from it.
    source = private / "approved-source"
    call("git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", ROOT, source)
    call("git", "-C", source, "checkout", "--quiet", "--detach", entry["source_commit"])
    require(
        call("git", "-C", source, "rev-parse", "HEAD").decode().strip()
        == entry["source_commit"],
        "Immutable source checkout mismatch",
    )
    # The accepted CI auditor binds GITHUB_SHA to its checked-out source. In a
    # promotion job that source is intentionally older than the release tooling.
    # Isolate this binding in a child; retain actual release-job context below.
    audit_environment = {**os.environ, "GITHUB_SHA": entry["source_commit"]}
    call(
        sys.executable,
        HERE / "audit_candidate.py",
        "--source",
        source,
        "--candidate",
        candidate,
        "--output",
        audit,
        env=audit_environment,
    )
    verified = read_json(audit / "audit-result.json")
    require(
        verified["source_commit"] == entry["source_commit"], "Audit source mismatch"
    )
    call("ostree", "init", "--mode=archive", "--repo=" + str(repo))
    call("flatpak", "build-import-bundle", repo, candidate / BUNDLE)
    signed_at = time.monotonic()
    call(
        "flatpak",
        "build-sign",
        "--arch=x86_64",
        "--gpg-homedir=" + str(home),
        "--gpg-sign=" + fingerprint,
        repo,
        APP_ID,
        "stable",
    )
    command = [
        "flatpak",
        "build-update-repo",
        "--title=CyrNava STAGING ONLY",
        "--default-branch=stable",
        "--gpg-homedir=" + str(home),
        "--gpg-sign=" + fingerprint,
    ]
    if deltas:
        command.append("--generate-static-deltas")
    call(*command, repo)
    signing_seconds = round(time.monotonic() - signed_at, 3)
    public_key = public / "staging-public.gpg"
    public_key.write_bytes(export_key(home, fingerprint))
    descriptors(public, url, public_key.read_bytes())
    refs = verify_repository(repo, public_key, private)
    report = {
        "format": 1,
        "purpose": "p5b-staging",
        "repository": "74Cerillion/CyrNava",
        "application_id": APP_ID,
        "version": policy()["version"],
        "architecture": "x86_64",
        **validate_candidate(candidate, entry),
        "signing_fingerprint": fingerprint,
        "authorization_ref": entry["authorization_ref"],
        "publication_target": url,
        "publication_result": "NOT PUBLISHED",
        "refs": refs,
        "flatpakrepo_native_validation": (
            "Post-publication check recorded separately in result.json"
        ),
        "runtime_lock": read_json(
            ROOT / "packaging/flatpak/production/toolchain.lock.json"
        ),
        "source_ci_workflow_id": policy()["ci_workflow_id"],
        "release_workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "release_tooling_commit": os.environ.get("GITHUB_SHA")
        or call("git", "-C", ROOT, "rev-parse", "HEAD").decode().strip(),
        "release_workflow_definition_sha256": sha(
            ROOT / ".github/workflows/release.yml"
        ),
        "static_deltas": deltas,
        "sign_and_summary_seconds": signing_seconds,
        "generation_seconds": round(time.monotonic() - started, 3),
    }
    (public / "release.json").write_bytes(encode(report))
    seal(public, home, fingerprint)
    verify_seal(public, public_key, fingerprint, private)
    return report


def init_store(path):
    path = outside_source(path)
    path.mkdir(mode=0o700)
    (path / ".p5b-staging-store").write_bytes(
        encode({"purpose": "p5b-local-staging-only"})
    )
    (path / "generations").mkdir()
    return path


def active_generation(store):
    current = store / "current"
    if not current.is_symlink():
        require(not current.exists(), "Invalid active pointer")
        return None
    link = os.readlink(current)
    require(
        re.fullmatch(r"generations/[a-f0-9]{64}", link) is not None,
        "Unsafe active generation pointer",
    )
    return safe_path(store / link)


def publish_local(public, store, public_key, fingerprint, *, before_activate=None):
    """Provider-neutral snapshot contract; no cloud/network backend exists in P5B.

    Serve stable /current/repo/ paths. Keep all previously visible objects in the
    new snapshot so clients holding an older summary can still retrieve them.
    """
    store = outside_source(store)
    require(
        stat.S_IMODE(store.stat().st_mode) == 0o700
        and store.stat().st_uid == os.getuid(),
        "Staging store must be private and owner-controlled",
    )
    require(safe_path(store / "generations").is_dir(), "Invalid generations directory")
    require(
        read_json(store / ".p5b-staging-store")
        == {"purpose": "p5b-local-staging-only"},
        "Publication requires an explicit disposable staging store",
    )
    lock = os.open(store / ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_seal(public, public_key, fingerprint, store)
        previous = active_generation(store)
        current_files = tree_manifest(public)
        if previous:
            verify_seal(previous, public_key, fingerprint, store)
            old = tree_manifest(previous)
            require(
                all(
                    current_files.get(name) == value
                    for name, value in old.items()
                    if name.startswith(("repo/objects/", "repo/deltas/"))
                ),
                "New generation would remove/change objects needed by existing clients",
            )
        generation = sha(public / "manifest.json")
        target = store / "generations" / generation
        if not target.exists():
            incoming = Path(tempfile.mkdtemp(prefix="incoming-", dir=store))
            try:
                shutil.copytree(public, incoming / "snapshot")
                verify_seal(incoming / "snapshot", public_key, fingerprint, store)
                for path in (incoming / "snapshot").rglob("*"):
                    if path.is_file():
                        with path.open("rb") as stream:
                            os.fsync(stream.fileno())
                for path in reversed(
                    [incoming / "snapshot", *(incoming / "snapshot").rglob("*")]
                ):
                    if path.is_dir():
                        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
                        try:
                            os.fsync(descriptor)
                        finally:
                            os.close(descriptor)
                os.rename(incoming / "snapshot", target)
                descriptor = os.open(
                    store / "generations", os.O_RDONLY | os.O_DIRECTORY
                )
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            finally:
                shutil.rmtree(incoming)
        verify_seal(target, public_key, fingerprint, store)
        if before_activate:
            before_activate()
        # Atomic name replacement on one local filesystem; not an assertion that
        # independent object-store PUTs can replace summary + signature atomically.
        pointer = store / ".next"
        require(
            not pointer.exists() and not pointer.is_symlink(),
            "Stale publication pointer",
        )
        pointer.symlink_to("generations/" + generation)
        os.replace(pointer, store / "current")
        descriptor = os.open(store, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return {
            "status": "PASS",
            "target": "LOCAL STAGING ONLY",
            "generation": generation,
            "previous_generation": previous.name if previous else None,
        }
    except BlockingIOError:
        raise Rejected("Another publisher holds the staging lock") from None
    finally:
        os.close(lock)
