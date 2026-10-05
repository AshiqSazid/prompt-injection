# Q1 readiness: current state

Updated 2026-10-05. **Not submission-ready.** The main manuscript is
`paper/main.tex` (elsarticle, `\journal{Journal of Information Security and
Applications}` since 2026-10-05), with the pilot
studies in `paper/supplement.tex`. `journal_paper/` is an older six-page IEEE
draft and `usenix_paper/` an older conference version; neither reflects the work
below. The round-4 review (`reviews/q1_review_2026-10-04_round4.md`) recommends
major revision; what it blocks on is new evidence, listed under
"What still limits the science". A revision pass is under way: the venue is set,
the build is repaired (TikZ added), the Study 4 cost label and the Study 3
alternative-reading decision are fixed, and the working-record docs are being
reconciled with the paper.

The round-5 review (`reviews/q1_review_2026-10-04.md`) also recommends major
revision. Its text corrections were applied on 2026-10-05 with no new model
call: the refusal arm now reports the two Gemini Pro trials that wrote the
planted working directory into a kept file path; the classifier paragraphs
match Table I.4 and state that one score moved on rescoring; the scanner
coverage sentence is accurate; the label-matching confound is in the threats
section; and the ethics paragraph says no notice has been sent. Its other
required changes need new experiments and are listed under "What still limits
the science".

## What the paper now contains

| Evidence | Status |
|---|---|
| Study 1: fact-by-field matrix, two preregistered models | Confirmatory. Matched 95/140 and 82/140 against 9/560 and 4/560 nonmatched. The paired bootstrap was implemented after collection. |
| Study 2: constraints and typed fields at handler receipt | Confirmatory. A permissive pattern does not reduce recovery; typed fields deliver the planted value in 239/240 trials. |
| Policy replay over the Study 2 calls | Exploratory, no model calls. The task allowlist removes every planted value; an oracle content filter misses the boolean. |
| Study 3: encodings and typed slots against the content filter | Confirmatory. Sealed, Bitcoin anchor verified before the first planted call, 1,600 trials on two models, both rules met on both models. |
| Study 4: three newer models, planted user and working directory, a tool that refuses the reduced call | Exploratory, no timestamp; design files committed with the data. Selectivity holds; a billing-attribution field returns the planted user on all three models (post hoc, one field text); no relocation of the targeted fact under refusal (one model wrote the planted working directory into a kept file path in 2 of 30 trials), and every refused task fails. The Gemini Pro leg is partial and a fourth leg was discarded. |
| Larger tool corpus (308 servers) and host-context survey (9 hosts) | Descriptive, no model calls. |
| Pilot studies, scanner votes, field classifier | Supplement and appendix. The scanner policy was re-run on 2026-10-04 with every reply kept and covers the 30 added fields of Studies 1 to 4, each on a synthetic order tool only. The classifier's nine positives and the 28 study fields were rescored with three repetitions; its 506 negatives were not. One preregistered superiority hypothesis failed and is reported in the abstract. |

Build as of 2026-10-05 (TikZ installed in the local TinyTeX): `make -C paper
pdf` produces main (45 pp) and supplement (11 pp) with 0 undefined references,
`make -C paper check` passes (254 registered numbers, 0 prose problems), and
`code/reproduce.py` passes (204 offline tests). The local `paper/main.pdf`
(gitignored) was rebuilt from the current source and carries the current title.

## Spending

Study 2 cost US$1.23. Study 3 stage 1 cost about US$2.09 of its US$15 cap
(two legs and the compatibility checks). As of 2026-10-02 no further paid calls
were authorized. Study 4 ran afterwards under per-leg approvals
(`extension_runs/approval-S4-*.json`) at US$6.37, and the scanner policy was
re-run on 2026-10-04 (138 `gpt-4o-mini` calls, then 168 with the Study 4 fields).

## What still blocks submission

| Blocker | Who | What is needed |
|---|---|---|
| Authors and declarations | Authors | Names, order, affiliations, corresponding author, CRediT roles, funding, competing interests (T22 to T25). The sections are hidden behind TODO comments. |
| AI-use statement | Authors | Review the wording: an AI assistant restructured the paper, implemented the replay and the Study 3 and Study 4 harnesses, and ran their calls under author approvals (T26). |
| Human-label attestation | Authors | One worksheet is attributed to two labelers, which the validator rejects (T05, T06). The discarded first labelling pass is released as `labels/v4-apidoc-gate.first-pass-failed.worksheet.csv` and disclosed in the supplement. |
| Study 4 discarded leg | Authors | The session record shows no `gemini-3.8-flash` output was inspected before the leg was stopped, and the paper states this; authors confirm the attestation (T32). |
| Field-review record for Study 3 | Author | Confirm or correct `docs/STUDY_3_STAGE1_FIELD_REVIEW.md`. |
| Venue | Authors | Changed on 2026-10-05 to the **Journal of Information Security and Applications** (Elsevier, same elsarticle source). Computers & Security is out of scope: its Elsevier page states a moratorium since early 2024 on submissions with AI or ML as a significant component and that "items directed to the security of AI/ML systems themselves (such as LLM and federated learning) are out of scope". The JISA scope page has no such exclusion. JISA was chosen on its Scopus/SCImago Q1 listing, which the author says is the list that counts; its JCR quartile is probably Q2. Still to do: read the JISA author guide, which refused automated access, and confirm the SCImago quartile (T34). `docs/TDSC_TARGET.md` is a superseded IEEE note. |
| Artifact release | Authors | DOI, licence, release scope (T27). The MCP-Zero snapshot is MIT-licensed and attributed. |
| Disclosure | Authors | Decided on 2026-10-04: notify six parties before submission, then wait 30 days (`docs/DISCLOSURE.md`). No notice has been sent yet, and the paper says so (T17). |
| Citations | Authors | All 45 records checked at title, author and abstract level; a full-text read is still open (T20, T21, T29, T30), and ten entries lack page numbers (T28). |
| Independent review | Outside reviewer | Statistics and novelty; a second person to repeat the timestamp check against a full node (T04). |

## What still limits the science

- Two confirmatory models, both older, and one main task. Study 4 adds three
  newer models, but it is exploratory, one leg is partial, and it changes the
  wordings and sampling settings along with the models.
- Seven hand-picked fields in Study 1, with targets assigned by the authors, so
  its interval is wide. Every field wording is the study's own.
- The user-context result rests on one field text (`account_attribution`, no
  recorded review) and 30 trials; it needs a prospective test with several
  wordings.
- Receipt is by a local handler. No commercial client, no remote server (T01, T02).
- Untested: a filter that decodes or joins arguments, an attacker that adapts
  to a filter, and a refusal returned by a remote provider. Study 4 tested a
  model whose reduced call a local handler refused (T16).
- Study 4 planted a working directory and a signed-in user; platform and date
  were not planted, and no real host supplied any of them.
- The field classifier has nine study-authored positives and no holdout. Scored
  on the 28 study field texts it misses 15, with no clear rule for which, and
  the one positive near its threshold changed score on rescoring.
- The prompts label each fact with the noun its naming field uses, so selecting
  a fact by category is not separated from matching a label. No trial states a
  fact in different vocabulary.
- The scanner saw the Study 2 to 4 fields on one synthetic tool only.
- Study 2's Bitcoin anchors postdate part of its collection; Study 4 has no
  timestamp. The paper says so.

The wider design in `docs/STUDY_3_PROTOCOL.md` (more fields, current models, an
enforcing provider) addresses several of these points. It needs a new budget.

## Where things are

- Manuscript and its notes: `paper/main.tex`, `paper/supplement.tex`, `paper/README.md`, `paper/REVISION_AUDIT.md`
- Reviews, all in `reviews/`: `q1_review_2026-10-04_writing_revision.md`, `_independent.md`, `_round3.md`, `_round4.md`, and `q1_review_2026-10-04.md` (round 5, the latest; its text corrections were applied on 2026-10-05)
- Study 3: `docs/STUDY_3_STAGE1_PROTOCOL.md`, `docs/STUDY_3_STAGE1_RUN_LOG.md`, `code/release_stage1.py`
- Study 4: `docs/STUDY_4_PROTOCOL.md`, `code/flagship_study.py`, `extension_runs/flagship-live-*`
- Policy replay: `code/release_policies.py`, `data/release_policy_replay.json`
- Surveys: `code/registry_prevalence.py`, `data/host_context_survey.json`
- Timestamp checks: `docs/timestamps/README.md`

```bash
.venv-q1/bin/python code/reproduce.py
make -C paper check
make -C paper pdf
```
