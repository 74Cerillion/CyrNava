"""Explicit P6 post-import preference contract; never part of the application."""

import base64
import hashlib
import json
import re
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{64}")
COMMON_CHECKS = {
    "appearance_preference_valid",
    "imported_workspace_bound",
    "preinteraction_preference_verified",
}
CHECKS = {
    "reset": "post_import_preference_reset",
    "preserve": "imported_preferences_preserved",
}
JAVASCRIPT = (
    "(()=>{const control=document.querySelector('.appearance-control select');"
    "if(!control)return null;return JSON.stringify({"
    "selected:control.value,appearance:localStorage.getItem('engage.appearance.v1'),"
    "theme:localStorage.getItem('cyrnava.theme.v1'),"
    "resolved:document.documentElement.getAttribute('data-mantine-color-scheme'),"
    "system_dark:matchMedia('(prefers-color-scheme: dark)').matches})})()"
)


def require(value, message):
    if not value:
        raise ValueError(message)


def saved_state(value):
    require(
        isinstance(value, dict) and set(value) == {"appearance", "theme"},
        "Invalid saved preference fields",
    )
    require(
        value["appearance"] in (None, "auto", "light", "dark")
        and value["theme"] in (None, "cyrnava"),
        "Invalid saved preference values",
    )
    return dict(value)


def digest(value):
    return hashlib.sha256(
        json.dumps(saved_state(value), sort_keys=True).encode()
    ).hexdigest()


def identity(value):
    require(
        isinstance(value, dict) and set(value) == {"workspace", "qt_profile"},
        "Missing workspace preference identity",
    )
    require(
        all(isinstance(v, str) and SHA.fullmatch(v) for v in value.values()),
        "Invalid workspace preference identity",
    )
    return dict(value)


def reset_config(maintenance, edited):
    require(
        edited.get("status") == "PASS"
        and edited.get("complete") is True
        and edited.get("checks", {}).get("dark_preference_saved") == "PASS",
        "Verified original Dark preference required",
    )
    require(
        maintenance.get("status") == "PASS"
        and maintenance.get("complete") is True
        and maintenance.get("checks", {}).get("import_activated_new_workspace")
        == "PASS",
        "Successful explicit import required",
    )
    old = identity(maintenance.get("previous_workspace_identity"))
    new = identity(maintenance.get("workspace_identity"))
    require(
        old == identity(edited.get("workspace_identity")),
        "Pre-import workspace changed unexpectedly",
    )
    require(
        all(old[k] != new[k] for k in old),
        "Import must select a separate workspace and Qt profile",
    )
    return {"mode": "reset", "workspace_identity": new}


def preserve_config(baseline):
    require(
        baseline.get("status") == "PASS" and baseline.get("complete") is True,
        "Verified post-import baseline required",
    )
    config = {
        "mode": "preserve",
        "workspace_identity": identity(baseline.get("workspace_identity")),
        "expected": saved_state(baseline.get("preferences_snapshot")),
    }
    require(
        all(
            baseline.get("checks", {}).get(k) == "PASS"
            for k in COMMON_CHECKS
            | {CHECKS["reset"], "post_import_new_preference_saved"}
        ),
        "Unverified post-import baseline",
    )
    require(
        baseline.get("preference_policy") == "P6-post-import-reset"
        and baseline.get("initial_preferences_snapshot")
        == {"appearance": None, "theme": None}
        and config["expected"] == {"appearance": "light", "theme": None},
        "Explicit new imported-workspace preference required",
    )
    require(
        baseline.get("preferences_sha256") == digest(config["expected"]),
        "Post-import baseline hash mismatch",
    )
    return config


def validate_config(config):
    require(
        isinstance(config, dict) and config.get("mode") in CHECKS,
        "Invalid P6 preference mode",
    )
    expected_keys = {"mode", "workspace_identity"} | (
        {"expected"} if config["mode"] == "preserve" else set()
    )
    require(set(config) == expected_keys, "Unexpected P6 preference configuration")
    identity(config["workspace_identity"])
    if config["mode"] == "preserve":
        saved_state(config["expected"])
    return config


def required_checks(config):
    validate_config(config)
    return (
        COMMON_CHECKS
        | {CHECKS[config["mode"]]}
        | ({"post_import_new_preference_saved"} if config["mode"] == "reset" else set())
    )


def validate_result(config, value):
    validate_config(config)
    require(
        value.get("preference_policy") == "P6-post-import-" + config["mode"],
        "Wrong preference policy evidence",
    )
    require(
        identity(value.get("workspace_identity")) == config["workspace_identity"],
        "Imported preference workspace changed",
    )
    probe = PreferenceContract(config)
    probe.observe(json.dumps(value.get("initial_appearance_observation")), {})
    require(
        probe.before_owner({"checks": {}}, value.get("live_workspace_identity")),
        "Missing or invalid preinteraction preference evidence",
    )
    state = saved_state(value.get("preferences_snapshot"))
    require(
        value.get("preferences_sha256") == digest(state),
        "Preference evidence hash mismatch",
    )
    require(
        all(value.get("checks", {}).get(k) == "PASS" for k in required_checks(config)),
        "Preference contract failed",
    )
    if config["mode"] == "preserve":
        require(
            state == config["expected"], "Imported preference changed during reinstall"
        )


class PreferenceContract:
    def __init__(self, config):
        self.config = validate_config(config)
        self.check_name = CHECKS[config["mode"]]
        self.first = self.last = None
        self.invalid = False
        self.gated = False

    def javascript(self):
        return JAVASCRIPT

    def observe(self, value, result):
        # Cancelled WebEngine callbacks must not erase a valid earlier sample.
        if value is None:
            return
        try:
            sample = json.loads(value) if isinstance(value, str) else None
            require(
                isinstance(sample, dict)
                and set(sample)
                == {"appearance", "theme", "selected", "resolved", "system_dark"},
                "Incomplete appearance observation",
            )
            saved_state({k: sample[k] for k in ("appearance", "theme")})
            require(
                sample["resolved"] in ("dark", "light")
                and sample["selected"] in ("auto", "dark", "light", "cyrnava")
                and type(sample["system_dark"]) is bool,
                "Invalid resolved appearance",
            )
        except (ValueError, TypeError):
            self.invalid = True
            return
        if (
            self.config["mode"] == "preserve"
            and {k: sample[k] for k in ("appearance", "theme")}
            != self.config["expected"]
        ):
            # Later reselection must never repair observed preference loss.
            self.invalid = True
        if self.first is None:
            self.first = sample
        self.last = sample

    @staticmethod
    def resolved_valid(sample):
        if sample is None:
            return False
        expected_dark = (
            sample["theme"] == "cyrnava"
            or sample["appearance"] == "dark"
            or (sample["appearance"] in (None, "auto") and sample["system_dark"])
        )
        selected = (
            "cyrnava"
            if sample["theme"] == "cyrnava"
            else sample["appearance"] or "auto"
        )
        return (
            sample["resolved"] == ("dark" if expected_dark else "light")
            and sample["selected"] == selected
        )

    def before_owner(self, result, workspace_identity):
        """Called while the native window is disabled, before instructions/unlock."""
        expected = (
            {"appearance": None, "theme": None}
            if self.config["mode"] == "reset"
            else self.config["expected"]
        )
        self.gated = (
            not self.invalid
            and self.resolved_valid(self.first)
            and {k: self.first[k] for k in ("appearance", "theme")} == expected
            and identity(workspace_identity) == self.config["workspace_identity"]
        )
        result.update(
            initial_appearance_observation=self.first,
            live_workspace_identity=workspace_identity,
        )
        result["checks"]["preinteraction_preference_verified"] = (
            "PASS" if self.gated else "FAIL"
        )
        return self.gated

    def instructions(self):
        if self.config["mode"] == "reset":
            return (
                "System appearance was recorded before input.\n\n"
                "Confirm the synthetic note, folder and screenshot.\n"
                "Select Appearance → Light. Wait for Saved, then close normally."
            )
        return (
            "The original Light baseline was verified before input.\n\n"
            "Confirm the synthetic note, folder and screenshot.\n"
            "Do not change Appearance or edit data. Close normally."
        )

    def finish(self, result, workspace_identity):
        checks = result["checks"]
        checks["preinteraction_preference_verified"] = "PASS" if self.gated else "FAIL"
        checks["imported_workspace_bound"] = (
            "PASS"
            if identity(workspace_identity) == self.config["workspace_identity"]
            else "FAIL"
        )
        valid = (
            not self.invalid
            and self.resolved_valid(self.first)
            and self.resolved_valid(self.last)
        )
        checks["appearance_preference_valid"] = "PASS" if valid else "FAIL"
        first = (
            {k: self.first[k] for k in ("appearance", "theme")} if self.first else None
        )
        last = {k: self.last[k] for k in ("appearance", "theme")} if self.last else None
        if self.config["mode"] == "reset":
            matched = first == {"appearance": None, "theme": None}
            checks["post_import_new_preference_saved"] = (
                "PASS"
                if valid and last == {"appearance": "light", "theme": None}
                else "FAIL"
            )
        else:
            matched = (
                first == self.config["expected"] and last == self.config["expected"]
            )
        checks[self.check_name] = "PASS" if valid and matched else "FAIL"
        result.update(
            preference_policy="P6-post-import-" + self.config["mode"],
            preferences_snapshot=last,
            initial_preferences_snapshot=first,
            preferences_sha256=digest(last) if last else None,
            appearance_observation=self.last,
        )


def script(original, config):
    """Call the P4 verifier's explicit optional hook; legacy main() stays strict."""
    validate_config(config)
    adapter = Path(__file__).read_bytes()
    encoded_adapter = base64.b64encode(adapter).decode()
    encoded_original = base64.b64encode(original).decode()
    encoded_config = json.dumps(config)
    return f"""
import base64 as _b64, json as _json
_adapter_bytes = {encoded_adapter!r}
_checker_bytes = {encoded_original!r}
_config = {encoded_config!r}
_adapter = {{"__name__": "p6_preference_contract", "__file__": "<p6-preferences>"}}
_checker = {{"__name__": "p6_reviewed_checker", "__file__": "<p6-reviewed-checker>"}}
exec(compile(_b64.b64decode(_adapter_bytes), "<p6-preferences>", "exec"), _adapter)
exec(compile(_b64.b64decode(_checker_bytes), "<p6-reviewed-checker>", "exec"), _checker)
_contract = _adapter["PreferenceContract"](_json.loads(_config))
raise SystemExit(_checker["main"](preferences=_contract))
""".encode()
