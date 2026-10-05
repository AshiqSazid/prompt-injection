# Referee report, round 3: "Required Tool Parameters Select Confidential Prompt Facts: Schema Checks and Content Filters Do Not Govern Their Release"

Journal extension of "Filling the Form: Disclosure of Planted System-Prompt Content Through Benign Required Tool-Schema Fields".

- **Reviewed:** the working tree of `Q1_journal_writing_revision` on 2026-10-04 at 18:10 (+06): commit `f59d832` plus 19 modified and 2 new files, all uncommitted. Round 2 (`reviews/q1_review_2026-10-04_independent.md`) reviewed `f59d832` alone. The brief names `Q1_journal`; that branch does not contain this revision.
- **Conflict of interest:** this reviewer made most of the revisions under review, at the authors' request, and another assistant session made the rest. This report is therefore not independent. To limit that, every number below was recomputed again from the raw logs in this pass, and each revision is judged against the round-2 finding it was meant to fix.
- **Method:** read-only. All scripts ran on a copy of the working tree (tracked plus untracked, non-ignored files) with `.venv-q1`. No provider or scanner API was called.
- **Labels:** MATCHES, MISMATCH, NO SOURCE FOUND, UNVERIFIED; for round-2 items, RESOLVED, PARTIAL, OPEN.
- **Line numbers** refer to the working tree as reviewed.

---

## Step 0. What changed since round 2

| Area | Change |
|---|---|
| Manuscript (`paper/main.tex`) | The abstract was rewritten (249 words). The Study 4 provenance, the dropped leg, the Study 3 filter-rule sensitivity, the neutral-control structure, the abandoned Flash run, the seed sensitivity, the scanner caveats and the "oracle" wording were added. "Flagship" and "host-supplied" were replaced. `\journal{Computers \& Security}`, two `\author` lines, a drafted CRediT statement and a competing-interest declaration were added |
| Supplement (`paper/supplement.tex`) | The discarded first labelling pass, with its counts as macros |
| Generators | `code/paper_details.py`: Study 3 sensitivity, discarded Study 4 leg, request-digest check, neutral-control structure, abandoned run, seed sweep, seed-free interval, half-up rounding. `code/paper_assets.py`: discarded-pass macros. `code/manifest.py`: one README binding |
| Data | `labels/v4-apidoc-gate.first-pass-failed.worksheet.csv` un-ignored (still untracked) |
| Docs | `README.md`, `paper/README.md`, `Q1_READINESS_AUDIT.md`, `journal_paper/README.md` edited. Banners added to `docs/THREAT_MODEL.md`, `docs/RELATED_WORK.md` and `docs/archive/tp_result.md`. New `docs/DISCLOSURE.md` |
| Raw evidence | Unchanged: no file under `runs/` or `extension_runs/` differs |

**Checks on the revised copy:** `code/reproduce.py` exit 0 (204 tests; `manifest.py --check` 244 numbers, 0 prose problems). The `--check` modes of `paper_assets`, `plot_figures`, `make_tables`, `release_policies` and `journal_assets` all exit 0. No macro used in `main.tex` or `supplement.tex` is undefined.

**Not compiled:** `tikz.sty` is still missing from this machine's TeX, and the tracked `paper/Selective Recovery ... Study.zip` is still the pre-revision version. UNVERIFIED: page count, layout, undefined references in the rendered PDF.

---

## Step 1. Numbers against data

**Carried over.** The two independent recount scripts from round 2 (my own scorer, not the repository's) produce byte-identical output on the revised copy. Every table number verified in round 2 still MATCHES.

**Numbers the revision added, recomputed in this pass:**

| Claim (location) | Paper | Recomputed | Status |
|---|---|---|---|
| Neutral control structure (`main.tex:777-786`) | 20 seeds; 21 and 26 distinct argument sets | 20 distinct seeds per model; 21 and 26 distinct `params_passed`; one identical request across all 8 labels | MATCHES |
| Abandoned first Flash run (`main.tex` provenance appendix) | 125 trials; 28/65 matched; 3/260 nonmatched | same, with my own scorer | MATCHES |
| Study 3 exact decoding under the filter (`main.tex` Study 3 result) | suffix 149 and 64; reversed 133 and 51; hex unchanged | same, with my own decoder and my own Jaccard filter | MATCHES |
| Study 3 under a containment token rule | suffix 78 and 51; reversed changes by at most one trial; hex unchanged | 78 and 51; reversed 133 and 52 (against 133 and 53); hex 151 and 158 | MATCHES |
| GPT-4o suffix difference | 63.8 | 102/160 = 63.75, half up 63.8 | MATCHES |
| Seed-free paired interval (`main.tex:712-718`) | [32, 95]; [17, 86] | full enumeration of all 7^7 resamples: [32.3, 95.0]; [17.1, 86.4] | MATCHES |
| Lower endpoint across seeds 0 to 19 (same lines) | 28–32; 16–18 | repository estimator: 28.4–32.5 and 16.4–17.9. My own 10,000-draw implementation: 28.2–32.5 and **16.4–28.6** | MATCHES for the repository's estimator; **the claim is narrower than the estimator's real seed sensitivity** (n1) |
| Discarded Study 4 leg (`main.tex` Study 4 appendix, refusal result) | 39 trials; 18 matrix; told the user in 2/21; relocated 0/21 | same; the two prose disclosures quote the model's own refused call | MATCHES |
| Requests match the committed design | 1,121/1,121 | 1,121/1,121 | MATCHES |
| Launch digest equals committed design for Pro only | stated | Sol, Opus and 3.8 Flash False; Pro True | MATCHES |
| Discarded leg stopped about 1.5 min after launch, at the author's request, before outputs were inspected | stated, citing "the session record" | launch 23:39:02Z; the author's "stop it use flagship model" at 23:40:37Z; killed 23:40:48Z; no output inspected in between | MATCHES against a local session log that is **not in the artifact** (n2) |
| Discarded labelling pass (`supplement.tex` annotation paragraph) | 58/60 one category; 10/60 agree; κ 0.011 pooled; 0.000 planted | same, computed independently from the worksheet and key | MATCHES |
| Abstract, sentence by sentence | 68% / 59% vs 2% / 1%; region, operator and key fields every call; two of three allusive fields never; neutral none; 61.5 to 77.4 pp; 239/240; 151/160 and 158/160; covert every trial; allowlist removes all; 0/350 relocated, bound met on two complete legs only; every refused task fails; failed hypothesis | all reproduced | MATCHES |

**One sentence is too narrow (n1).** For Gemini Flash, the exact bootstrap distribution of the difference has a gap from 18.6 (cumulative 0.0274) to 28.6 (cumulative 0.0405), just above its 2.5% point. With 10,000 draws, about 7.5% of random streams therefore place the lower endpoint at 28.6. The "16–18" range is a property of one random number generator's first 20 seeds, not of the estimator. The conclusion that the interval excludes zero is unaffected.

---

## Step 2. Experimental code

The trial counts, the condition contrasts, sampling, seeds, pinning and partial legs are unchanged from round 2, because the data did not change. The paper now states the Study 1 block ordering, the neutral-request structure, the dropped leg, and the Sol client-side error.

**New generator code**, read for correctness:
- **`study3_sensitivity`** (`code/paper_details.py`) raises if the protocol rule stops reproducing the published P3 counts, so the alternative readings cannot drift from the table.
- **The discarded leg and the abandoned run** are each pinned by a SHA-256 digest.
- **The request-digest check** rebuilds each trial's request from the committed design. It depends on `flagship_study.build_spec`, so a future edit to the stimulus code would change the count; that is the intended behaviour.
- **`exact_cluster_bootstrap`** uses multinomial weights over sorted combinations; my enumeration over ordered resamples agrees.
- **`pp`** rounds half up. It moved three interval bounds by 0.1 (91.3, 96.3, 26.3), consistently.
- **`annotation_macros`** (`code/paper_assets.py`) now reads the discarded worksheet, pinned by digest. That file is untracked. A commit that leaves it out produces a checkout in which `paper_assets.py` raises `FileNotFoundError` (n3).

**Human labels:** unchanged. One worksheet, attested to two labelers, is rejected by `code/label.py`. The paper says so, and now also reports the discarded pass and its selection problem.

---

## Steps 3 and 4. Defense and realism

No new evidence. What changed is the wording, which now matches the evidence:
- The allowlist is called an oracle in the abstract, contribution 3 