# N3 owner checkpoint

3 November 2026. **N1/N2 ACCEPTED / COMPLETE. N3 VERIFIED PASS / RECOMMENDED FOR
OWNER ACCEPTANCE. N4 unauthorized.** Report: [N3_REPORT.md](N3_REPORT.md).

- [x] Shared native updater/recovery/uninstaller and thin shell wrappers implemented.
- [x] Authenticated release path retains trusted-key, signature, hash and extraction checks.
- [x] Real disposable full-package upgrades and provider/backend/data validation PASS.
- [x] Whole-profile checkpoints, imported workspace, compatible binary rollback/return PASS.
- [x] Actual uninstall/reinstall preserves data, origin, Qt storage, backups and release payloads.
- [x] Actual portable backup/import and newer-schema refusal PASS.
- [x] 175 native regressions, 92 backend regressions, Ruff/format/shell/Desktop Entry checks PASS.
- [x] Owner executed the reviewed exact new-client policy load; current mode enforce.
- [x] Saved load result and non-GUI bootstrap independently reviewed PASS.
- [x] Actual final-package GUI/renderer/authentication/menu/appearance/reinstall checks PASS in both phases.
- [x] Saved data/origin bytes and actual completed uninstall/reinstall inventories independently checked.
- [x] Package/source/provider/accepted N2 identities preserved; 29 independent review checks PASS.
- [ ] Formal N3 owner acceptance. No N4 implementation begins automatically.

Actual result: `ci-output/native-n3-owner-1/result.json`, PASS / complete.
SHA-256: `f933f6f48449106860c87b33f22ac2b192ed11cad7bb041e34901df42a295bf7`.
Independent review: [review.json](evidence/n3/native-review-2026-11-03/review.json).
Original records and private logs remain in place. Existing regressions were not
rerun; no implementation or native execution occurred in this review.

## Formal acceptance option

If satisfied with the documented support boundary and evidence, the owner may state:

> I formally accept N3 — Data-safe manual updater and uninstaller.
> N4 remains pending separate authorization.

No further N3 GUI test is required. This candidate is unsigned/disposable and supports
schema 5 with the unchanged application/data/Qt consumer family. Uninstall retains
program versions/data/checkpoints. N3 acceptance does not authorize N4, signing,
commits/pushes, CI or public release.

## Historical completed host step — do not repeat

The owner ran this handoff in **GNOME Terminal outside VS Code/Codex**. It loads
only the new disposable N3 client's exact profile, preserves the accepted N2 policy, changes no global
settings, and runs a non-GUI bootstrap check. It never starts an application.
The script pins source hashes and refuses inherited confinement/NoNewPrivs.

```bash
bash "/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava/ci-output/native-n3-policy-review-1/load-reviewed-policy-on-owner-host.sh"
```

Script SHA-256: `ab27e2121c93ed43b8a9c3f1ed082b5e0a93299927a5af7f306fb16ac071f4fd`.
Profile: `cyrnava-native-u1000-7180461d3e5719da3d409effaeb8b936`.
Policy SHA-256: `2e8eba098eafda2302478f1b4be7ce4320e7c8250acfa7733a30d3231ba0d1bd`.
Saved PASS result: `ci-output/native-n3-policy-owner-load-1/`.
Saved non-GUI bootstrap PASS; current exact profile enforce independently confirmed.

## Historical completed focused GUI step — do not rerun

The following command and interactions produced the reviewed attempt-1 PASS.
They are retained for provenance; the output already exists and must be preserved.

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
/usr/bin/python3.14 -B packaging/native/verify_update.py --owner-host \
  --manifest-sha256 6f18cbd08dbccf4c578b0412805856d143f38f5c1d927ae2e753f85bbcbab096 \
  --output "$PWD/ci-output/native-n3-owner-1"
```

This uses only `native-n3-client-1` and its imported synthetic workspace. Expect
two short launches, approximately 2–4 minutes of interaction:

1. After registration, click **CyrNava — N2 Candidate** once in GNOME Applications.
   The internal label is retained from the unchanged accepted application.
2. Confirm the imported workspace initially selects **System**. Open the existing
   **N2 installed note**, inspect its image/bold content, and select **Dark**.
   Do not edit the note or paste another screenshot. Close normally when the
   repeated live-checks PASS / CLOSE instruction appears.
3. The driver verifies data, uninstalls/reinstalls the disposable activation and
   confirms every stopped profile byte is unchanged. No data is deleted.
4. When prompted, click the same menu entry again; verify the same note/image,
   **Dark**, window/icon/grouping. Close when instructed, then enter
   `CONFIRM N3 UPDATE` only if every requested observation is correct.

Live evidence must complete within 30 seconds; close reminders repeat every five
seconds after success. No automatic GUI retry, signing, network, normal installation
or policy change occurs. The temporary menu entry is removed only if unchanged.
If it fails, close normally and retain the fresh output/private logs for review.
Do not rerun the command or change the imported profile to bypass a preflight.

Uninstall deliberately retains program versions/checkpoints/data; it is not a purge
or disk-cleanup command. Production signing/publication/licensing closeout belong
to separately authorized N4. The existing ordinary-user tradeoff and MIT selection
are already decided; renderer sandboxing remains mandatory.
