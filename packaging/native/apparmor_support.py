"""N2 exact-path AppArmor contract. No GUI, policy auto-loading or global changes."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CONTRACT = {
    "format": 2,
    "mode": "enforce",
    "abi": "5.0",
    "access": "ordinary-user-allow-all",
}
LEGACY_CONTRACT = {"format": 1, "mode": "default_allow", "abi": "5.0"}
NAME = r"cyrnava-native-u[0-9]+-[0-9a-f]{32}"


def require_contract(operation, contract):
    if contract == CONTRACT or (operation == "remove" and contract == LEGACY_CONTRACT):
        return
    raise ValueError("Legacy policy is permitted only for exact historical removal")


def read_loaded_profile(
    name, base=Path("/sys/kernel/security/apparmor/policy/profiles")
):
    """Read only this profile's public kernel metadata; never assume mode from source."""
    if not re.fullmatch(NAME, name):
        raise ValueError("Invalid kernel profile identity")
    try:
        matches = [
            p
            for p in base.iterdir()
            if p.name.startswith(name + ".") and p.name[len(name) + 1 :].isdecimal()
        ]
        if len(matches) != 1:
            return {"state": "ABSENT" if not matches else "AMBIGUOUS", "profile": name}
        entry = matches[0]
        actual_name = (entry / "name").read_text().strip()
        mode = (entry / "mode").read_text().strip()
        if actual_name != name:
            return {"state": "IDENTITY MISMATCH", "profile": name}
        known = {
            "enforce",
            "allow",
            "default_allow",
            "unconfined",
            "complain",
            "kill",
            "prompt",
        }
        return {
            "state": "PRESENT",
            "profile": name,
            "mode": mode if mode in known else "unknown",
        }
    except OSError as error:
        return {"state": "UNREADABLE", "profile": name, "errno": error.errno}


def profile_name(root, uid=None):
    root = Path(root)
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Absolute canonical installation root required")
    uid = os.getuid() if uid is None else uid
    if type(uid) is not int or uid < 0:
        raise ValueError("Invalid owner identity")
    return (
        f"cyrnava-native-u{uid}-" + hashlib.sha256(os.fsencode(root)).hexdigest()[:32]
    )


def policy_path(path):
    """Quoted literal AARE; reject patterns instead of broadening attachment."""
    path = str(path)
    if (
        not Path(path).is_absolute()
        or ".." in Path(path).parts
        or any(ord(c) < 32 or ord(c) == 127 or c in "*?[]{}^\\" for c in path)
    ):
        raise ValueError("Unsupported literal AppArmor path")
    return '"' + path.replace('"', '\\"') + '"'


def render_policy(root, release, uid=None, *, contract=None):
    root, release = Path(root), Path(release)
    if release.parent != root / "releases" or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?-[0-9a-f]{16}", release.name
    ):
        raise ValueError("Exact installed release required")
    helper = (
        release
        / ".venv/lib/python3.14/site-packages/PySide6/Qt/libexec/QtWebEngineProcess"
    )
    inherited = [Path("/usr/bin/python3.14"), release / ".venv/bin/python", helper]
    contract = CONTRACT if contract is None else contract
    if contract not in (CONTRACT, LEGACY_CONTRACT):
        raise ValueError("Unsupported AppArmor policy construction")
    mode = "enforce" if contract == CONTRACT else "default_allow"
    return (
        "# CyrNava N2: ordinary-user access; namespace allowance for this process family.\n"
        "# Per-user writable attachment is NOT signature enforcement. No global change.\n"
        "abi <abi/5.0>,\n"
        f"profile {profile_name(root, uid)} {policy_path(root / 'cyrnava-native')} flags=({mode}) {{\n"
        + ("  allow all,\n" if contract == CONTRACT else "")
        + "  userns create,\n"
        + "".join(f"  {policy_path(p)} ix,\n" for p in inherited)
        + "}\n"
    ).encode()


def check_label(root, label=None):
    if label is None:
        label = Path("/proc/self/attr/apparmor/current").read_text()
    expected = profile_name(root)
    if label.rstrip("\n") != expected + " (enforce)":
        raise ValueError("Expected CyrNava AppArmor profile is not attached")
    return {"profile": expected, "label": label.rstrip("\n")}


def compile_bootstrap(source, output):
    """One bounded compiler job; no downloads or recipient-side compilation."""
    import resource
    import time

    if Path(output).exists():
        raise ValueError("Existing bootstrap output preserved")

    def limit():
        resource.setrlimit(resource.RLIMIT_AS, (128 * 1024**2, 128 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))

    command = [
        "/usr/bin/cc",
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-fPIE",
        "-pie",
        "-fstack-protector-strong",
        "-D_FORTIFY_SOURCE=2",
        "-Wl,-z,relro,-z,now,-z,noexecstack",
        str(source),
        "-o",
        str(output),
    ]
    started = time.monotonic()
    result = subprocess.run(
        command, check=False, capture_output=True, timeout=60, preexec_fn=limit
    )
    if result.returncode:
        Path(output).with_suffix(".compiler.private.log").write_bytes(result.stderr)
        raise RuntimeError(
            "Bootstrap compilation failed; preserve private compiler log"
        )
    Path(output).chmod(0o700)
    if Path(output).stat().st_size >= 1024**2:
        raise ValueError("Bootstrap exceeds reviewed 1MiB bound")
    return {
        "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        "executable_sha256": hashlib.sha256(Path(output).read_bytes()).hexdigest(),
        "compiler": subprocess.check_output(["/usr/bin/cc", "--version"], timeout=5)
        .decode()
        .splitlines()[0],
        "options": command[1:-3],
        "seconds": round(time.monotonic() - started, 3),
        "address_space_limit_bytes": 128 * 1024**2,
        "cpu_limit_seconds": 60,
    }


# This literal executes under system Python -I. Root NEVER imports repository code
# or executes a mutable user-owned helper. Policy bytes arrive on stdin and are
# checked against an explicit digest before exclusive root-owned creation.
ROOT_HELPER = r"""
import hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
operation,name,expected = sys.argv[1:]
if os.geteuid()!=0 or operation not in {'load','remove'} or not re.fullmatch(r'cyrnava-native-u[0-9]+-[0-9a-f]{32}',name) or not re.fullmatch(r'[0-9a-f]{64}',expected):
    raise SystemExit('Root policy identity refused')
directory=Path('/etc/apparmor.d')
info=directory.lstat()
if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:
    raise SystemExit('Unsafe policy directory')
if Path('/proc/sys/kernel/apparmor_restrict_unprivileged_userns').read_text().strip()!='1':
    raise SystemExit('Global namespace restriction differs; no policy change')
path=directory/name
profiles=Path('/sys/kernel/security/apparmor/profiles')
def present():
    return [s for s in profiles.read_text().splitlines() if s.split(' (',1)[0]==name]
parser=['/usr/sbin/apparmor_parser','--skip-cache','--jobs=1']
if operation=='load':
    data=sys.stdin.buffer.read(65537)
    if len(data)>65536 or hashlib.sha256(data).hexdigest()!=expected:
        raise SystemExit('Policy digest refused')
    if present(): raise SystemExit('Existing profile preserved')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o644)
    subprocess.run(parser+['--skip-kernel-load',str(path)],check=True,timeout=30)
    subprocess.run(parser+['--add',str(path)],check=True,timeout=30)
    actual=present()
    if actual != [name+' (enforce)']:
        modes=[s.rsplit(' (',1)[-1].removesuffix(')') for s in actual]
        print(json.dumps({'status':'FAIL','stage':'post-load-mode-check','profile':name,'actual_modes':[m if m in {'enforce','allow','default_allow','unconfined','complain','kill','prompt'} else 'unknown' for m in modes],'policy_sha256':expected}))
        raise SystemExit('Loaded profile mode unverified; preserve file')
else:
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or info.st_mode&0o022 or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise SystemExit('Changed policy preserved')
    for process in Path('/proc').iterdir():
        if not process.name.isdecimal(): continue
        try: label=(process/'attr/apparmor/current').read_text().strip()
        except FileNotFoundError: continue
        except PermissionError: raise SystemExit('Process labels unreadable; removal refused')
        if any(part==name or part.startswith(name+'//') for part in label.split(' (',1)[0].split('//&')):
            raise SystemExit('Live profile process; close normally before removal')
    if not present(): raise SystemExit('Profile missing; removal requires review')
    subprocess.run(parser+['--remove',str(path)],check=True,timeout=30)
    if present(): raise SystemExit('Profile removal unverified; preserve file')
    path.unlink()
fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
os.fsync(fd); os.close(fd)
print(json.dumps({'status':'PASS','operation':operation,'profile':name,'policy_sha256':expected}))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "load", "remove"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument(
        "--policy-sha256", help="Required reviewed policy digest for load/remove"
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--owner-host", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    repo = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "n2_policy_engine", repo / "desktop/install_engine.py"
    )
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    engine.host_supported()
    root = engine.private_directory(args.root)
    engine.require(
        root.parent == repo / "ci-output", "Disposable direct ci-output client required"
    )
    output = engine.checked_path(args.output)
    engine.require(
        output.parent == repo / "ci-output" and not output.exists(),
        "Fresh direct evidence output required",
    )
    with engine.installation_lock(root):
        release = (
            root
            / "releases"
            / engine.member_name(engine.load(root / "current.json")["release"])
        )
        receipt, manifest = engine.installed(release)
        engine.require(
            receipt["manifest_sha256"] == args.manifest_sha256,
            "Reviewed AppArmor candidate required",
        )
        require_contract(args.operation, manifest.get("apparmor"))
        policy = render_policy(root, release, contract=manifest["apparmor"])
        expected = hashlib.sha256(policy).hexdigest()
        if args.operation != "prepare":
            engine.require(
                args.policy_sha256 == expected,
                "Explicit reviewed policy checksum required",
            )
        output.mkdir(mode=0o700)
        name = profile_name(root)
        (output / name).write_bytes(policy)
        record = {
            "status": "PREPARED",
            "operation": args.operation,
            "profile": name,
            "policy_sha256": expected,
            "manifest_sha256": args.manifest_sha256,
            "native_launch": "NOT EXECUTED",
            "host_policy": "NOT MODIFIED",
            "kernel_before": read_loaded_profile(name),
        }
        try:
            subprocess.run(
                ["/usr/sbin/apparmor_parser", "-Q", "-K", "-j1", str(output / name)],
                check=True,
                capture_output=True,
                timeout=30,
            )
            record["parser"] = "PASS"
            if args.operation != "prepare":
                if args.owner_host:
                    engine.require(sys.stdin.isatty(), "Owner terminal required")
                command = [
                    "/usr/bin/sudo",
                    *([] if args.owner_host else ["-n"]),
                    "/usr/bin/python3.14",
                    "-I",
                    "-c",
                    ROOT_HELPER,
                    args.operation,
                    name,
                    expected,
                ]
                # In owner-host mode sudo may prompt via /dev/tty; child output stays private.
                result = subprocess.run(
                    command, check=False, input=policy, capture_output=True, timeout=90
                )
                (output / "policy.private.log").write_bytes(
                    result.stdout + result.stderr
                )
                if result.returncode:
                    record.update(
                        status="BLOCKED",
                        failure_category="privileged-policy-operation-failed",
                        exit_code=result.returncode,
                        host_policy="NOT CONFIRMED; preserve policy and private log",
                    )
                    if result.stdout:
                        try:
                            detail = json.loads(result.stdout)
                        except (ValueError, UnicodeDecodeError):
                            detail = {}
                        if (
                            detail.get("stage") == "post-load-mode-check"
                            and detail.get("profile") == name
                            and detail.get("policy_sha256") == expected
                        ):
                            modes = detail.get("actual_modes")
                            if isinstance(modes, list) and all(
                                m
                                in {
                                    "enforce",
                                    "allow",
                                    "default_allow",
                                    "unconfined",
                                    "complain",
                                    "kill",
                                    "prompt",
                                    "unknown",
                                }
                                for m in modes
                            ):
                                record.update(
                                    status="FAIL",
                                    failure_category="loaded-policy-mode-rejected",
                                    host_policy="ADDED; MODE REJECTED",
                                    actual_modes=modes,
                                )
                else:
                    loaded = json.loads(result.stdout)
                    engine.require(
                        loaded
                        == {
                            "status": "PASS",
                            "operation": args.operation,
                            "profile": name,
                            "policy_sha256": expected,
                        },
                        "Root policy receipt mismatch",
                    )
                    record.update(
                        status="PASS",
                        host_policy="LOADED" if args.operation == "load" else "REMOVED",
                    )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            record.update(
                status="FAIL",
                error_type=type(error).__name__,
                host_policy="NOT CONFIRMED",
            )
        record["complete"] = True
        record["kernel_after"] = read_loaded_profile(name)
        engine.durable(output / "result.json", record)
        print(json.dumps(record, indent=2))
        return 0 if record["status"] in {"PREPARED", "PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
