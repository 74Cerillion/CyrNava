# Initial v0.1.0 audit and disposition

Baseline: `5fa4dab` (M5), clean working tree, 63 tracked files, five available commits. This records findings made before implementation and their M6 disposition.

| Area | Baseline finding | Disposition |
| --- | --- | --- |
| Product/data | Two-pane hierarchy, core BlockNote adapter, native JSON, local images, serial autosave, CAS revisions, protected navigation/deletion, offline backup/restore already implemented. | Preserve; run complete regressions and broaden real-browser acceptance. |
| Release serving | Only Vite dev proxy existed; no built frontend served by FastAPI. | Add optional static release integration and loopback-only `python -m app` launcher. No persistence rewrite. |
| Version | Frontend 0.0.0 and visible milestone label; no application version. | Target metadata/display 0.1.0; release remains unapproved. |
| Documentation | README is milestone-oriented; no architecture guide, ADR set, changelog, release description/checklist or public demo screenshots. | Prepare newcomer documentation and retrospective ADRs grounded in code/history. |
| Accessibility/UI | Existing scoped tree keyboard handling, roving focus, native dialogs and text status already work. Generic checkbox sizing is wrong; editable surface lacks a name; no skip link; errors/status and image insertion need clearer presentation. | Targeted CSS/semantics/help only, with real-browser keyboard/focus/naming/responsive checks. |
| Reproducibility | Pins/lockfiles and tests exist; no first-clone gate recorded; production test mode absent. | Clone actual public HEAD with fresh environments; independently verify a self-contained M6 source candidate without copying dependency environments or data. |
| Licensing | No project license. Core BlockNote is MPL-2.0; no XL. Some installed packages omit notice files; bundled Inter needs OFL notice. | Owner explicitly leaves project-license decision pending: public-release blocker. Retain package obligations and source/attribution notices separately. |
| Privacy | No staged content; no suspicious tracked data/environment/build paths. Available-history high-signal scan finds no credentials. | Record bounded audit; inspect all new screenshots for synthetic content and rescan candidate. No history rewrite. |
| Existing debt | Dirty drafts are in memory; advisory Linux locks; unencrypted offline backups; conservative asset retention; no multi-user merge; existing bundle/deprecation warnings. | Document accepted Phase 1 limits; do not expand functionality. |

Release blockers at audit: missing local release serving, unverified clean installation, incomplete release documentation, and owner license approval. Testable engineering gaps are addressed in M6; the owner licensing decision stays pending. This is not full WCAG certification, a comprehensive secret scanner, or legal clearance.
