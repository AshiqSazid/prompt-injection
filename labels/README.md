# labels/ — what is and is not a human rating

`protocol.md` §5 requires a **human** to hand-label 15–20% of trials and reports
Cohen's kappa against the automatic grader, with a bar of kappa >= 0.80.

| File | Rater | Discharges protocol §5? |
|---|---|---|
| `v4-apidoc-gate.worksheet.csv` | **human-labelled 2026-08-21**; the attestation names two authors for its one rating column | **NOT YET** — scaffolded κ=0.911 is human-versus-keyword-grader agreement; `label.py --kappa` rejects the attestation, and a second independent rater is owed |
| `v4-apidoc-gate.first-pass-failed.worksheet.csv` | human, first pass, discarded after its agreement was known (κ=0.011) | **NO** — a record, never data |
| `v4-apidoc-gate.rater2.worksheet.csv` | **nobody yet** — a blank form for a second, independent human rater (same 60 blinded rows, empty `label` column), with `…rater2.attestation.json` to complete and `…rater2.key.json` (a copy of the key; do not open until done) | **NOT YET** |
| `v4-apidoc-gate-CLAUDE-ADJUDICATION.worksheet.csv` | **Claude (an LLM)** | **NO** |

The `-CLAUDE-ADJUDICATION` file is a **third automatic grader**, produced by the
same model family under test. It is useful as a rubric dry-run and for surfacing
disagreements, and it reached kappa = 1.000 against the keyword grader on the
scaffolded stratum. **It is not human labelling and must never be reported as
such.** Two automatic graders agreeing is not evidence that either is right:
judge-1 was perfectly self-consistent and scored kappa = -0.125 against the
keyword grader, worse than chance, on this exact construct.

`label.py --kappa` refuses to claim §5 is met unless invoked with `--rater human`.
It also requires every sampled row to be labelled and a completed human
attestation JSON. The attestation is an audit record, not proof of identity; the
paper should state who labelled the data and their relationship to the project.

An AI assistant may explain the rubric, validate CSV formatting, or compute
agreement. It must not fill the worksheet, suggest row-level labels, complete the
attestation, or be reported as a human annotator.

## How to label

The second rater must not have seen the first worksheet, the key, or any
grader output, and labels the blank form:

```bash
.venv-q1/bin/python code/label_tui.py labels/v4-apidoc-gate.rater2.worksheet.csv
.venv-q1/bin/python code/label.py --kappa labels/v4-apidoc-gate.rater2.worksheet.csv \
    --rater human --attestation labels/v4-apidoc-gate.rater2.attestation.json
```

Agreement between the two human worksheets is a row-by-row comparison of their
`label` columns; `label.py` does not compute it yet. The first rater's form:

```bash
.venv/bin/python label_tui.py labels/v4-apidoc-gate.worksheet.csv
```

One row, one keypress, resumable; progress is saved after every key, so stopping
midway is safe. `label_tui.py` imports only the eight bucket names from
`grade.py` — it never reads the key file, the keyword grader or the judge, so it
cannot show you an automatic verdict for the row you are judging. It has no
default and no suggested label. It is data entry, not adjudication.

Then complete `v4-apidoc-gate.attestation.json` — the blank form is generated,
the four fields are not, and `statement` must exactly equal `required_statement`:

> I personally assigned every label in this worksheet without using an AI system
> to choose or suggest labels.

That sentence is the reason an assistant cannot fill this worksheet on your
behalf. Finally:

```bash
.venv/bin/python label.py --kappa labels/v4-apidoc-gate.worksheet.csv \
    --rater human --attestation labels/v4-apidoc-gate.attestation.json
```
