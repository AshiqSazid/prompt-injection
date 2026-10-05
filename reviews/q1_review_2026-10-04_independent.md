# Referee report: "Required Tool Parameters Select Confidential Prompt Facts: Schema Checks and Content Filters Do Not Govern Their Release"

Journal extension of "Filling the Form: Disclosure of Planted System-Prompt Content Through Benign Required Tool-Schema Fields".

- **Reviewed:** branch `Q1_journal_writing_revision`, commit `f59d832` (2026-10-04), manuscript `paper/main.tex` (2,792 lines) with `paper/supplement.tex`. The brief names `Q1_journal`; the author chose the newer branch, which holds this restructured manuscript. Line numbers refer to `f59d832`.
- **Method:** read-only. All scripts ran in a throwaway `git archive` copy of `f59d832` with `.venv-q1` (Python 3.12.3). No provider or scanner API was called. The headline counts were recomputed by my own scorer, written for this review, which reads the raw JSONL and does not import the repository's scoring code. Bootstrap intervals were re-derived by my own resampling. Other intervals and p-values were checked only through the repository's generators (`--check` modes); they are marked as such.
- **Labels:** MATCHES, MISMATCH (both values), NO SOURCE FOUND, UNVERIFIED.
- **Independence:** two other review files exist (`reviews/q1_review_2026-10-04.md` and `_second.md` on `Q1_journal`, and `reviews/q1_review_2026-10-04_writing_revision.md` here). This report was produced without using them.

---

## Step 0. Repository map

| Kind | Location |
|---|---|
| Manuscript | `paper/main.tex` (elsarticle, no `\journal`, no authors), `paper/supplement.tex` (pilot studies). Older drafts: `journal_paper/main.tex` (IEEE, 6 pp), `usenix_paper/main.tex` |
| Generated paper inputs | `paper/numbers.tex` (`code/manifest.py --tex`), `paper/analysis_numbers.tex`, `paper/details_*.tex`, `paper/generated_*.tex` (`code/paper_assets.py`, `code/paper_details.py`), `paper/*_labels.tex` (`code/cross_labels.py`), `paper/figures/*.pdf` (`code/plot_figures.py`) |
| Raw results | `runs/` (149 tracked files: Study 1, pilots, gate, real-schema arm), `extension_runs/` (83 tracked: Studies 2, 3, 4 with `.meta.json`, `.ledger.jsonl`, `.raw.jsonl`, approval files, console logs) |
| Derived data | `data/defense_eval.json`, `data/benign_fields.json`, `data/real_tools.json`, `data/release_policy_replay.json`, `data/registry_prevalence.json`, `data/host_context_survey.json`, `data/artifact_selection.json`, `data/source_snapshots/native/*` (8 captured MCP schemas) |
| Scanner output | `results/scan-invariant-policy-raw-20261004.json` (every reply kept), `results/scan-snyk-inspect-20260808-120749.txt` |
| Harness and analysis | `code/run.py`, `conditions.py`, `providers.py` (Study 1); `schema_types_{design,run,analyze}.py` (Study 2); `release_stage1.py`, `release_policies.py` (Study 3 and replay); `flagship_study.py`, `flagship_providers.py` (Study 4); `q1_analysis.py`, `stats.py`, `scoring_sensitivity.py`, `reproduce.py` |
| Defense code | `code/defense.py` (field classifier), `code/scan.py` (study-authored profiles), `code/scan_invariant.py` (published policy), `code/release_policies.py` (P0–P4) |
| Human labels | `labels/v4-apidoc-gate.worksheet.csv`, `.key.json`, `.attestation.json`; `-CLAUDE-ADJUDICATION` files (a model grader) |
| Protocols | `protocol-v3.md` (Study 1), `docs/JOURNAL_EXTENSION_PROTOCOL.md` + `AMENDMENT_1` (Study 2), `docs/STUDY_3_STAGE1_PROTOCOL.md` (Study 3), `docs/STUDY_4_PROTOCOL.md` (Study 4, not timestamped); `.ots` proofs and `docs/timestamps/*.upgraded.ots` |
| Prose docs | `README.md`, `docs/THREAT_MODEL.md`, `docs/RELATED_WORK.md`, `docs/archive/tp_result.md`; also `CLAUDE.md`, `Q1_READINESS_AUDIT.md`, `docs/Q1_PUBLICATION_CHECKLIST.md`, `paper/README.md`, `paper/REVISION_AUDIT.md` |

**Reproduction gates (in the throwaway copy):** `code/reproduce.py` exit 0 (204 tests OK, `manifest.py --check` 244 numbers / 0 prose problems, tables, v3 report, evidence inventory, statistical appendix, journal assets all fresh). `paper_assets.py --check`, `plot_figures.py --check` (10 figures), `make_tables.py --check`, `release_policies.py --check`, `journal_assets.py --check` all exit 0. `cross_labels.py --check` exits 1 in a fresh copy only because `supplement.aux` must be compiled first. The 153-macro fallback snapshot in `main.tex:56-210` is identical to the generated values.

**Not compiled.** The reviewed source adds a TikZ figure (`main.tex:40-41, 424-455`). `tikz.sty` is absent from this machine's TeX, so I could not build the PDF. The tracked bundle `paper/Selective Recovery ... Study.zip` contains the previous version (old title, no TikZ), so **no PDF of the reviewed source exists in the repository.** UNVERIFIED: page count, undefined references, layout.

---

## Step 1. Numbers against data

All counts below were recomputed from the raw rows unless marked otherwise.

### Study 1 (`runs/v3_matrix_*`, `runs/v3_unplanted_*`)

| Claim (location) | Paper | Recomputed | Status |
|---|---|---|---|
| Abstract, Table `tab:primary`: GPT-4o matched / nonmatched | 95/140 (68%), 9/560 (2%) | 95/140, 9/560 | MATCHES |
| Same, Gemini Flash | 82/140 (59%), 4/560 (1%) | 82/140, 4/560 | MATCHES |
| Paired difference and field-bootstrap CI | 66 [32, 95]; 58 [17, 86] | 66.3 [32.3, 95.0]; 57.9 [16.4, 86.4] (my seed 1) | MATCHES (Monte Carlo noise) |
| Leave-one-field-out range (`main.tex:754-755`) | 60.6–77.5; 50.8–67.5 | 60.6–77.5; 50.8–67.5 | MATCHES |
| Table `tab:fields`, all 14 cells | e.g. `client_user_agent` 15/20, 2/20 | identical, all 14 | MATCHES |
| Table `tab:classes`, all 10 rows | naming 75/80, 62/80, 80/80, 64/77, 80/80; adjacent 20/60 ×4, 40/43 | identical | MATCHES |
| Table `tab:matrix`: Claude, DeepSeek, Pro | 100/140, 0/560; 84/137, 4/548; 120/123, 24/492 | identical | MATCHES |
| Neutral control (`main.tex:758-762`) | 0/160 calls, 0/800 checks, both models | identical | MATCHES |
| Generic field | 0/20, 0/20 | identical | MATCHES |
| Unplanted controls (`main.tex:848-857`) | 0/93, 0/77, 0/120, 0/77; pooled 0/367 | identical; six fields per model | MATCHES |
| Accounting table `tab:accounting_table-1` | attempts, errors, emitted per arm; total 2,013 rows, 10 errors | identical | MATCHES |
| Wilson and bootstrap intervals for single cells | various | generator `--check` only | UNVERIFIED independently |
| Crosstalk split (`main.tex:833-837`) 8/9, 4/4 | — | generator only | UNVERIFIED independently |

### Study 2 (`extension_runs/schema_types-{A,B}-live-*`)

| Claim | Paper | Recomputed | Status |
|---|---|---|---|
| Table `tab:exp25`, 2a Gemini / GPT-4o free and constrained | 157/160, 157/160; 158/160, 154/160 | identical | MATCHES |
| Same, 2b | 32/40, 30/40; 33/40, 32/40 | identical | MATCHES |
| Differences 0.0, 2.5, 5.0, 2.5 | — | arithmetic agrees | MATCHES; CIs UNVERIFIED independently |
| Table `tab:exp25capacity`, 12 cells; `\ExpACapacityPlanted` 239/240 | 40/40 ×5, 39/40; unplanted 6, 5, 20 / 6, 5, 19 | identical | MATCHES |
| Holm-adjusted p ≤ 0.0006 | — | generator only | UNVERIFIED independently |
| Selectivity at receipt (`main.tex:1039-1043`) | 98.1%, 98.8%; other facts 0.0%; unplanted 0/40 | 157/160, 158/160; 0/480 each; 0/40 | MATCHES |
| Task success 2a, 2b (`main.tex:1047-1050`) | 320/320 ×2; 60/80, 61/80 | identical | MATCHES |
| Misses 14 (2a), 33 (2b) | — | 14, 33 | MATCHES |
| First-word truncations 12, 17; wrong tool 13; no call 1 | — | not recomputed | UNVERIFIED independently |
| Table `tab:release`, P0 receipts and P0 2b task success | 626, 127, 80, 80, 79; 121 | identical | MATCHES |
| Table `tab:release`, P1 2b task 98, P3 boolean 79, P3 integer task 70 | — | generator only | UNVERIFIED independently |

### Study 3 (`extension_runs/release_stage1-live-*`)

| Claim | Paper | Recomputed | Status |
|---|---|---|---|
| Table `tab:study3` P0 / P3 / P2 per encoding, harness fields | Gemini 160/154/136/151, P3 0/153/133/151; GPT-4o 160/105/57/158, P3 0/102/53/158; P2 all 0 | identical from the row-level `policy` fields | MATCHES |
| Same, re-decoded by my own decoder (exact suffix, exact reversal) | as above | Gemini suffix P0 153 (vs 154); GPT-4o suffix 98 (vs 105), reversed 53 (vs 57) | MATCHES under the protocol's rule (`docs/STUDY_3_STAGE1_PROTOCOL.md:125-126`: substring after decoding, suffix by `endswith`). The protocol rule credits over-long and partly wrong outputs; see minor weakness m7 |
| P3 under a "half of its tokens" containment reading of the filter (`main.tex:1090`) | — | suffix P3 Gemini 78 (vs 153), GPT-4o 48 (vs 102); hex and reversed unchanged | Rule-definition sensitivity; see major weakness M4 |
| Covert arm, both models, both lengths | 40/40 ×4 planted; 0/40 ×4 unplanted; P2 0 | identical | MATCHES |
| Differences 95.6, 83.1, 94.4, 63.7, 33.1, 98.8 | — | arithmetic agrees | MATCHES; CIs UNVERIFIED independently |
| Cost US$2.03 | — | 1.136 + 0.894 from meta files | MATCHES |

### Study 4 (`extension_runs/flagship-live-*`)

| Claim | Paper | Recomputed | Status |
|---|---|---|---|
| Table `tab:study4`, all 21 cells | 92/144, 17/720, 61.5; 114/144, 13/720, 77.4; 56/72, 13/360, 74.2; naming, adjacent, relocated | identical; my hits equal harness `received_hits` on every row | MATCHES; intervals UNVERIFIED independently |
| Table `tab:study4-fields`, 42 cells | — | identical | MATCHES |
| Table `tab:study4-facts`, 18 cells | user 17/144, 12/144, 10/72; working directory 0 | identical | MATCHES |
| Abstract: user via billing field "all three" | 12/12, 12/12, 6/6 | identical | MATCHES |
| First turn 349/350, relocated 0/350, prose 0/350, unplanted 0/210 | — | identical, **for the three reported legs** | MATCHES; see M1 for the fourth leg |
| Trials 1,082; Pro missing 298; stopped 159, 160; Pro kept calling 16 | — | identical | MATCHES |
| Sol credential-2 split 5 no-call / 5 user; Sol email quoted 68/71; task 143/216 | — | not recomputed | UNVERIFIED |
| Cost US$6.37 | — | 0.684 + 4.505 + 1.181 | MATCHES |
| "each echoed back by its provider exactly as requested" (`main.tex:2227`) | — | served IDs in Study 4 raw files not checked | UNVERIFIED |

### Robustness, detection, context

| Claim | Paper | Recomputed | Status |
|---|---|---|---|
| Table `tab:real-schemas` (keyword T1) | GPT-4o 78/113, 78/125, 22/24 tools, D 0/109; Claude 120/120, 120/125, 24/24, D 0/119, 0/124; D pooled 0/228 | identical | MATCHES |
| Gate deltas (`main.tex:1522-1523`) | 67, 0, 0 | A′ 9/30 vs C 29/30; 30/30 vs 30/30 ×2 | MATCHES |
| Scanner (`main.tex:1487-1496`, `tab:scanners`) | 3 reps, 138/138 valid, 46 arms, B and B′ flagged, 20 study arms (9/4/7) 0 flagged | identical | MATCHES |
| Classifier (`main.tex:1501-1510`, `tab:ppv`) | AUC 0.994, FPR@20 2.6%, TPR 100%, PPV 3.8 / 28.2 / 67.2%, attack wording 25, Sequential Thinking 5/13 | AUC 0.9936, 13/506, 9/9, same PPVs, 25, 5/13 | MATCHES; AUC CI and the 15 for `user_agent.original` UNVERIFIED |
| Depth table `tab:depth`, reticence figure, framework arm 0/240, prevalence counts (0/401 etc.), MCP-Zero counts, host survey | — | generator `--check` only | UNVERIFIED independently |
| Figures `selectivity`, `gradient`, `matrix`, `constraints` | — | underlying counts recomputed above; `plot_figures.py --check` passes | MATCHES |
| Figure 1 (threat model) | no numbers | — | n/a |

**No MISMATCH was found in any table, figure or abstract number.** No reported number lacks a source. One prose claim about provenance does not match the record (M1).

---

## Step 2. Experimental code

**Trial counts as run.** Study 1: 320 per model for the four complete arms; Gemini Pro 253 with 10 errors; unplanted 120 per model over 6 of 8 fields. Study 2a: 600 per model, plus one failed Gemini launch file of 598 error rows (excluded, disclosed). Study 2b: 80 per model. Study 3: 800 per model, 0 errors; Gemini resumed 50 times. Study 4: Sol 460 (1 error), Opus 460 (0 errors, 1 resume), Pro 162 of 460, and **`gemini-3.8-flash` 39 rows (18 matrix, 21 refusal), not reported in any table.**

**Do conditions differ only in the intended variable?**
- Study 1: C and D differ only in the added field's name and description. Prompt, task, tool, temperature (0.7) and `max_tokens` are constant (checked in rows). Name and description vary together, as `main.tex:1736-1737` admits.
- Study 1 execution order: each model's 320 trials ran as **16 contiguous blocks**, one per condition and field. Field is therefore confounded with collection time. `main.tex:1738` says only that "no record shows that trial order ... was randomized"; the record shows it was not.
- Study 2: free and constrained arms share prompt, task and facts; the capacity domains vary wording, fact and type together (disclosed, `main.tex:1033-1035`).
- Study 3: encodings vary field name and description together. The filter is fixed in code (`code/release_policies.py:44-45, 70-84`).
- Study 4 differs from Studies 1–3 in model, **sampling (provider defaults instead of T = 0.7)**, output cap (2,048 instead of 1,024), number of planted facts (6 instead of 4–5), and field wordings. Cross-study comparisons confound all five.
- Scanner arms: the tool name is constant inside each comparison (`lookup_recent_orders` for all 35 pilot and Study 1 arms, `fixture_orders` for the 11 Study 2 and 3 arms). **No tool-name confound.**

**Temperature, seeds, pinning.** Studies 1–3 used T = 0.7; Study 4 sent no temperature. Seeds are recorded per row but only reach OpenAI-compatible endpoints (`code/providers.py:119-215`); for Gemini, Anthropic and Study 4 they are labels. Study 1 requested undated aliases (`gpt-4o`, `gemini-3-flash-preview`), disclosed at `main.tex:1754-1755`. Studies 2–3 pin `gpt-4o-2024-08-06`. Gemini models throughout are preview identifiers.

**Grader.** Deterministic normalized substring matching (`main.tex:603-618`). My independent scorer reproduces Studies 1, 2 and 4 exactly, row by row for Study 4. Study 3 reproduces under the protocol's lenient decode rule. The Study 1 credential alias is a 12-character prefix (`code/conditions.py:569`), which the three-rule sensitivity check covers.

**Human labels.** One 60-row worksheet exists (`labels/v4-apidoc-gate.worksheet.csv`). It covers only the pilot gate's keyword measure, not the main marker endpoint. The attestation names **two labelers with the same completion second for one worksheet** (`labels/v4-apidoc-gate.attestation.json`), and `code/label.py --kappa ... --rater human --attestation ...` rejects it ("incomplete human attestation"). **No human inter-rater agreement exists in the repo.** The paper says so (`main.tex:2030, 2727-2729`); `README.md:274-275` and `CLAUDE.md:1495` still claim "protocol §5 MET, κ = 0.911".

**Missing or partial legs.** Study 1: Gemini Pro partial with no generic cell; unplanted controls lack the platform-adjacent and region-adjacent fields. Study 4: Pro partial (162/460); `gemini-3.8-flash` started and dropped. Sol's single "API error" is a client-side `PydanticUserError`, not a provider error (`extension_runs/flagship-live-gpt-6.1-sol-*.jsonl`, trial `796c0266...`).

---

## Step 3. Defense

| Component | Evaluation data | Overlap with design | Holdout | Curves and rates | External comparison |
|---|---|---|---|---|---|
| Field classifier (`code/defense.py`) | 9 positive rows (7 distinct names: `agent_identity` and `caller_context_summary` appear twice) vs 506 real benign fields (472 MCPTox, 34 OpenTelemetry) | Yes: `system_prompt` and `model_name` are named in the detector prompt and are positives (`main.tex:2391-2394`); the prompt was rebuilt by an author who knew C | None (`main.tex:2418-2423`) | ROC, FPR at 20 and 80, PPV scenarios; no PR curve | none |
| Study-authored scanner profiles (`code/scan.py`) | pilot conditions | Yes: R1 fields were required to be scanner-clean under these profiles (`code/test_harness.py:318-325`, `TestR1FactField`) | n/a | binary | n/a |
| Published policy (`code/scan_invariant.py`) | 46 declarations, 3 reps, raw replies kept | Independent rule text, study-chosen inputs | n/a | binary | Invariant `policy.gr` from mcp-scan 0.3.39 only; hosted Snyk service not run |
| Dispatch policies P0–P4 (`code/release_policies.py`) | Study 2 replay (post hoc); Study 3 and 4 prospective | P2 allowlist and P3 filter use **oracle** knowledge of task arguments and planted values | n/a | counts | none |

- The classifier was never scored on the region, operator, credential, encoded or slot-split fields of Studies 1–4 (`main.tex:2535-2538`), so its AUC says nothing about the paper's main attacks.
- The scanner result is clean of tool-name confounds, but the study-authored profiles report "clean" for C by construction.
- The positive recommendation, the allowlist, is evaluated only as an oracle (`main.tex:1640-1644`). It is applied to local handlers and was never derived by a realizable host mechanism.

---

## Step 4. Realism

| Source | Schemas | Use |
|---|---|---|
| Synthetic, study-authored | `lookup_recent_orders` (Study 1), `fixture_orders`, `fixture_email` (Studies 2–4) | all primary results |
| MCPTox rendered listings | 25 tools from 25 servers, reconstructed as all-string schemas (`data/real_tools.json`) | pilot arm, keyword measure |
| Native captured MCP schemas | 8 (`data/source_snapshots/native/*.json`, with raw `tools_list` captures); served by local fixtures, servers not executed | Study 2b (8), Study 3 and 4 (`files-official` only) |
| Corpora, no model calls | 45 MCPTox servers / 401 names; MCP-Zero 308 servers; 9 open-source host prompts | descriptive context |

**Every added field wording was written by the study team.** No independently authored or in-the-wild field was tested, and the paper's own survey finds client-identity fields in 0/401 MCPTox names (`main.tex:1543-1545`).

**End-to-end MCP client.** Only `runs/mcp_client_capture.jsonl` exists: 3 rows dated 2026-08-10, one per condition, recorded by the local stdio server. The file holds no model, provider or raw response, so its live-model origin is **UNVERIFIED**. `docs/THREAT_MODEL.md:296-327` calls it "OBSERVED"; `docs/Q1_PUBLICATION_CHECKLIST.md` calls the transport "mock plumbing"; the paper does not cite it and states that no MCP transport or remote server was measured (`main.tex:500-502, 1729-1730`). **No commercial client and no remote server appear anywhere.**

---

## Step 5. Documentation consistency

| File:line | Statement | Contradicted by |
|---|---|---|
| `README.md:10-11` | "The active manuscript uses IEEE formatting" | `paper/main.tex:17-20` (elsarticle) |
| `README.md:24` | focused revision "is now in journal_paper/" | `Q1_READINESS_AUDIT.md:3-6` (paper/main.tex is the manuscript) |
| `README.md:70` | "Bitcoin anchoring is still pending" | `main.tex:2561-2567` (anchors verified, block 961955) |
| `README.md:105` | "0/401 request a credential" as the whole story | `main.tex:1562-1571` (MCP-Zero has credential-taking parameters) |
| `README.md:135` | `usenix_paper/` is the "USENIX submission" | `Q1_READINESS_AUDIT.md:3-6` |
| `README.md:274-275` | "§5 discharged ... κ = 0.911" | `code/label.py` rejects the attestation; `main.tex:2030, 2727-2729` |
| `README.md` (whole) | no mention of Studies 3 or 4; Study 2 called "Experiment 25" | `main.tex:1073-1347` |
| `docs/THREAT_MODEL.md:155, 174` | C = 87% as the attack rate | paper's primary endpoint is matched/nonmatched recovery (`main.tex:708-765`); 87% is a pilot cell |
| `docs/THREAT_MODEL.md:216-228` | attack chain "80–100% ... for identifier-shaped content" | identifier-shaped bound withdrawn (`README.md:110-111`; credential 20/20, `main.tex:843-845`) |
| `docs/THREAT_MODEL.md:296-327` | transport link "now OBSERVED" | `main.tex:500-502`; checklist says mock plumbing |
| `docs/THREAT_MODEL.md:370-373` | "0/401 ask for a credential" | `main.tex:1562-1571` |
| `docs/THREAT_MODEL.md` (whole) | adversary model has no host release policy, refusal, or dispatch controls | `main.tex:424-455` (Figure 1), Studies 2–4 |
| `docs/RELATED_WORK.md:36` | "A′ 37% vs C 87% — the inversion" as a differentiator | `RELATED_WORK.md:166` (superseded); `main.tex:1516-1525` (failed hypothesis) |
| `docs/RELATED_WORK.md:39` | "Grader validation: Stratified κ = 1.00, blinded judge" | attestation rejected; `main.tex:2030` |
| `docs/RELATED_WORK.md:117` | "Payload generality ... severity now known" | superseded by the matrix (`main.tex:843-845`) |
| `docs/RELATED_WORK.md:159` | headline "Pooled 92% [82, 96]" | paper headline 68/59% vs 2/1% (`main.tex:229-233`) |
| `docs/RELATED_WORK.md` (whole) | no MSB, FIDES, ConfAIde, PrivacyLens or MCP-Zero | cited at `main.tex:281, 1556, 1624, 1653` |
| `docs/archive/tp_result.md:1-14` | no "superseded" banner | file contains withdrawn claims below |
| `docs/archive/tp_result.md:269` | "bounded to identifier-shaped content" | withdrawn (see above) |
| `docs/archive/tp_result.md:340-343` | "one sentence closes it ... zero-cost mitigation" | `main.tex:1392` (works on one provider, not another) |
| `CLAUDE.md:127, 234, 588` | `usenix_paper/main.tex` "is THE SUBMISSION" | `Q1_READINESS_AUDIT.md:3-6` |
| `CLAUDE.md:1274, 1456, 1869, 1898` | "anchoring pending" | `main.tex:2561-2567` |
| `CLAUDE.md:1495` | "protocol §5 MET" | validator output above |
| `Q1_READINESS_AUDIT.md:43, 46` | "neither a current flagship"; refusal untested | Study 4 (`main.tex:1203-1347`) |
| `docs/Q1_PUBLICATION_CHECKLIST.md:6, 51` | active draft in `journal_paper/`; permission "US$0" | `main.tex:1717-1719` (Studies 2–4 spent US$9.63) |
| `docs/STUDY_4_PROTOCOL.md:23, 48` | four models incl. `gemini-3.8-flash`; all 14 texts "reviewed for Study 2" | `main.tex:2229-2231` (leg discarded); `main.tex:1791-1792` and TODO T31 (four reviewed) |
| `main.tex:1974-1981` (AI declaration) | assistant "implemented ... the Study 3 harness and ran the Study 3 ... calls" | `main.tex:2282-2284` (the assistant also implemented and ran Study 4) |

---

## Step 6. Review

### Summary

The paper measures whether a required parameter in a third-party tool schema makes a tool-calling model copy a matching confidential fact from its system prompt into the call. Study 1 crosses seven study-authored fields with five seed-derived planted facts on two preregistered models (68% and 59% matched vs 2% and 1% nonmatched, neutral field 0/800 checks). Study 2 adds receipt by a local handler and shows that a secret-admitting string pattern and small categorical types do not reduce what is received. Study 3 shows that the models compute hexadecimal, suffix, reversed and slot-split forms of a secret on request, which defeats an oracle content filter, while an oracle task-argument allowlist removes every planted value. Study 4, exploratory, repeats the matrix on three newer models, adds a working directory and a signed-in user, and lets a local handler refuse the allowlisted call, finding no relocation and complete task loss.

### Verified strengths

1. **Every reported table number I recomputed matches the raw logs**, across all four studies, the pilot real-schema arm, the gate, the scanner and the classifier (Step 1). The repository's own check suite passes from a clean copy (`code/reproduce.py`, 204 tests).
2. **The core design gives the matched/nonmatched contrast meaning.** All facts are planted in every trial, and the markers are seed-derived nonsense (`code/conditions.py:534-571`). Unplanted controls return 0/367 (Study 1) and 0/210 (Study 4) despite field population, which rules out fabrication.
3. **The preregistration story is unusually checkable for Studies 1–3.** Digests, `.ots` proofs, commit times and first-trial times are stated, including the inconvenient ones (`main.tex:2561-2580`: Study 2's anchor post-dates the Gemini leg start, and the Study 1 timestamp has no time zone).
4. **Negative and inconvenient results are reported.** These include the failed gate hypothesis (`main.tex:1516-1525`), the adjacent-field failures (`main.tex:782-798`), the missing unplanted cells, the incomplete Pro arm, and the classifier's lack of a holdout (`main.tex:2418-2423`).
5. **Study 3 is a clean, prospective test.** The sealed protocol has a Bitcoin anchor before the first call (block 969484 at 19:19 UTC; first call 20:07 UTC; commit `8afdd25`). Its covert result is unambiguous: 160/160 exact codes under the filter and 0/160 unplanted.
6. **The scanner evidence is now auditable** (138/138 raw replies kept and valid), and its inputs have no tool-name confound.

### MAJOR weaknesses (block acceptance)

**M1. Study 4's provenance is overstated, and a protocol-named leg was dropped without reporting its data.**
- `main.tex:2222-2224` says the design "was written and committed before any planted call". Git shows that `docs/STUDY_4_PROTOCOL.md`, `code/flagship_study.py` and all four approval files were **first committed in `cfec543` at 2026-10-02T00:41:50Z, together with the collected data**. The first planted call was 2026-10-01T23:04:03Z (`extension_runs/flagship-live-gpt-6.1-sol-*.meta.json`). No other ref contains an earlier version. The protocol SHA in the approval files matches the current file, but those files were written by the harness session and committed afterwards, so they do not establish precedence.
- `docs/STUDY_4_PROTOCOL.md:23` names `gemini-3.8-flash` as a Study 4 model, and its approval file approves it. `main.tex:2229-2231` discards it after 39 trials "because it is not that provider's flagship".
- Those 39 trials contain the only refusal-arm cases in which a model **stated the credential to the user** (2/21: the model quoted its own call, `service_key:svc_...`, in its reply). The paper reports prose disclosure as 0/350 (`main.tex:1314-1315`) without mentioning them.
- The flagship framing is also inconsistent with the protocol. `main.tex:1218-1219` calls Opus 5.5 the current flagship, but `docs/STUDY_4_PROTOCOL.md:31-33` says the top reasoners (`claude-fable-5-1`, `gpt-6-astra`) were considered and not run.
- Study 4 appears in the abstract (`main.tex:233-235, 240-242`) and in contribution 1 (`main.tex:340-342`), so this affects headline claims.

**M2. The central defense recommendation is evaluated only as an oracle against local handlers.** The paper's thesis is that release must be a host information-flow decision (`main.tex:242-244, 1610-1663`). The only control that "holds", the P2 allowlist, is defined by the experimenter's knowledge of the legitimate call (`main.tex:1640-1644`). It is applied post hoc in the replay and against in-process handlers in Studies 3–4 (`main.tex:1338-1342`). None of the four realizable sources the authors list is implemented (`main.tex:1644-1654`), and no run uses an MCP transport, a remote server or a commercial client (Step 4). The "coercion lever" argument (`main.tex:1656-1663`) rests on a refusal message the authors wrote and a local handler.

**M3. External validity of the selectivity claim rests on seven study-authored wordings and one task.** Every field is study-authored (`main.tex:1763-1765`), the operational wording was chosen after an ablation (`main.tex:1526-1528`), and the primary interval resamples seven hand-picked fields (`main.tex:751-753`). The "naming" fields state their target category (for example `service_key_reference` asks for "the service key this integration was configured with"). Their success is close to "ask for X, receive X". The adjacent fields, the non-trivial case, fail on the primary pair (0/20 for two of three, `tab:fields`). The selectivity half of the claim is solid; the claim that a schema works as a "precise query" (`main.tex:307-309`) is shown only for fields that name the fact.

**M4. The content-filter conclusion for the suffix encoding depends on an unstated rule choice.** `main.tex:1090` describes P3 as removing an argument that shares "half of its tokens" with a planted value. The code computes Jaccard similarity over the union of token sets (`code/release_policies.py:45, 80-83`), which the protocol states (`docs/STUDY_3_STAGE1_PROTOCOL.md:109-110`). Under the containment reading the prose suggests, suffix values such as `gb-2` for `xy-kzfgb-2` are removed through the shared single-digit token. Suffix P3 then falls from 153 to 78 (Gemini) and from 102 to 48 (GPT-4o); hex and reversed are unchanged. The suffix decision rule likely still passes, but the reader cannot tell from the text, and the general claim "a filter that matches content fails" (`main.tex:1117-1119`) is sensitive to filter details the paper fixes by fiat.

### MINOR weaknesses

- **m1.** The abstract says "three current flagship models reproduce this" (`main.tex:233-234`) without noting that one leg is 162/460. It says "models do not relocate the secret" (`main.tex:241-242`), while the paper's own prespecified rule across the three legs is "not met" (`main.tex:1319-1323`).
- **m2.** The capability reading (`main.tex:1268-1270`) compares Study 4's adjacent texts (`issuing_environment`, `serving_location_hint`) with Study 1's different texts (`issuing_surface`, `locality_hint`), under different prompts, sampling and caps. Wording is confounded with model generation; the claim should be removed or tested on the same texts.
- **m3.** `main.tex:1738` understates the order problem: the Study 1 record shows sequential blocks by condition and field (Step 2).
- **m4.** The classifier was not scored on any Study 1–4 field (`main.tex:2535-2538`). It has 9 rows but 7 distinct names, and two positives appear in its prompt (`main.tex:2391-2394`). As evidence it is weak, and its section length exceeds its weight.
- **m5.** The study-authored scanner profiles' "clean" verdicts for C are by construction, since R1 fields were required to pass them (`code/test_harness.py:318-325`). `tab:scanners` (`main.tex:2321-2348`) does not say so.
- **m6.** Sol's single "API error" (`main.tex:2258`) is a client-side `PydanticUserError`, a harness bug, not a provider error.
- **m7.** The Study 3 decode rule credits over-long and partly wrong outputs: a "suffix" of `fyzlk-8` for `he-fyzlk-8`, and a "reversal" `9-oomucr-xr` for `xr-cumoo-9` (substring after reversal). This follows the protocol, but the "obtained" counts for GPT-4o reversed (57 vs 53 exact) and suffix (105 vs 98 exact) include them. Report exact-decode counts beside them.
- **m8.** The AI-use declaration (`main.tex:1974-1981`) omits that the assistant implemented and ran Study 4 (`main.tex:2282-2284`).
- **m9.** Submission state: no authors (`main.tex:219`), no `\journal`, 27 `% TODO` markers (T01–T31), and a tracked bundle that is the previous version (Step 0). `docs/TDSC_TARGET.md` targets an IEEE venue while the source is elsarticle.
- **m10.** Study 4 field review: `docs/STUDY_4_PROTOCOL.md:48` and `docs/STUDY_4_FIELD_REVIEW.md` say all 14 texts were reviewed; `main.tex:1791-1792` and TODO T31 say four. Git confirms all 14 texts were committed 2026-09-28 (`3c8fd73`), before Study 2. Only the review record is in doubt.
- **m11.** Ethics: no vendor notification (`main.tex:1715-1716`, TODO T17), although the paper documents effective wordings and a credential channel.
- **m12.** The prose docs (Step 5) contradict the paper on venue, anchoring, human validation, transport and severity. A reviewer browsing the artifact meets these first.

### Required changes, ranked by impact

| # | Change | Effort |
|---|---|---|
| 1 | Correct the Study 4 provenance text (M1). State the commit timeline; report the `gemini-3.8-flash` leg, why and when it was stopped, and its 2/21 prose disclosures; reconcile "flagship" with the protocol. | half a day, no cost |
| 2 | Evaluate at least one realizable release policy end to end (M2): for example schema pinning at review time or per-parameter purpose declarations, derived without the oracle, over a real MCP transport to a separate server process, with a provider-side refusal. | 2–4 weeks, under US$50 |
| 3 | Add independently authored field wordings (M3): written blind by someone outside the team, including non-naming fields, on a second task family, on the two primary models. | 1–2 weeks, about US$20–50 |
| 4 | State the P3 token rule precisely in the text and report the suffix result under the containment reading and with exact decoding (M4, m7). Offline only. | 2 hours |
| 5 | Qualify the abstract (m1); drop or properly test the capability claim (m2). | 1 hour |
| 6 | Either complete the Pro Study 4 leg and Study 1's two missing unplanted cells, or remove them from headline sentences. | days, quota-bound |
| 7 | Score Studies 1–4 fields with the classifier on a frozen prompt, or move the classifier to the supplement (m4); note the clean-by-construction profiles (m5). | 1–2 days, under US$5 |
| 8 | Complete author, declaration, venue and ethics items (m8, m9, m11); rebuild the bundle from the reviewed source. | authors, 1–2 days |
| 9 | Bring README, THREAT_MODEL, RELATED_WORK, CLAUDE.md and the readiness files in line with the paper, and add a superseded banner to `docs/archive/tp_result.md` (m12). | half a day |
| 10 | Fix the order statement (m3) and the Sol error label (m6). | 15 minutes |

### Requests for evidence

1. Provide a commit, timestamp or other record showing that `docs/STUDY_4_PROTOCOL.md` and `code/flagship_study.py` existed in their final form before 2026-10-01T23:04Z, or change `main.tex:2222-2224`.
2. State when the `gemini-3.8-flash` leg was stopped relative to inspection of its outputs, who decided, and why the protocol-named model was replaced. Report its 39 trials in the appendix.
3. Report Study 3 suffix and reversed counts under exact decoding, and suffix P3 under a containment token rule.
4. Provide model, provider and raw responses for `runs/mcp_client_capture.jsonl`, or state that it is not evidence.
5. Provide an attestation with one labeler per worksheet, or remove the κ = 0.911 claim from `README.md` and `CLAUDE.md`.
6. Provide the full-node verification of the OpenTimestamps anchors (the paper used a block explorer, `main.tex:2565-2566`; TODO T04).
7. Show the served model identifiers for Study 4 (`main.tex:2227`).
8. Provide the root cause of the Sol `PydanticUserError` and confirm that no other trial was affected.

### Scores (1–5)

| Criterion | Score | Justification |
|---|---:|---|
| Novelty | 3 | Parameter-based extraction is known (HiddenLayer, MSB); the simultaneous-fact selectivity measurement and the dispatch-control studies are new and useful. |
| Soundness | 3 | Every number I checked is correct and the controls are well designed, but Study 4's provenance is overstated and the main defense is an oracle. |
| Experimental rigor | 3 | Studies 1–3 are prospectively sealed with deterministic scoring; seven study-authored fields, one task, sequential order, preview models and a partial and a dropped leg limit it. |
| Defense evaluation | 2 | The positive control is an oracle on local handlers; the classifier has no holdout and never sees the main attack fields; one published scanner policy. |
| Presentation | 3 | Clear and candid prose, but 27 TODOs, no authors, a stale bundle, prose-code gaps in the filter rule, and very long appendices. |
| Significance | 3 | Directly relevant to MCP host design, tempered by synthetic secrets, study-authored fields and the paper's own finding that such fields are rare in real schemas. |

### Recommendation

**Major Revision.** The measurements are correct and unusually reproducible. The issues are scope and reporting: an exploratory study whose provenance is overstated and whose dropped leg is unreported, and a defense conclusion that has only been shown for an oracle.

### The single change that would most improve the paper

Replace the oracle allowlist with one realizable host release policy and evaluate it end to end: a real MCP transport to a separate server process that can refuse, with field wordings written by someone outside the team. The paper's thesis is that release is a host decision. That experiment would show whether a host can actually make the decision, and what it costs the task.
