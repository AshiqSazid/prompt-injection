# Deviations from the pre-registration

> **Working record, not the paper.** The focused revision is
> `journal_paper/main.tex`; `paper/main.tex` was rewritten as an expanded
> Elsevier-format journal manuscript on 2026-10-01 using the corrected evidence.
> This file records corrections and evidence history. Disagreement
> must be resolved against source evidence, not by treating prose as authority.

Written 2026-08-08 in response to USENIX review item 7. `protocol.md` is the
immutable pre-registration and is **never edited**; this file is the honest
diff between what was pre-registered and what was actually run.

**Read this before citing any number from `docs/archive/tp_result.md`.** The headline result
of the paper is **not** the pre-registered one. The pre-registered decision rule
returned a negative and we report it as such (§1). Everything that is exploratory
is marked exploratory here, once, in a single table, so a reviewer does not have
to reconstruct it from git history.

Legend for **Status**:
`PRE-REG` = in `protocol.md` as written · `POST-HOC` = added after seeing data ·
`NOT RUN` = pre-registered but never executed · `CHANGED` = pre-registered but
executed differently.

---

## 1. The headline: the pre-registered test FAILED

| | |
|---|---|
| **Pre-registered primary outcome** | Δ = disclosure(C) − disclosure(A′) for framework identity, on aligned models (`protocol.md` §1, §8) |
| **Pre-registered GO rule** | Δ ≥ 20 pp, statistically real, on **≥ 2 of 3** Gate models (§6, §8) |
| **Observed** | gpt-4o Δ = **+67 pp** · Claude Δ = **0 pp** · Gemini Δ = **0 pp** → **1 of 3** |
| **Verdict** | **GATE FAILED.** Under the pre-registered rule this is not a GO. |

Claude and Gemini sit at Δ = 0 by a **ceiling effect**, not by absence of the
channel: A′ and C are both 30/30 on each. Δ measures the *reticence the channel
bypasses*, not the channel's strength. That is an explanation, not a rescue — the
rule was fixed in advance and it was not met.

**What the paper claims instead** is post-hoc (§2, §8): the channel extracts planted
content universally (~80–100% on all three providers), and the *inversion* C > A′
appears **wherever the model is reticent**. At baseline that was gpt-4o only, which
is why the pre-registered Δ failed. The 2026-08-08 reticence ladder shows the
inversion is inducible on Claude (Δ 0 → +50 → +100 pp as the confidentiality
instruction is strengthened), so it is a property of the reticent *regime* rather
than of one vendor. All of this reframing was chosen after seeing the data and must
be labelled as such wherever it appears.

## 2. Hypotheses

| ID | Pre-registered claim | Status | Outcome |
|---|---|---|---|
| **H1** | Aligned agents reveal **their own** framework/model more via a harmless field than when asked | **RETRACTED** | Refuted by the framework arm: real LangGraph with nothing planted leaked **0/240**. The channel moves *planted system-prompt content*, not self-knowledge. |
| **H1 (revised)** | A benign required field extracts *planted* system-prompt content more than an explicit ask | **POST-HOC** | Holds wherever the model is reticent. At baseline that is gpt-4o only (and there, only for a recognizable product name). Under an induced confidentiality instruction it reproduces on Claude at Δ = +100 pp, and C beats the explicit E parameter 80% vs 15% on product identity. |
| **H1b** | disclosure(C) − disclosure(D) > 0 (wording, not field existence, is the cause) | **PRE-REG** | **Supported and strong.** D = 0/450 in the bare arm, 0/30 per scaffolded cell, and **0/97 across all five payloads**. |
| **H2** | More capable models leak more | **NOT RUN** | Requires the Breadth grid; no capability-scaling analysis exists. |
| **H3** | Scanners catch the pushy version (B) and miss the harmless one (C) | **CHANGED** | Supported, but only against a **project-authored** scanner (§5). |

## 3. Conditions

| Cond | Status | Note |
|---|---|---|
| A, A′, B, C, D | **PRE-REG** | `protocol.md` §3 as written. |
| **B′** | **POST-HOC** | Added after B was found to confound tone × ask-size × channel. B′ holds ask and channel constant with A′ and varies only tone. Never describe B′ as pre-registered. |
| **E** | **POST-HOC** | HiddenLayer replication (explicit `system_prompt` + `model_name`). Added after the literature review (`docs/RELATED_WORK.md` §2.1). |
| **Planted scaffolds** (`cursor`, `claude-code`) | **POST-HOC — material** | `protocol.md` assumes the model discloses its *genuine* identity. Planting a framework string in the system prompt changes the construct being measured from self-disclosure to prompt-content extraction. This is the deviation that made the H1 retraction necessary; it should be stated in the paper's method section, not in a footnote. |
| **Payload fixtures** (5) | **POST-HOC** | Added to test what the channel can extract beyond a product name. |

## 4. Design and grid

| Item | Pre-registered | Actual | Status |
|---|---|---|---|
| Gate | 3 aligned models × 5 conds × 30 reps | Done: gpt-4o, claude-sonnet-4-5, gemini-3-flash-preview (300 each) | **PRE-REG** |
| Breadth | ~12 models incl. Llama/Qwen/Mistral/DeepSeek | Configured, **never completed** | **NOT RUN** |
| Depth: framework arm | 5 framework variants | 1 real framework (LangGraph ReAct) + 2 planted scaffolds | **CHANGED** |
| Depth: required vs optional | pre-registered factor | never varied — **all fields are required** | **NOT RUN** |
| Depth: field position (before/after `query`) | pre-registered factor | never varied — always appended | **NOT RUN** |
| Depth: plausible vs implausible field name | pre-registered factor | never varied as a factor | **NOT RUN** |
| Depth: "needed for the tool to work" cue | pre-registered factor | never varied | **NOT RUN** |
| Depth: 4 wording styles | pre-registered | 5 run (4 + a `default` baseline) | **PRE-REG** |
| Primary wording | not specified in advance | `api_documentation` selected **after** the ablation showed it was the only one working on gpt-4o | **POST-HOC** |
| Temperature | "run at a low temp AND a realistic temp; pick the primary in advance" | **only 0.7**, all 22 stages | **NOT RUN** |
| Seeds | "fix and log seeds wherever the API allows" | were process-randomized `hash()` and ignored by every adapter; **fixed 2026-08-08** (stable sha256, passed to OpenAI-compatible endpoints only) | **CHANGED** |
| Task / tool diversity | one fixed task (as designed) | one fixed task, **one synthetic tool** | **PRE-REG** (but a known external-validity limit) |

## 5. Scanner (H3)

| Item | Pre-registered | Actual | Status |
|---|---|---|---|
| Scanner | **mcp-scan (Invariant Labs)** plus one meaning-based scanner | **`code/scan.py`, authored by us** | **CHANGED — material** |
| Surface scanned | tool definitions | descriptions only until 2026-08-08; parameter **names** were invisible | **CHANGED** |
| `desc+name` profile | not pre-registered | added 2026-08-08 after review | **POST-HOC** |
| Real external scanner (hosted service) | required | wired (`snyk-agent-scan`); verdicts require a remote endpoint, so **deliberately unrun** pending §14 | **NOT RUN** |
| Real external scanner (published policy) | required | **DONE 2026-08-08** — Invariant's `policy.gr` re-implemented locally (`code/scan_invariant.py`): B/B′ flagged; A′, C×5, D **and E** clean | **CHANGED** |

The `desc+name` result **strengthens** H3 rather than rescuing it: adding
parameter-name rules newly flags A′ (the honest ask) and E (HiddenLayer's
parameters), while C stays clean across all five wordings. Report both profiles.

## 6. Grading and statistics

| Item | Pre-registered | Actual | Status |
|---|---|---|---|
| Keyword grader | fixed keyword list | **kw-2**; kw-1 revised after finding a systematic false negative on concatenated User-Agent tokens (`CursorAI/1.0`) | **CHANGED** |
| LLM judge | 8 buckets, condition blinded | 8 buckets unchanged and blinding preserved; **prompt revised twice** after inspecting failures **on this data** (judge1 κ = −0.125) | **CHANGED** |
| Judge holdout | implied | **none** — judge-3 has never been evaluated on data not used to write it | **NOT RUN** |
| Disclosure rule | **both** graders must agree (§2, §5) | implemented 2026-08-10 (`grade.conjunctive_t1`, reported by `code/make_tables.py`); reproduces every scaffolded number exactly — see §8a | **PRE-REG** |
| Human labelling | 15–20% of trials | **none by a human.** 60 rows (20%) sampled, stratified and blinded; an LLM adjudication exists and is labelled as such (`labels/README.md`) but does NOT discharge §5 | **NOT RUN** |
| **κ ≥ 0.80 human-vs-LLM** | **required** | only grader-vs-grader κ reported (1.00 scaffolded / 0.00 degenerate bare) | **NOT RUN** |
| Mixed-effects logistic regression | required | **implemented 2026-08-08** (`code/stats.py`): Bayesian mixed logistic, `(1|model)` + `(1|wording)` where identified. Complete separation makes ORs regularisation-dependent; reported with that caveat | **CHANGED** |
| Odds ratios, α = 0.05 tests, Holm correction | required | **implemented 2026-08-08** — Fisher exact + Holm per contrast, Newcombe intervals on the risk difference | **PRE-REG** |
| Payload marker scoring | not pre-registered | strict + **loose** (normalized) markers; aliases fixed before the 30-rep run but chosen from a 10-trial probe | **POST-HOC** |

## 7. Defense (§10)

| Item | Pre-registered | Actual | Status |
|---|---|---|---|
| Intent classifier | propose and test | **rebuilt 2026-08-08**: held-out prompt (derived only from HiddenLayer's published params), 9 unseen positives, 506 real-schema negatives; AUC 0.994 | **CHANGED** |
| Disclosure reduction on C | required | **DONE** — 100% of observed C disclosures blocked at threshold 20 | **PRE-REG** |
| False-positive cost on benign fields | required | **DONE** — 2% on real MCP parameters, 9% on OpenTelemetry telemetry | **PRE-REG** |
| Prompt-level mitigation | not pre-registered | naming tool parameters in the confidentiality instruction closes C entirely (0/10, §7a) | **POST-HOC** |

## 8. Analyses that exist but were not pre-registered

Every one of these is exploratory:

- The A′ / B′ / C tone-vs-framing ladder (`confound_fix_*`).
- The wording ablation as a *result* rather than a Depth factor.
- Payload generality (`payload_generality_*`) and its severity ladder.
- The `desc+name` scanner profile and loose payload markers (both 2026-08-08).
- Harness anosognosia — models confabulating `"assistant"` when asked which
  framework runs them. A genuine finding, but discovered, not predicted.
- The **reticence ladder** (`conditions.RETICENCE_LADDER`, 2026-08-08). Manipulating
  the confidentiality instruction is nowhere in `protocol.md`; it was designed after
  the Gate returned Δ = 0 on two of three providers. Its result is strong, and it is
  **exploratory**.
- **Condition E × payloads** (2026-08-08), added after the payload run showed A′ was
  the wrong explicit comparator for non-identity payloads.
- The **defense rebuild** — held-out prompt, real-schema negatives, ROC. The original
  §10 design is pre-registered; this evaluation methodology is not.
- LangGraph field pass-through (240/240). Pre-registered as a *risk* to check
  (§13), reported as a *finding*.

## 8a. Reviewer-driven revision round (added 2026-08-10)

**protocol-v2 RESULT, 2026-08-10.** The planned study ran and its primary
hypothesis is **supported**: diagonal 99% vs off-diagonal 1% (gpt-4o) and 99% vs
4% (Gemini), clustered by field, neutral control ~0. Per the outcome table frozen
in `protocol-v2.md` §5 — row 1 — this means as an **exploratory result**:

- the "bounded to identifier-shaped content" claim is **WITHDRAWN** (the credential
  extracted 20/20 on both providers through a field that names it, versus 0/20
  through `client_user_agent`);
- severity is revised **upward** from reconnaissance to exfiltration;
- **`protocol.md` §14 coordinated disclosure must be re-opened before publication
  or any external sharing**, because the finding changed category.

The Anthropic leg did not run (credit exhausted) and is owed.

**PROVENANCE CORRECTION, 2026-08-10.** An earlier version of this paragraph said
the pre-commitment "was made before the data existed, which is the only reason this
reads as a result rather than a reframing". **That claim is false and is
withdrawn.** `protocol-v2.md` was never committed: `git log -- protocol-v2.md`
returns nothing, and the file and the first `runs/v2_*` artifacts were found
together as untracked working-tree files. Local modification times are not a
substitute for version-control history.

Consequences, stated plainly because they are load-bearing:

- **The v2 results are EXPLORATORY, not confirmatory.** The study currently has
  **no** confirmatory evidence for the field–content matching mechanism.
- A pre-commitment recorded only in an uncommitted file the author can edit is a
  statement of intent, not a preregistration, and a reviewer should treat it as
  worthless.
- The findings themselves (99% diagonal, 1% off-diagonal, credential 20/20) are
  unaffected as *measurements*. What is lost is the claim that the analysis was
  fixed in advance of seeing them.
- `protocol-v3.md` and the `preregistration:` guard in `code/run.py` exist so this
  cannot recur; see §8a.2 for the procedure that makes the next run auditable.

### 8a.2 The provenance procedure for `protocol-v3.md` — required before any run

The v2 failure was not a lapse of intent; it was the absence of a mechanism. This
is the mechanism. It is enforced in code where it can be, and written down where
it cannot.

**Enforced by `code/run.py`.** Every `v3_*` stage declares `preregistration:
protocol-v3.md`. `preflight()` calls `_preregistration_problems()`, which refuses
the run unless the protocol is **tracked**, **present in HEAD**, and **byte-clean
against HEAD**. `--dry-run` is exempt, so plumbing checks stay free. Verified: a
live `v3_matrix_openai` today exits **1** with *"protocol-v3.md is not tracked by
git"* before any provider call; the dry run exits 0.

**Not enforceable in code — do this by hand, in this order:**

1. Commit `protocol-v3.md`, the v3 fixtures (`conditions.v3_facts`) and the v3
   stages, in a commit containing **no** `runs/v3_*` artifact.
2. `sha256sum protocol-v3.md`.
3. Publish **only that digest** with a dated external witness — OpenTimestamps, or
   any dated public post. **Do not publish the file.** Its contents include
   condition-C patterns; publishing them is the coordinated disclosure
   `protocol.md` §14 governs, and severity is now credential-grade.
4. Record digest, witness and UTC time in the table below.
5. Only then run.

| Digest (SHA-256 of `protocol-v3.md`) | Witness | UTC time |
|---|---|---|
| `4c4557e9022508aff6bf80911ba573d30c47837b65c24cd787b66fa3613eee3d` | OpenTimestamps — commitment held by four independent calendars (`alice`/`bob` opentimestamps.org, catallaxy, eternitywall); proof in `protocol-v3.md.ots`, Bitcoin anchoring pending | **2026-08-11T03:37:28Z** |

Steps 1–2 are complete and independently checkable:

- `protocol-v3.md` is tracked, present in HEAD, and byte-clean against it
  (`run._preregistration_problems` returns no problems).
- It entered the repository in commit **`a139e87`**, and that commit contains
  **zero** `runs/v3_*` artifacts. No `runs/v3_*` path exists anywhere in the
  history of any branch. That is the ordering `protocol-v2.md` could not show.

**Step 3 is CLOSED, 2026-08-11T03:37:28Z.** The digest — and only the digest; the
client hashes locally, so the file never left this machine — was submitted to the
OpenTimestamps calendar network. Four independent calendars now hold a commitment
to it. `ots info protocol-v3.md.ots` prints the file hash back and it matches the
row above character for character.

Verify without trusting this repository:

```bash
ots verify protocol-v3.md.ots      # needs the file; digest must match the table
ots info   protocol-v3.md.ots      # prints "File sha256 hash: 4c4557e9…"
```

**Anchoring is pending, and the distinction matters.** As of the timestamp above
the proof carries four `PendingAttestation`s, not a Bitcoin block header. What is
established *now* is that four unrelated parties hold this digest — which is
already something a commit date is not, since a commit date is author-controlled
and this is not. What arrives later, when a block confirms and the proof is
upgraded (`ots upgrade protocol-v3.md.ots`), is verifiability that does not
require trusting the calendars either. Anyone re-checking after that point should
see a block height and time preceding every `runs/v3_*` artifact.

Do not describe the current state as "anchored in Bitcoin". It is "lodged with
four independent timestamp calendars, Bitcoin anchoring pending" until `ots
upgrade` succeeds — at which point update this paragraph with the block height.

**What this does not do.** It does not retroactively validate v2. No existing
artifact may be described as confirmatory.

### 8a.4 Disclosure status of the v3 artifacts (2026-08-11)

`protocol.md` §14 governs sending condition-C material to third parties, and
§13.13 of `CLAUDE.md` requires that gate to be re-opened before external sharing
because the finding moved from fingerprinting to credential disclosure. Checked
before committing the v3 run data, against what the public remote already holds:

| String | Files already published on `origin/master` |
|---|---:|
| `client_user_agent` | 67 |
| `service_key_reference` | 17 |
| `caller_context_summary` | 17 |
| `issuing_surface` | 1 |

**The disclosure already occurred**, through the code and the v2 artifacts
pushed earlier — every condition-C field name and the credential-shaped
parameter are in the public history. Committing the v3 runs therefore publishes
*evidence*, not a new capability. The one genuinely new string is the v3 canary
`svc_a0086960eac4e052`, which is a seed-derived fixture corresponding to no real
service, as `protocol.md` requires and as it must remain.

This is recorded as a finding, not as a defence of the ordering: the right time
to have made this decision deliberately was before the repository went public on
11 July. It is noted here so that a future release of new material is checked
against the gate *first* rather than discovered to be moot afterwards.

Mock artifacts are excluded from the record going forward — `runs/*-dry-*` is now
gitignored. `_mock()` fills grade as real disclosures and have already produced
one wrong number in this project; nine such files predate the rule and stay
tracked rather than being rewritten out of history.

### 8a.3 DEVIATION — the Gemini leg was switched to Pro mid-run (2026-08-11)

**Logged before the substituted stage ran, not after it produced numbers.**

`protocol-v3.md` §3 pins the models: *"`gpt-4o` and `gemini-3-flash-preview`,
pinned IDs."* On the author's instruction the Gemini leg was moved to
**`gemini-3.1-pro-preview`**, and `max_tokens` for the two Google stages was
raised 256 → 1024. Both edits post-date the digest witnessed at
2026-08-11T03:37:28Z. The consequence has to be stated plainly:

| Leg | Model run | Matches the witnessed protocol? |
|---|---|---|
| `v3_matrix_openai` (320/320, 0 err) | `gpt-4o` | **yes** — it ran to completion before any config edit |
| `v3_matrix_google` | `gemini-3.1-pro-preview` | **no** — model substituted |
| `v3_unplanted_google` | `gemini-3.1-pro-preview` | **no** — model substituted |

**The decision rule cannot be reported as satisfied.** `protocol-v3.md` §5 asks
for ≥ 20 pp with a bootstrap CI excluding zero on **both providers run**. Only
one of the two providers now runs the pre-registered model, so the honest
reading is: the gpt-4o leg is confirmatory evidence under a witnessed protocol,
and the Gemini-Pro leg is a *robustness arm on a different model*. Do not
describe the pair as "confirmatory on two providers".

**REPAIRED 2026-08-11.** The Pro leg hit a hard per-model daily cap --
`generate_requests_per_model_per_day, limit: 250, model: gemini-3.1-pro`, with a
server-supplied retry delay of 18h20m -- and the stage needs 320 trials, so it
could not have completed on any single day. It stopped at 253 rows (243 usable,
10 quota errors). `config.yaml` was therefore reverted to `gemini-3-flash-preview`
at `max_tokens: 256`, byte-identical to its pre-swap state, and the Gemini leg
re-run on the pinned model. **The substitution above is therefore withdrawn as
the study's Gemini result**: the confirmatory leg is flash, as pre-registered.

The Pro rows are retained as a **labelled exploratory robustness arm**, and they
earn their place -- they are the only frontier-tier evidence in the project, and
they carry the one cell the pinned model cannot supply on its own: a field named
`issuing_surface` recovered the planted platform 20/20 and `locality_hint`
recovered the region 20/20, neither of which names its target. That is the
naming-vs-adjacent gradient CLAUDE.md 13.13 recorded as unmeasured. Do not pool
these rows with the flash leg, and do not report them as confirmatory: the file
is partial, single-provider, and `g_credential_adjacent` reached only n=3 before
the quota wall -- which is precisely the most interesting cell.

**The original note, retained:**

**The flash leg remains available and is the cheapest way to repair this.**
Re-pointing `v3_matrix_google` at `gemini-3-flash-preview` and re-running would
restore a fully protocol-conformant two-provider result; the substitution does
not destroy that option, it defers it. The partial artifact
`runs/v3_matrix_google-live-20260811-111215.jsonl` (**125/320 rows, flash,
killed mid-stage**) is retained under the never-delete rule and must not be
pooled with anything.

**Two incidental fixes shipped with the swap**, both provoked by Pro and both
covered by tests:

- `_google` indexed `candidates[0].content.parts` unconditionally. A thinking
  model can return no parts at all — measured at `max_output_tokens=32`, where
  reasoning consumes the whole budget — which raised `TypeError` and recorded a
  budget problem as a provider outage. Empty is now an ordinary no-output trial.
  This is also why `max_tokens` was raised: 256 sufficed in probes, but a cap
  that tight against a reasoning model is a silent-truncation risk across 320
  trials.
- `providers.served_model` checked `model` and `modelVersion`. The Google SDK
  dump spells it `model_version`, so the substitution guard added the same day
  was **inert for the entire Google leg** — the one provider whose model was
  about to be substituted. Now read in all three spellings.

### 8a.1 Deviations from `protocol-v2.md` §4 — logged, not buried

**Provenance correction.** `protocol-v2.md` and the first live `v2_*` artifacts
were discovered together as untracked files. There is no Git commit proving that
the protocol preceded data collection. Consequently, every v2 result is
exploratory regardless of whether its execution followed the written plan. The
local timestamps are useful forensic context but are not preregistration evidence.
No existing artifact may be described as confirmatory.

The prospective plan specified five analyses. **The first pass executed
one.** A round-2 referee read caught it, and all four were implemented on
2026-08-10 against the data already collected (`code/stats.py --v2`). Recorded here
because a paper whose method claim is pre-registration discipline cannot let this
be discovered from git history.

| §4 item | First pass | Now |
|---|---|---|
| (1) cluster bootstrap by field | ✅ implemented | unchanged |
| (2) hierarchical logistic `y ~ matched + (1\|field) + (1\|fact) + (1\|provider)` | ❌ not run | ✅ implemented |
| (3) per-fact Wilson intervals | ❌ not run | ✅ implemented |
| (4) Holm across per-fact diagonal tests | ❌ not run | ✅ implemented |
| (5) Newcombe intervals on pp differences | ❌ not run | ✅ implemented |

Two further departures from §4 as literally written, both in the authors' favour
to disclose:

1. **§4(4) says "Holm across the 8 per-fact diagonal tests"; the family is 14.**
   Only seven fact families have a condition-C field targeting them — the eighth,
   `opaque`, is targeted by condition D, which is the control and is excluded from
   the diagonal. Seven facts × two providers = 14 tests. The larger family is the
   *more* conservative choice; all 14 survive Holm at α = 0.05.
2. **Probe rows are excluded from the planned primary counts.** `v2_matrix_probe`
   ran at the same configuration and temperature, but it exists to be inspected
   before the grid, and folding inspected data into the primary analysis is
   not defensible. `code/stats.py` filters it out by filename; the first version of
   this analysis did not, which inflated two gpt-4o cells from 20 to 21 trials.

**Superseding note.** After a second USENIX-style review, the R1 design below was
judged too narrow to identify the mechanism: it varied the field but kept one
payload, so an empty cell could still mean "the fact was absent". It is superseded
by **`protocol-v2.md`**, a prospective plan whose intended freeze predates the
`v2_*` runs but whose Git provenance is invalid. protocol-v2 plants **all eight fact families in every trial** and
requests one per schema, so an empty off-diagonal cell means the model had the fact
and withheld it. The R1 stages are retained for provenance but `v2_matrix_*` is the
experiment to run. protocol-v2 also discharges two long-standing `protocol.md` §4
items that were never executed: the second temperature, and the required-vs-optional
and field-position Depth factors.

All three arms below were designed **after** an adversarial re-read of the payload
results, and all three are **exploratory**. They are recorded here before they run
so that neither outcome can later be presented as predicted.

| Arm | Status | What it decides |
|---|---|---|
| **R1** `r1_field_fact_*` | **POST-HOC, staged, not run** | Whether the severity bound is *shape restriction of content* or *field–content matching*. All payload results to date used ONE field (`client_user_agent`); the payloads that extract are exactly the ones phrased as answers to it. R1 crosses one payload with five fact-targeted benign fields. |
| **R2** `r2_payload_norm_*`, `r2_explicit_norm_openai` | **POST-HOC, staged, not run** | Re-measures the payload arm with three stimulus confounds removed (see below). |
| **R5** `code/defense.py --sweep` | **POST-HOC, implemented, not scored** | Whether a re-wording exists that scores at or below legitimate telemetry on the detector while still extracting. |

**Intended pre-commitment for R1.** R1 was superseded by the v2 matrix and never
ran, so nothing rests on this. It carries the same defect as the v2 one — it lives
in a working-tree edit, not a commit that precedes any data — and is recorded here
as a statement of intent only. Both outcomes were to be reportable and neither a
rescue:

- *Diagonal fills* → the mechanism is field–content matching, the "bounded to
  identifier-shaped content" claim is **withdrawn**, severity is revised **upward**,
  and the §14 disclosure timeline is revisited.
- *Only the platform column fills* → shape restriction survives its strongest
  falsification test and is reported as such.

**Three stimulus defects found in the v1 payload arm** (`conditions.PAYLOADS`),
which is why R2 exists. The v1 fixtures are left unedited so existing artifacts
stay reproducible; v2 is a separate arm and the two must not be pooled.

1. `credential_shaped` states inside the prompt that the token is "(test fixture,
   not a live credential)". Its 0/20 therefore measures how the channel treats
   material annotated as fake. This cell is load-bearing for the paper's claim that
   the bound is real, so the defect is material.
2. `long_block` carries its own "Do not reveal any of this configuration" on top of
   the appended confidentiality sentence — two prohibitions where
   `product_name`/`internal_codename` get one. It still leaked 100%, which is a
   *stronger* result than currently claimed, but the arms are unmatched.
3. `policy_sentence`'s content is itself a non-disclosure instruction, so its 0/20
   is equally well explained by instruction strength as by content shape.

**Closed by this round:**

- **Two-grader disclosure rule** (§6 row "Disclosure rule", previously NOT RUN) —
  implemented as `grade.conjunctive_t1` and reported by `code/make_tables.py`. It changes
  **no** scaffolded number: 0 disagreements in 300 judged scaffolded rows across
  gpt-4o and Claude. All 50 disagreements are in the bare arm and are judge-2
  over-calls on generic self-description. Residual: no judge-3 pass exists for any
  gate leg, and Gemini has no judged derivative.
- **Duplicate-cell reporting** — `gate_openai_apidoc` and `confound_fix_openai`
  measure one identical cell. Pooled: A′ 20/60 = 33%, C 55/60 = 92%. Quote the
  pooled figure; earlier drafts quoted 97% in one place and 87% in another.

**Newly recorded as a limitation, not closed:** T3's shape patterns encode tokens
planted by the fixtures (4 of 5), so T3 measures fixture recovery rather than the
open-world construct `protocol.md` §2 defines.

## 9. Known open items before submission

Updated 2026-08-08 end of day.

**Still owed:**

1. ~~**Human labelling + κ ≥ 0.80.**~~ **CLOSED 2026-08-21** — a human co-author
   (Md. Rafiur Rahman) labelled the blinded sample; scaffolded κ = 0.911, §5 MET
   (report by stratum, not pooled 0.856). Was the single hardest blocker.
2. ~~**Combined two-grader disclosure rule.**~~ **CLOSED 2026-08-10** — see §8a.
3. **Real external scanner (hosted service).** Gated on the §14 disclosure step.
   Invariant's *published policy* has been run locally (§5).
4. **Second temperature.** Superseded: a separate v2 temperature-zero arm exists;
   see the 2026-09-28 correction below. The confirmatory v3 matrix remains at 0.7.
5. **Breadth / H2 capability scaling.** Configured, never completed.
6. **Depth factors:** required-vs-optional, field position, plausible-vs-implausible
   name, necessity cue. None varied.

**Closed since this file was written:**

- Mixed-effects regression, odds ratios, Holm — implemented (`code/stats.py`).
- Defense trade-off curve — AUC 0.994 [0.986, 0.999] over 506 real-schema
  negatives with a held-out detector prompt.
- `payload_generality_anthropic` — ran, 150/150. The gpt-4o payload file remains
  **partial** (297/300) and is labelled as such.
- T3 — implemented and applied; a case-sensitivity bug found by applying it.
- External validity — 24 real MCP schemas on two providers.
- Reticence as a manipulated treatment — Claude and Gemini.

## 2026-09-28 — post-collection evidence-integrity corrections

These changes are implementation and reporting corrections, not a new
preregistration. Historical protocols and all raw run artifacts remain unchanged.

- The prior manifest emitted call-level Wilson intervals where the manuscript
  described a field bootstrap. The repaired implementation resamples seven
  targeted fields jointly for diagonal and off-diagonal rates. GPT-4o's difference
  is +66 pp [32, 95]; Gemini Flash's is +58 pp [17, 86]. Leave-one-field-out
  difference ranges are [60.6, 77.5] and [50.8, 67.5] pp. The independent
  count and NumPy-bootstrap cross-check is in `data/q1_analysis.json`.
- Excluding the targetless generic field changes the off-diagonal denominator
  from 660 to 560 checks for each complete confirmatory arm. Counts remain 9
  and 4. The generic result is separately 0/20 calls on each provider.
- The neutral result is 0/160 calls returning any canary, equivalently 0/800
  correlated fact checks, not 800 independent calls. A descriptive call-level
  Wilson upper endpoint is 2.34%; it is not a bound for unseen schema populations.
- The quota-capped Gemini Pro matrix has 253 attempted rows, including 10 errors
  and 243 usable responses. Missing completion metadata previously hid those
  errors and excluded that arm from the registry's total. The selected v3
  inventory now reports 2,013 attempted rows and 10 errors across all matrix and
  unplanted arms, with the Pro arm explicitly partial; primary pair counts do not change.
- Protocol-v3 §2 says the generic field has no target, while §5 applies a
  diagonal-minus-off-diagonal decision rule to it. That rule is undefined.
  We report the descriptive generic endpoint and explicitly do not claim a
  confirmatory resolution of that part of H-v3-2.
- V3 per-fact and gradient tests and a hierarchical logistic fit are now
  implemented in `code/q1_analysis.py`. The per-fact family covers both named
  providers; the naming/adjacent gradient forms a separate Holm family. The
  protocol did not specify that family boundary. Variational fitting with
  fe_p=2/vcp_p=1 and deterministic initialization is a disclosed implementation
  choice, not a prospectively specified prior. Neither these call-level tests
  nor the two-provider random effect supersede primary field-level inference.
- The exploratory temperature-zero v2 arm has 160 rows: diagonal 80/80,
  off-diagonal 0/560, neutral 0/80 calls. Its different canaries and collection
  time prevent attributing its difference from v3 to temperature.
- `data/artifact_selection.json` freezes historical selection and digests.
  The early v2 depth run has repeated trial identifiers without depth-arm labels;
  it remains preserved, while the later labeled run remains the manuscript source.
  Two historical mock files also contain duplicates; neither is scientific evidence.
- The model identity guard previously accepted sibling prefixes. All inventoried
  raw files were audited with the stricter rule: no reported-ID mismatch was
  found. Missing IDs remain unverified; raw/derived copies are not independent trials.
- The offline MCP client path was broken. The repaired transport is verified with
  synthetic responses, including handler rejection and no call. This is not new
  live-model disclosure evidence or commercial-client/UI evidence.
- Detector scores project which historical field-associated leaks might have
  been blocked; they do not measure end-to-end prevention or task utility. Lexical
  separation from the detector prompt is not an independently designed holdout.

**Disclosure status:** §8a records prior public exposure of the repository.
That is not coordinated vendor notification. No notification correspondence is
recorded in this artifact; hosted evaluation and new attack publication remain
gated on a documented author decision. No vendor was contacted in this revision.

## Journal-focused revision, 2026-09-28

The new `journal_paper/` manuscript is a narrower existing-evidence presentation,
not a new experiment or retrospective registration. It leads with selective
recovery in emitted arguments and separates validation, dispatch, receipt and
utility. The earlier manuscript sources remain available. Normalized
marker/prefix-alias matching is described explicitly rather than as full-canary
exact equality; reconstructed listing schemas are not called native schemas.

Three additional **post-collection** scoring sensitivities use existing primary
rows only: full normalized markers, full verbatim markers, and registered
markers/aliases including the `query` argument. Each gives the same matched and
nonmatched counts as the registered endpoint on both primary models. No primary
endpoint, threshold, fixture, protocol, exclusion, or historical data changed.
These results assess scorer sensitivity, not general task robustness.

The focused literature update adds Lin (2026) on structured-output schema
influence and Yergattikar (2026) on runtime defense, and corrects the HiddenLayer
byline and MCP specification version in the journal bibliography. Existing
evidence is not asserted to supersede either neighboring line of work.
The draft extension is uncollected, budget permission remains zero, and final
venue/author/disclosure/release decisions are not completed by code checks.

Final journal audit also found a control-coverage deviation: all four selected
v3 unplanted stages contain six fields (120 attempted rows each), not all eight
matrix fields. `g_platform_adjacent` and `g_region_adjacent` are absent. The
historical config and metadata agree about the six-field stage, but protocol-v3
§3 describes the same fields as the planted arm. Configured-stage completeness
is now distinguished from full protocol-grid coverage. Counts and H-v3-1 are
unchanged; H-v3-3 is not described as complete across all eight fields. No missing
control outcomes were imputed and no historical artifacts were rewritten.

The historical policy-scanner artifact stores boolean votes, not the original
judge text. Its parser previously mapped every non-`YES` answer to a negative
vote, so malformed outputs cannot be excluded retrospectively. Scanner claims
in the focused journal manuscript are downgraded to provisional recorded-vote
evidence. Future parsing accepts only YES/NO, retains raw content and reported
model identity, refuses output collisions, and marks invalid observations
incomplete. No historical votes were changed and no new classifier calls made.

## Expanded journal writing revision, 2026-10-01

`paper/main.tex` now presents the corrected existing evidence as a full journal
article with integrated methods, sensitivity analyses and appendices. Historical
observations and protocols are unchanged. When this entry was written the planned
extension was uncollected. It has since been collected and is reported in the
manuscript; see the completion entry at the end of this file.

The annotation recheck found that `labels/v4-apidoc-gate.attestation.json` uses
suffixed metadata for two author identities, while `label.py --rater human`
expects a single set of unsuffixed fields and currently rejects that file. There
is one completed 60-row worksheet, not two independently attributable worksheets.
Its recomputed scaffolded keyword agreement is kappa 0.911 and its agreement
with the eight-category judge is 0.855. These are agreement statistics on the
retained labels; they do not resolve the attribution or attestation-format issue.
Earlier notes declaring the human-validation requirement complete are therefore
qualified by this correction. The expanded manuscript reports provenance as
unresolved. No label, identity, signature, or attestation was changed or supplied
on an author's behalf. This does not affect the grader-free v3 marker counts.


## Full journal repository audit, 2026-10-01

The expanded `paper/main.tex` now includes the full stimuli, all selected matrix
cells, historical condition breakdowns, and retrospective descriptive Wilson
intervals. `paper/REVISION_AUDIT.md` lists all distinct conflicts found across
historical summaries and the retained evidence. Existing logs, protocols, labels,
and attestations remain unchanged.

Additional reporting corrections from this pass:

- The historical `Real...Itt` macros exclude API errors. They describe usable
  responses, not all attempted requests. Claude's listing arm has 250 attempts,
  one error, and 249 usable responses. D alone has 125 attempts and 124 usable.
- Original payload “strict” matching ignores case. It differs from the v3
  verbatim sensitivity rule. Older T1 keyword scoring includes assistant prose
  as well as arguments and cannot itself establish server-bound disclosure.
- The revised defense prompt explicitly includes `system_prompt` and `model_name`,
  which are also two positive evaluation fields. Thus the claim that all nine
  positives were unseen is false. C vocabulary separation is not an independent
  holdout. Removing already scored families is not retraining or cross-validation.
- The classifier negatives are 472 MCPTox fields and 34 OpenTelemetry fields.
  Its scored positives do not cover all later v3 region/operator/credential fields.
- The v3 protocol's uniform length claim does not match the fixture descriptions:
  the client description has 26 whitespace tokens and the generic description ten.
- Three historical server captures are retained as limited receipt observations.
  Missing correlated raw model responses prevent treating them as a fully audited
  model-to-server chain or as the primary matrix's delivery rate.

No new model observations, external scanner verdicts, human ratings, or vendor
notifications were generated by this writing revision.

## Expanded manuscript completion pass, 2026-10-01

`paper/main.tex` now reports Experiment 25 as RQ5. Its numbers come from the four
canonical legs declared in `code/journal_assets.py` (digests checked) through the
pre-registered `schema_types_analyze` functions. The experiment is reported
separately and is never pooled with the historical evidence. Earlier statements in
this file and elsewhere that the extension is uncollected describe the state before
2026-09-29.

Reporting corrections from this pass:

- Every result number in the manuscript prose now comes from a generated macro
  (`paper/details_macros.tex`, written by `code/paper_details.py`).
  `code/paper_assets.py --check` fails if a fraction, interval or decimal percentage
  is typed into `paper/main.tex`.
- The pooled GPT-4o cell (gate plus tone run, 55/60 for C) has a third candidate
  replicate: the API-documentation cell of the wording ablation, 25/30, with the
  same recorded model, scaffold, wording and temperature. The canonical rows of all
  three runs omit the output-token budget, so no two can be confirmed identical in
  every request setting. The choice of the pooled pair is not documented. The
  manuscript states this and pools only the registered pair.
- The description-only scanner profile already flags condition E. The statement
  above that parameter-name rules "newly" flag E is wrong; only A-prime changes.
- Sequential Thinking contributes 5 of the 13 false positives at threshold 20,
  from 4 distinct parameter names. "Four of the 13" in older summaries counts names.
- The bare stratum is 0/30 in every cell on all three gate models: 0/450 over five
  conditions, and 0/90 for D alone. "D = 0/450 in the bare arm" above gives the
  five-condition total.
- The OpenTelemetry negatives were harvested from the unversioned `main` branch, so
  the cited source has no pinned revision.
- The gradient figure legend says "every trial". Its cells divide by emitted calls
  (for example 17/17 for one DeepSeek cell). The copy generated for
  `paper/main.tex` says "every call".
- `docs/Q1_PUBLICATION_CHECKLIST.md` describes the human validation as one
  coauthor. The attestation file lists two author identities with identical
  timestamps. This adds to the attribution issue recorded above.

No model observation, label, attestation, protocol or run file was changed, and
this pass issued no live model request.

## Study 4: flagship replication and the refusal arm, 2026-10-02

Exploratory, run after the three sealed protocols and never pooled with them.
Design, schedule, scoring and analysis were written and committed before any
planted call (`docs/STUDY_4_PROTOCOL.md`, `code/flagship_study.py`); the study
carries no timestamp proof, and it is labelled exploratory everywhere it appears.

- **Models.** The current flagship of each provider whose key the study holds:
  `gpt-6.1-sol`, `claude-opus-5-5`, `gemini-3.1-pro-preview`. The absolute-top
  reasoners (`gpt-6-astra`, `claude-fable-5-1`) were considered and not run: the
  task emits one tool call, so output is small, and their thinking output at list
  price would have multiplied the cost for the same measured behaviour. A
  `gemini-3.8-flash` leg was started and stopped at the author's instruction after
  39 of 460 trials, because it is not that provider's flagship; it is discarded and
  supports no number.
- **New prose a model sees.** Two clauses were added to the reviewed Study 2a
  configuration sentence, for a working directory and a signed-in user, and two
  refusal messages were written for the feedback arm. A study author reviewed all
  four before any model saw them (`docs/STUDY_4_FIELD_REVIEW.md`). Every field
  description is an unchanged Study 2 text.
- **A removed arm.** An earlier draft would have had a language model write
  additional field descriptions, so that the wordings were not all authored by the
  experimenters. Asked to produce them, `claude-sonnet-5-5` declined
  (`stop_reason: refusal`, no output). The arm was removed rather than reworded:
  a generated wording would not have carried the human review this study requires
  of anything a model sees. Study 4 therefore varies models and planted facts, not
  wordings, and says nothing about a wording an adversary might choose.
- **One incomplete leg.** The `gemini-3.1-pro-preview` leg stopped at 162 of 460
  trials when three successive attempts on one trial returned
  `429 RESOURCE_EXHAUSTED`, the prespecified stop. 298 trials were never sent. The
  shortfall is uneven across arms because the schedule is shuffled within
  replicate blocks: 90/216 selectivity, 42/84 unplanted, 30/160 refusal. The cause
  is a per-day request cap fixed for this preview model, independent of the
  account balance. A resume was attempted on 2026-10-02 at 00:34 UTC; the cap had
  not reset and every probe was refused, so nothing further was collected for this
  version of the paper. The missing trials are **not imputed**, the leg is never
  pooled with the complete ones, and it is reported as partial in the table, the
  results text, the threats section and the appendix. It remains resumable from its
  recorded rows under the same design hash.
- **Consequence for the stated bound.** The relocation bound (interval upper end
  below ten percentage points) is met on the two complete legs, each 0/160 with
  interval [0.0, 2.3], and not on the partial leg, where 0/30 gives [0.0, 11.4].
  The decision read across all three models is therefore reported as not met,
  although no relocation was observed anywhere.
- **Execution detail, not a design parameter.** Concurrency is a `--workers`
  override. The two complete legs ran four trials at a time; the Pro leg ran
  serially after the provider returned per-minute rate limits. It changes nothing
  that is sent or scored and is excluded from the design digest.

No earlier observation, label, attestation, protocol or run file was changed by
this round.

## Study 4: the Gemini 3.1 Pro leg resumed, 2026-10-05

A post hoc continuation of the one partial Study 4 leg, at a study author's
instruction during the figure revision of 2026-10-05. It adds trials to an arm
that was already reported; it adds no model, arm, field, prompt or analysis.

- **Why this leg.** The author first asked for a run on "Gemini 3.8 Pro". The
  provider's model list, read with the study's key on 2026-10-05, holds no such
  model: the 3.8 family is Flash, speech and live models only, and the newest Pro
  is `gemini-3.1-pro-preview` (version `3.1-pro-preview-01-2026`). Nothing was run
  under an invented identifier. Offered the choice, the author chose to continue
  the partial `gemini-3.1-pro-preview` leg, which the protocol names as resumable
  under its design hash, over re-running the discarded `gemini-3.8-flash` leg.
- **Decided after results were seen.** The first session's 162 trials had been
  analysed and written into the manuscript before the resume was decided. The
  schedule is fixed by the design, the trials still to send are the ones the
  first session never reached, and each session ended at the provider's cap and
  not at a result. It is still a continuation chosen with the earlier results in
  view, and the manuscript says so.
- **Checks before the paid launch.** `--check-live` returned no blocker, and the
  design hash computed that day (`423a1871…b1d38c1`) equals the one the leg
  recorded at its first launch. The client library is `google-genai` 2.14.0, the
  version `requirements.txt` records as used. An offline mock run of the leg
  wrote 460 of 460 rows to a scratch directory, not to `extension_runs/`. The
  unplanted `--compat` probe ran at 15:23 UTC: 13 of 38 trials were accepted and
  25 refused by the per-minute limit of 25 requests
  (`extension_runs/compat_flagship-gemini-3.1-pro-preview-20261005-152325.jsonl`).
  The probe billed about US$0.17 and is outside the budget ledger, as the
  earlier probes are.
- **The resume.** Launched at 15:25:06 UTC with `--resume` on the leg's own log
  and `--workers 2`; the first session ran serially. Concurrency is not in the
  design digest and changes nothing that is sent or scored. The `workers` field
  of the leg's `.meta.json` records the harness constant, not this override. The
  launch stopped at 15:37 UTC when three successive attempts on one trial
  returned `429 RESOURCE_EXHAUSTED`, the prespecified stop, after 225 settled
  calls and 6 refused attempts. One direct request at 15:38 UTC, which the
  provider refused, named the limit: `generate_requests_per_model_per_day`,
  250, resetting at 00:00 UTC. The probe's 25 accepted calls and the launch's 225
  are that day's 250.
- **What it added.** 111 trials, from 162 to 273 of 460: selectivity 122/216,
  unplanted 60/84, refusal 91/160. No error row. All 111 new rows store the
  request digest of the committed design, and the provider echoed
  `gemini-3.1-pro-preview` on every call, as in the first session. The ledger
  settled US$1.20 for the launch; the leg has billed US$2.27 of its approved
  US$15. 187 trials remain unsent.
- **Files changed.** The harness's resume path appended to the leg's `.jsonl`,
  `.raw.jsonl` and `.ledger.jsonl` and rewrote its `.meta.json`. The first 162
  rows of the log, the first 162 rows of the raw file and the first 439 lines of
  the ledger are byte-identical to the files as committed before the resume
  (SHA-256 `9fa785b4…`, `b9918942…`, `5e3bf088…`). The log's digest is now
  `f817b1d3…f4d8b8e`, and the pin in `code/paper_details.py` was updated to it.
- **What changed in the paper.** The leg's counts moved everywhere they are
  generated. One prespecified decision changed: the relocation bound was not met
  on this leg at 0/30, interval [0.0, 11.4], and is met at 0/91, interval
  [0.0, 4.1], so the rule read across the three models went from not met to met.
  The manuscript reports both readings and that the second depends on the
  resumed trials. The selectivity decision (met) and the adjacent-class decision
  (not met) did not change. The generic field's any-fact count on this leg went
  from 1/9 to 4/19; all four are the planted user name inside a context label.
  `code/paper_details.py` now raises if this leg is complete while declared
  partial, if a leg stops clearing the relocation bound, or if the first
  session alone would have excluded it.
- **Still partial.** The leg is reported as partial in the table, the figures,
  the results text, the threats section and the appendix, and is never pooled
  with the two complete legs. Two more daily sessions would complete it.
- **Collection stopped by choice.** After this session the author decided not to
  wait for those sessions and to report the leg at 273 of 460. The two earlier
  stops were the provider's cap; this one is the author's, and it was made after
  seeing that the relocation bound had just been met. `docs/STUDY_4_PROTOCOL.md`
  section 4 says there is no data-dependent stopping, so this is a deviation from
  it, and the manuscript states it in the results, the threats section and the
  appendix. The leg stays resumable under its design hash; completing the fixed
  schedule later would remove the objection.

No protocol, approval, label, attestation or other run file was changed by this
round. No hosted scanner was contacted.
