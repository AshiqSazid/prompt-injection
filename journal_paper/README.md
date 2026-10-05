# IEEE TDSC preparation draft

**Older draft.** The active manuscript is `../paper/main.tex` (elsarticle); see
`../Q1_READINESS_AUDIT.md`. This folder's manuscript uses `IEEEtran`
journal/compsoc formatting and an IEEE bibliography, and does not report
Studies 3 and 4. The supplement is a separate PDF. Direct SCImago evidence confirms
**2025 Q1** in the two listed categories; see [venue dossier](../docs/TDSC_TARGET.md).
**This is not an approved submission:** author details, declarations, independent
review and the agreed prospective experiment remain unfinished.

## Files

- `main.tex` / locally built `main.pdf`: existing-evidence manuscript.
- `supplement.tex` / locally built `supplement.pdf`: statistical supplement.
- `COVER_LETTER.md`: editable letter draft, not sent; attestations pending.
- `numbers.tex`, `journal_numbers.tex`, `*_table.tex`, `refs.bib`,
  `evidence_lock.json`: generated and checked; do not edit manually.
- `additional_refs.bib`: reviewed additions/overrides to `paper/refs.bib`.

Experiment 25 has been collected (stage A 1,200 calls, stage B 160 calls, under
the sealed protocol and amendment 1) and is reported in `main.tex` Section
"Prospective schema-constraint experiment" and the supplement. Its numbers and
tables come from the declared canonical files through `code/journal_assets.py`;
mock runs are never used.

## Build and verify

```bash
.venv-q1/bin/python code/journal_assets.py --write
.venv-q1/bin/python code/reproduce.py
.venv-q1/bin/python code/reproduce.py --write-papers
.venv-q1/bin/python code/submission_check.py
```

LaTeX needs `IEEEtran.cls`, `IEEEtran.bst` and its Computer Society fonts
(Palatino, Times, Helvetica and Courier), plus the packages imported by the sources.
On TinyTeX, install missing fonts using `tlmgr install palatino times helvetic courier`.
The last Python command fails until the author decisions and exact final source
approvals are complete. Rebuilding evidence locks is not author approval.

The 100–200-word abstract, separate supplement and current page counts are
mechanically reviewable. Confirm final template settings, author biographies,
fees and portal requirements before submission. TDSC is single-anonymous;
replace the explicit pending-author placeholder with confirmed author details.

See [the handoff](../docs/SUBMISSION_HANDOFF.md) and
[experiment protocol](../docs/JOURNAL_EXTENSION_PROTOCOL.md).
No upload, publication or vendor notification has been performed.
