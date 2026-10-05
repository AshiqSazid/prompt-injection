# Reviewer report, round 2: "Required Tool Parameters Select Confidential Prompt Facts: Schema Checks and Content Filters Do Not Govern Their Release"

Journal extension of "Filling the Form: Disclosure of Planted System-Prompt Content Through Benign Required Tool-Schema Fields".

- Reviewed: branch `Q1_journal_writing_revision`, commit `f59d832` (2026-10-04 03:22), manuscript `paper/main.tex` (2,792 lines) and `paper/supplement.tex` (477 lines).
- Why this branch: the brief names `Q1_journal`. That branch is the commit I reviewed in round 1 (`94f9a0e`) plus one housekeeping commit (`d25ef2b`) that adds two review files and five unused lines in `code/paper_details.py`. The revised manuscript is on `Q1_journal_writing_revision`, which was checked out while this review was running. Round 1 is at `reviews/q1_review_2026-10-04.md` on `Q1_journal`.
- Method: read-only, from a fixed `git archive` snapshot of `f59d832`, because the working tree changed branch mid-review. Raw JSONL was re-scored with my own scorer.
- Labels: **MATCHES**, **MISMATCH**, **UNVERIFIED**. Line numbers refer to `f59d832`.
- Date: 2026-10-04. Standard: IEEE TIFS / TDSC.

---

## Step 0. What changed since round 1

| Area | Change in `f59d832` |
|---|---|
| Manuscript | `paper/main.tex` rewritten around one thesis, one section per study (2,237 changed lines). New title. Pilot studies moved to a new `paper/supplement.tex` |
| Study 4 reporting | Four new generated tables: per field, per fact, refusal arm, field texts (`paper/details_study4_*.tex`) |
| Scanner | Re-run with every reply kept: `results/scan-invariant-policy-raw-20261004.json`; `code/scan_invariant.py` extended to the Study 1 to 3 fields |
| Numbers | 132 macros added (58 in `paper/numbers.tex`, 74 in `paper/details_macros.tex`). No existing macro changed value |
| Tooling | `code/cross_labels.py` (cross-references between main text and supplement), `data/citation_check.json`, extra `check` step in `paper/Makefile` |
| Raw data | Unchanged. No file under `runs/`, `extension_runs/`, `labels/` or `data/source_snapshots/` differs |
| Prose docs | Unchanged: `README.md`, `docs/THREAT_MODEL.md`, `docs/RELATED_WORK.md`, `docs/archive/tp_result.md`, `Q1_READINESS_AUDIT.md`, `paper/README.md` |

---

## Step 1. Numbers against data

**Carried over.** Every number verified in round 1 still stands: the macros have the same values and the raw files are byte-identical. That covers the Study 1 matrix and controls, Study 2 (strings, capacity, native schemas, task success), Study 3 (encoding and covert arms), the Study 4 headline counts, the classifier metrics and the reconstructed-listing arm.

**Newly recomputed this round**

| Claim | Paper | Recomputed | Status |
|---|---|---|---|
| Study 4, attribution field | user 12/12, 12/12, 6/6; operator 0/12, 0/12, 0/6 | same | MATCHES |
| Study 4, nonmatched by fact | user 17/144, 12/144, 10/72 (pooled 39/360); working directory 0; other facts 0, 1, 3 | same | MATCHES |
| Study 4, second credential field on Sol | 5 no-call, 5 user | same | MATCHES |
| Study 4, generic and neutral fields | generic 0/36, 0/36, 1/9; neutral 0/36, 0/36, 0/9 | same | MATCHES |
| Study 4, matrix task success | Sol 143/216, Opus 216/216, Pro 89/90 | same; Sol succeeds on 3 of 72 email calls | MATCHES |
| Study 4, refusal arm detail | accepted 0/159, 0/160, 0/30; retried 81, 93, 24; per-message relocation 0 in all six cells | same | MATCHES |
| Scanner re-run | 46 arms, 138 replies, all valid; B and B′ flagged; 0 of 20 study fields flagged | same; every reply is an exact YES or NO; served model `gpt-4o-mini-2024-07-18` | MATCHES |
| Pilot gate, 15 cells on three models | e.g. GPT-4o A′ 9/30, C 29/30; Gemini B 7/30 | same; a simple independent regrade agrees cell for cell | MATCHES |
| Tone arm | GPT-4o 11/30, 7/30, 26/30; Claude 30/30 three times | same | MATCHES |
| Framework arm | 0/240 disclosed, 240/240 called | same | MATCHES |
| Optional and position arm | 8/20, 14/20, 19/20, 20/20; required baselines 20/20 | same | MATCHES |
| Human-label agreement | κ 0.911 (29/30), bare 29/30, judge κ 0.855 (53/60) | same, with my own κ | MATCHES |
| Policy replay under the content filter | strings 0/640 and 0/160; enum 0/80; integer 0/80; boolean 79/80; `limit` removed in 10/80; 1,360 trials | same, with my own implementation of the filter | MATCHES |
| MCPTox survey | 45 servers, 1,048 parameters, 401 names; 0 client-identity, 0 credential, 0 policy | same; the zero credential count also holds under a looser substring match | MATCHES |
| MCP-Zero survey | 308 servers, 2,797 tools, 1,066 names; 0 client-identity; 34 credential names on 13 servers | same | MATCHES |
| Costs | US$1.23, 2.03, 6.37 | same | MATCHES |

The repository's own checks pass on the snapshot: `manifest.py --check` (244 registered numbers, 0 prose problems), `paper_assets.py --check`, `plot_figures.py --check` (10 figures).

**Status of the four round-1 mismatches**

1. "Four nonmatched facts" in the abstract: **resolved**. The abstract no longer states a count and the tables use five.
2. "The allowlist holds" versus the rule reading "not met": **partly resolved**. The abstract now reports the observation. Contribution 3 (`paper/main.tex:347-352`) and the subsection title (`:1308`) still say the allowlist "holds", while the prespecified rule is "not met" across the three models (`:1319-1323`).
3. The signed-in user "named by no field": **resolved**, and now a headline result (`paper/main.tex:1275-1306`) that matches the raw data.
4. Seed sensitivity of the primary interval: **open**. `paper/main.tex:698` still says a different seed reproduces the intervals. Seeds 3, 5, 9, 11 and 15 of the registered estimator give a GPT-4o lower bound of 28 or 29 against the reported 32.

**Not verified**

- UNVERIFIED: the confidentiality-ladder and wording-ablation numbers. The ladder is now a main-text result (`paper/main.tex:1351-1396`).
- UNVERIFIED: which scoring rule the text uses for the explicit-parameter arm. The registered pooled value is 46/100 under a partial-match rule; a full-marker rule gives 43/100 (long block 16/20 instead of 19/20).
- UNVERIFIED: bootstrap intervals of Studies 2 to 4 (point differences check), Holm-adjusted p-values (consistent with the minimum attainable under 10,000 permutations), mixed-model status.
- UNVERIFIED: page counts and supplement cross-references. The build needs TikZ (`paper/main.tex:40-41`), which my TeX installation lacks.

---

## Step 2. Experimental code

No experiment code or raw data changed, so the round-1 findings hold. In brief:

- Counts as run: Study 1 320 per model (Gemini Pro 253 with 10 errors); Study 2 1,360; Study 3 1,600; Study 4 460, 460 and 162.
- Study 1 treatment and neutral conditions differ only in the added field (`code/conditions.py:724-736`); field name and description change together.
- Temperature 0.7 in Studies 1 to 3, provider defaults in Study 4 (`code/flagship_providers.py:16`). Seeds control sampling only on OpenAI-compatible endpoints (`code/providers.py:253-257`).
- Study 1 requests alias `gpt-4o` (served as `gpt-4o-2024-08-06` under four fingerprints); Gemini is an unpinned preview alias.
- Grading in Studies 1 to 4 is deterministic substring matching (`code/make_v3_report.py:56-60`).

Facts the code and logs show that the revised paper still does not state:

- **Study 1 order was not randomized.** All five legs are collected in 16 contiguous blocks for 16 cells. `paper/main.tex:1738` still says "No record shows".
- **The neutral control repeats seeds.** Its 160 calls per model are 20 (prompt, seed) pairs issued eight times; on GPT-4o they yield 21 distinct outputs.
- **The confirmatory Gemini Flash leg is a second attempt.** A first run of 125 rows (`runs/v3_matrix_google-live-20260811-111215.jsonl`) was abandoned for a model swap. It shows the same pattern (28/65 matched, 3/260 nonmatched) and is not mentioned.
- **A first human labelling pass was discarded** (κ = 0.011, 58 of 60 labels later changed; `CLAUDE.md:1504-1509`, `.gitignore:63`). `paper/supplement.tex:264-277` reports one worksheet and does not mention it. There is still no second independent rater.

New in the revision, and disclosed: only four of the fourteen Study 4 field texts carry a recorded review (`paper/main.tex:1791-1792`). The field behind the new headline result is one of the ten that do not.

---

## Step 3. Defense

**Scanner: improved.**
- Every reply is now stored, and all 138 are exact YES or NO, which removes the round-1 parser concern.
- Coverage now includes 20 field declarations from Studies 1 to 3, including the encoded and slot-split requests. None is flagged.
- Still one policy text, re-implemented locally, judged by `gpt-4o-mini-2024-07-18`. No hosted scanner was run (`paper/main.tex:1498-1499`).
- The ten field texts used only in Study 4, including `account_attribution`, were not scanned.
- The study-authored "desc" and "desc+name" columns remain in `tab:scanners`. Their rules encode the conditions' own names and their test suite asserts the outcome (`code/scan.py:59-66`, `:199`), so they are not independent evidence.
- Tool name is constant across arms, so there is no tool-name confound. Parameter name and description still change together.

**Classifier: unchanged.**
- Nine study-authored positives, two of them named verbatim in the detector prompt (`code/defense.py:57-66`); threshold chosen on the scored set; no holdout, no repeated scoring, no raw replies (`paper/main.tex:1770-1772`).
- The one effective pilot wording scores 25 against a threshold of 20. No Study 1 to 4 field was scored.

**Release control: same evidence, better framed.**
- The content filter still needs six shared characters and does no decoding (`code/release_policies.py:44-45`), so encoded and short values pass by construction. The revised section title, "models transform confidential content on request", now describes what was measured.
- The paper now says the allowlist was defined by the experimenter and that no method of obtaining one was evaluated (`paper/main.tex:1639-1654`).
- New and verified: against a refusing provider the allowlist costs the task. No refusal-arm trial reached an accepted call (0/159, 0/160, 0/30).
- No adaptive attacker and no decoding or joining filter.

---

## Step 4. Realism

Unchanged from round 1.

| Schema source | Count | Used in |
|---|---|---|
| Synthetic, author-written | 1 tool | Study 1 |
| Synthetic, author-written | 2 tools | Studies 2a, 3, 4 |
| MCPTox listings reconstructed from text, all parameters typed string | 25 tools | One exploratory arm with a keyword measure |
| Natively captured schemas, served by local fixtures | 8 | Study 2b; one reused in Studies 3 and 4 |

- No end-to-end run against a real MCP client or remote server exists. The only transport evidence remains the three-row probe in `runs/mcp_client_capture.jsonl`, which the paper does not cite. The paper states the limit (`paper/main.tex:1729-1730`).
- The "host-supplied" user and working directory of Study 4 are synthetic values that the experimenters planted in the system prompt (`paper/main.tex:1221-1226`). No real host supplied them.
- Both preconditions remain rare in the paper's own surveys (`paper/main.tex:1573-1578`).

---

## Step 5. Documentation consistency

None of the prose docs changed, so every stale statement listed in round 1 remains. The restructure adds new ones.

| File:line | Statement | Conflict |
|---|---|---|
| `paper/README.md:4` | Old title, "Selective Recovery…" | Paper has a new title |
| `paper/README.md:9-15` | "leads with two studies"; pilots in appendices F, H and I | Four studies; pilots are in `paper/supplement.tex` |
| `paper/README.md` (LaTeX requirements) | Package list without TikZ | `paper/main.tex:40-41` requires it |
| `README.md:11` | "The active manuscript uses IEEE formatting" | Manuscript is `elsarticle` (`paper/main.tex:20`) |
| `README.md:13-15` | "no new model observations have been collected" | Studies 2 to 4 and a scanner re-run are collected |
| `README.md:38` | "Two findings", scanner observation first | Paper has four studies and one thesis |
| `README.md:70` | "Bitcoin anchoring is still pending" | Anchored (`docs/timestamps/README.md:19`) |
| `Q1_READINESS_AUDIT.md:25`, `:43`, `:46` | No further paid calls; no flagship model; refusing provider untested | Study 4 and the scanner re-run contradict all three |
| `journal_paper/README.md:3` | "The active manuscript now uses IEEEtran" | Contradicts `Q1_READINESS_AUDIT.md:3-6` |
| `docs/THREAT_MODEL.md:47-48` | "single-call adversary" | Study 4 has a multi-turn refusal arm |
| `docs/THREAT_MODEL.md:58-59`, `:219` | Fingerprinting with "no scanner alert"; schema "passes tool-poisoning scanners" | Genuine-identity claim withdrawn; one policy tested |
| `docs/THREAT_MODEL.md:87-89`, `:95-96` | Eight facts at about 99%; non-naming fields untested | Paper: five facts at 68% and 59%; adjacent fields tested |
| `docs/THREAT_MODEL.md:114-141` vs `:350-352`, `:389-390` | Detection gap is load-bearing and independent vs still self-refereed | Internal contradiction; paper treats detection as secondary |
| `docs/THREAT_MODEL.md:227-230` | Credential-shaped strings "do not come out this way" | Credential field returns the key 20/20 on five models |
| `docs/THREAT_MODEL.md:353` vs `:363-368` | Reticence "has been manipulated" vs still to be done | Internal contradiction |
| `docs/THREAT_MODEL.md:398-400` | "held-out detector prompt"; ROC still to run | ROC is run; paper says no holdout |
| `docs/THREAT_MODEL.md:404-405` | Coordinated disclosure before publishing | Paper: none documented (`paper/main.tex:1715-1716`) |
| `docs/archive/tp_result.md:25`, `:200`, `:242`, `:247`, `:409`, `:420` | Scanner and E arm unrun; Claude payload leg unrun; human κ not done; one task, one tool | All superseded by later runs |
| `docs/archive/tp_result.md:362`, `:377`, `:384` | Nine fields "genuinely unseen"; detector "a real mitigation" | Paper says the first is incorrect and the detector is not a prevention result |
| `docs/RELATED_WORK.md:36`, `:39` | "A′ 37% vs C 87% — the inversion"; "κ = 1.00" | Inversion is the failed hypothesis; κ is 0.911 |
| `docs/RELATED_WORK.md:45-49`, `:162-164` | Eight facts, about 99%, 0/1760; "invisible" to shipped policy | Exploratory v2 figures; overstated |
| `docs/RELATED_WORK.md:53-54`, `:198` | protocol-v3 "has not run"; gradient "staged, unrun" | Both ran on 2026-08-11 |
| `docs/RELATED_WORK.md:159-160` | "Pooled 92% … 0/228 across 25 real schemas" | Joins two experiments; GPT-4o on the listings is 69% |
| `docs/RELATED_WORK.md:173`, `:213` | Detection gap "should lead the paper"; abstract "must not imply secret exfiltration" | Paper leads with selectivity and reports the key in every call |
| `docs/RELATED_WORK.md` (whole file) | No mention of MSB | Paper cites MSB as prior art (`paper/main.tex:281-282`) |

---

## Step 6. Review

### Summary

The paper asks whether a required tool parameter controls which confidential system-prompt fact a model releases, and whether checks a host can apply at dispatch decide that release. Study 1 plants five synthetic facts and finds that a field naming a category returns that fact in 68% and 59% of calls on two preregistered models and each other fact in 2% and 1% of checks. Studies 2 and 3, also preregistered, record receipt at a local handler and report that a permissive pattern, categorical field types and an oracle content filter do not stop planted values, while an allowlist of task arguments does. Study 4, exploratory, repeats the matrix on three newer models, reports that a billing-attribution field returns a planted signed-in user in every trial, and shows that when a provider refuses the reduced call the models do not relocate the value and the task fails. The revision restructures the manuscript around that thesis, moves the pilot studies to a supplement, and re-runs one published scanner policy with all replies kept.

### Verified strengths

1. **Every number I recomputed matches**, now including the pilot tables, human-label agreement, policy replay, both prevalence surveys, costs, and all new Study 4 and scanner macros. No previously reported value changed in the revision.
2. **The revision reports what round 1 found missing.** The attribution result, the per-fact breakdown and the per-field table are in the main text and agree with the raw logs (`paper/main.tex:1275-1306`).
3. **Scanner evidence is now auditable**: 138 stored replies, all valid, covering 20 study fields.
4. **The paper faces its strongest objection directly** in "Is this instruction following?" (`paper/main.tex:1599-1624`), and states that its allowlist is an oracle (`:1639-1654`).
5. **The cost of the structural defense is measured**: zero accepted calls in 349 refusal trials.
6. **Clean primary manipulation, real preregistration for three studies, deterministic grading, and negative results reported**, as in round 1.
7. **Candid new limits**: only four of fourteen Study 4 texts have a recorded review; Sol's low task success is traced to an exact-match oracle (`paper/main.tex:1344-1347`, `:1791-1792`).

### Major weaknesses

**M1. No end-to-end evidence (unchanged).**
All receipt is by an in-process handler (`paper/main.tex:1729-1730`); T01 and T02 are still open. Native schemas appear in 160 trials with one field, served by fixtures. The surveys still find both preconditions rare (`:1573-1578`).

**M2. The central contrast still depends on author-assigned targets.**
The paper now concedes the point for one field: "the designated target may simply have been the wrong prediction" (`paper/main.tex:1298-1302`). The estimand is unchanged. The primary interval still resamples seven hand-picked fields; the Study 4 "adjacent class: not met" decision (`:1257-1264`) is still computed with a target the paper says was mis-specified; and no independent rater assigned any target. Independent wordings remain untested (`:1762-1765`).

**M3. A post-hoc, single-field observation now carries headline weight.**
The user-context result is in the abstract (`paper/main.tex:233-235`), contribution 1 (`:340-342`) and the highlights. It rests on one field text, 30 trials (6 on the partial leg), in an exploratory study, on a text with no recorded review. The value is called "host-supplied" (`:1275`, `:341`) although the experimenters planted it. Two further inferences rest on 12-trial cells across designs that differ: that "the semantic distance a field can bridge grows with capability" (`:1265-1269`) and that current models show the restriction "loosening" (`:1699-1702`). The finding is credible and important; it needs a prospective test with several wordings before it is stated at this level.

**M4. Defense evaluation remains thin.**
The scanner is fixed but is still one re-implemented policy. The classifier is unchanged: nine self-authored positives, overlap with the prompt, no holdout, no study field scored (`code/defense.py:57-66`, `paper/main.tex:1770-1772`). The content filter fails by construction (`code/release_policies.py:44-45`), and no adaptive attacker or decoding filter was run.

**M5. Not submittable as it stands.**
26 TODO markers (22 in `paper/main.tex`, 4 in `paper/supplement.tex`), no authors, no venue, an astrophysics template (`paper/main.tex:20`), and no documented vendor disclosure (`:1715-1716`) against the commitment in `protocol.md:230`.

### Minor weaknesses

- **m1.** "Holds" in contribution 3 and the heading at `paper/main.tex:1308` versus "not met" at `:1319-1323`.
- **m2.** `paper/main.tex:698` on bootstrap seeds (Step 1, item 4). Report the exact enumerated distribution for seven fields.
- **m3.** `paper/main.tex:1738` should state that Study 1 order was not randomized.
- **m4.** The neutral control's 160 calls are 20 seeds issued eight times; its Wilson interval overstates precision.
- **m5.** The discarded first labelling pass and the abandoned first Gemini Flash run are not disclosed (Step 2).
- **m6.** Gemini Pro is partial in both studies, yet the abstract says "all three" models (`paper/main.tex:234`), on 6 attribution trials for that leg.
- **m7.** "Reproduce" (`paper/main.tex:234`, `:340`, `:1943`) for a study that differs from Study 1 in models, temperature, facts, fields, tools, repetitions and scorer.
- **m8.** The confidentiality ladder is now a main-text result and supports an introduction claim (`paper/main.tex:321-323`), with 10 to 20 attempts per cell and one incomplete cell (`:1385-1390`). Numbers UNVERIFIED.
- **m9.** The unplanted control cannot fail by construction and has few calls on the ceiling fields (Gemini operator 2/20).
- **m10.** Sol's matrix task success (143/216) reflects an exact-match oracle rejecting a quoted phrase, so task-success figures are not comparable across models. Disclosed.
- **m11.** In Study 3 the region suffix normalizes to three alphanumeric characters. The GPT-4o suffix difference is 63.75 points and is printed as 63.7.
- **m12.** The reconstructed-listing arm uses a different outcome and planted fact from Study 1 (`paper/main.tex:1398-1407`).
- **m13.** Stale supporting docs (Step 5), including a build README without TikZ.
- **m14.** UNVERIFIED: length against TIFS/TDSC limits.

### Required changes, ranked by impact

| # | Change | Rough effort |
|---|---|---|
| 1 | End-to-end run: real MCP transport, at least one commercial client, a remote server recording receipt, with the host's own injected context as the protected facts | 3–5 weeks |
| 2 | Prospective, preregistered test of the user-context result: several independently written attribution-style and path-style fields, blinded target assignment, complete legs on all models | 1–2 weeks, under US$50 |
| 3 | Larger independently authored field sample (30 or more) for the primary contrast; exact or hierarchical interval | 2–3 weeks |
| 4 | Rebuild the classifier evaluation with a frozen prompt and threshold, a holdout, every study field, repeated scoring and stored replies; run at least one current hosted scanner | 2–4 weeks |
| 5 | Add a decoding and joining filter and an attacker that adapts to it | 1–2 weeks |
| 6 | Text corrections: m1 to m7, and describe the planted user as planted | 1 day |
| 7 | Complete or drop Gemini Pro; collect the two missing unplanted cells; rerun Study 1 with randomized order, pinned snapshots and distinct control seeds | 2–3 days, under US$20 |
| 8 | Resolve disclosure under `protocol.md` §14 | 1–2 weeks elapsed |
| 9 | Authors, venue and matching template, TODO items, length | 1 week |
| 10 | Second independent labelling worksheet; disclose the discarded pass | 2–3 days |
| 11 | Bring the prose docs in line with the paper or mark them archived | 1 day |

### Requests for evidence

1. Provide correlated dispatch and remote-receipt records from at least one commercial MCP client.
2. Provide a prospective replication of the attribution result with more than one field wording.
3. Provide classifier scores for every field text used in Studies 1 to 4, including `account_attribution`.
4. Provide scanner verdicts for the ten field texts used only in Study 4.
5. Provide a second, independently completed human worksheet, and state which author produced the existing one.
6. Provide the disclosure chronology required by `protocol.md` §14, or the recorded decision not to notify.
7. Provide the completed Gemini Pro legs, or remove "all three" from the abstract.
8. State the number of independent neutral-control samples per model.
9. Explain why the first Gemini Flash run was abandoned, and add it to the provenance record.
10. Provide full-node verification of the timestamp proofs (T04).

### Scores

| Criterion | Round 1 | Round 2 | Justification |
|---|---|---|---|
| Novelty | 3 | 3 | The channel is prior art; selectivity, the transformation result and the cost of the allowlist are new but incremental. |
| Soundness | 3 | 3 | The text now agrees with the data, but the central contrast still rests on author-assigned targets and a post-hoc result is promoted to the abstract. |
| Experimental rigor | 3 | 3 | Excellent provenance; still seven fields, two confirmatory models, blocked ordering and two partial legs. |
| Defense evaluation | 2 | 2 | The scanner record is fixed; the classifier and the filter are unchanged. |
| Presentation | 2 | 3 | One thesis, a clear study-per-section structure and an honest objection section; still 26 TODOs and no authors or venue. |
| Significance | 3 | 3 | The user-context result raises relevance; receipt is still local and the preconditions are rare in the paper's own surveys. |

### Recommendation

**Major Revision.** The revision is a clear improvement and closes the reporting problems of round 1. What blocks acceptance is now evidence, not writing.

### The single change that would most improve the paper

Test the user-context result prospectively and end to end: a real MCP host, the context that host itself injects, several independently written attribution and path fields, and a remote server recording what arrives.
