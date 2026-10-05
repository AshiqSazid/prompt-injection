# schema-disclosure-gap

**Manuscript (2026-10-04):** [paper/main.tex](paper/main.tex) is the journal
manuscript, in Elsevier `elsarticle` format, with the pilot studies in
[paper/supplement.tex](paper/supplement.tex). It reports four studies: the
fact-by-field matrix (Study 1, preregistered), schema constraints and typed
fields at handler receipt (Study 2, preregistered, formerly "Experiment 25"),
encodings and typed slots against a dispatch filter (Study 3, preregistered), and
an exploratory replication on three newer models with a refusing tool (Study 4).
Build it with `make -C paper`; verify with `make -C paper check`. See
[the manuscript notes](paper/README.md). **The project is not submission-ready:**
authors, declarations and the disclosure decision remain open; start with
[Q1_READINESS_AUDIT.md](Q1_READINESS_AUDIT.md). The source now targets the
**Journal of Information Security and Applications** (`\journal{...}` in
`paper/main.tex`, elsarticle format); Computers & Security was dropped on
2026-10-05 because it excludes LLM-security work;
the older [docs/TDSC_TARGET.md](docs/TDSC_TARGET.md) IEEE note is superseded and
does not match the current source.

Offline reproduction: `python3.12 -m venv .venv-q1`,
`.venv-q1/bin/python -m pip install -r requirements-analysis.lock`, then
`.venv-q1/bin/python code/reproduce.py`.
No paid model calls are needed for these checks.

[journal_paper/](journal_paper/README.md) is an older, shorter IEEE draft and
[usenix_paper/](usenix_paper/) an older conference version; neither reflects
Studies 3 and 4. `code/submission_check.py` intentionally fails until author,
venue, and release decisions are confirmed; passing analysis tests does not clear
those gates.

A measurement study of **required tool-schema parameters as an exfiltration
channel** in tool-calling LLMs. A malicious tool publisher controls the JSON
Schema an agent fills in, and sees every argument the agent sends during an
ordinary tool call. No imperative attack text is needed; the planted material
is explicitly confidential. API emissions are not, by themselves, server receipts.

The two pilot-era findings below are kept for orientation. The manuscript leads
with selective recovery and adds Studies 2 to 4; cite numbers from
`paper/main.tex`, not from this page.

**Scanner observation.** Invariant Labs' published tool-poisoning policy
(`mcp-scan==0.3.39`), re-implemented locally with its own model, flags
command-phrased injections but rates clean both our benign parameter *and* the
published explicit attack whose parameters are literally named `system_prompt`
and `model_name`, and all 30 added fields of Studies 1 to 4. Those 30 were each
scanned on a synthetic order tool only; the email tool and the native schemas
were not scanned. The 2026-10-04 re-run keeps every reply
(`results/scan-invariant-policy-raw-20261004-s4.json`, 168 replies over 56
declarations), all of them an exact YES or NO, and supersedes the earlier
boolean-only record. The
policy asks whether a declaration contains an injection. This is one published
policy, not the vendor's hosted service, and it does not show that every
injection-oriented defense will miss these fields.

**Disclosure is selected by the parameter, not wholesale.** Plant five
seed-derived canaries in one system prompt, have each schema request exactly one,
and the requested canary comes back far more often than the four it did not ask
for.

| Model | Status | Diagonal | Off-diagonal | Neutral control (fact checks) |
|---|---|---:|---:|---:|
| `gpt-4o` | **confirmatory** | **68%** [36, 96] | 2% [0, 4] | **0/800** |
| `gemini-3-flash-preview` | **confirmatory** | **59%** [20, 87] | 1% [0, 2] | **0/800** |
| `claude-sonnet-4-5`, `deepseek-v4-flash`, `gemini-3.1-pro` | post-hoc | 61–98% | 0–5% | 0 |

Each confirmatory neutral arm contains **160 calls**, with five correlated
canary checks per call. They are one identical request sent with the same 20
seeds under each of the eight field labels, so they are far from 160
independent observations. Paired-bootstrap differences are +66 pp [32, 95] and
+58 pp [17, 86] over seven hand-selected fields. These are post-collection
implementation corrections, not a newly preregistered analysis.

Confirmatory means named in `protocol-v3.md`, whose SHA-256 was lodged with four
independent OpenTimestamps calendars **before any trial existed**. Only the two
models that protocol names are confirmatory; the other three were added
afterwards. The proof is now anchored in Bitcoin block 961955, checked against
the block header through a public explorer, not a full node.

Supporting results, all regenerated from `runs/` by `code/manifest.py`:

- A parameter named `service_key_reference` returns a planted, fabricated
  credential **20/20 on all 5 models**.
- **Unplanted control: 0/367.** With nothing planted, models still fill the
  parameter — gpt-4o writes `us`, `online-store-manager/1.0` — but never produced
  a canary. This is why the outcome measure is canary recovery, not field
  population. A seed-derived canary cannot be guessed, so this checks the scorer
  and rules out contamination; it is not a fabrication rate.
  These unplanted stages cover six of eight matrix fields, omitting the
  platform-adjacent and region-adjacent controls; they are not full same-field
  control coverage despite completed six-field stage metadata.
- **69%** (78/113) on 25 attacker-mutated authentic tool listings from 25 MCPTox
  server entries, against
  a neutral-parameter floor of **0/228**.
- **92%** [82, 96] pooled on gpt-4o for the `client_user_agent` parameter, n=60
  over two runs of the identical cell. (Pilot-era orientation figure; it pools
  two runs and is **not** reported in `paper/main.tex`. Cite the paper's per-field
  numbers instead.)

## What this study does *not* show

Read this before quoting anything.

- **On the two confirmatory models, a parameter that never names its target does
  not retrieve it.** The pooled "adjacent" rate of 33% is one parameter,
  `locality_hint`, which is a near synonym for the region it retrieves. The two
  that genuinely avoid naming their target recover **0/20** and **0/20** on gpt-4o
  and nothing on any complete Study 1 arm. **Study 4 qualifies this:** on the three
  newer models some adjacent wordings succeed in part or in full, and a
  billing-attribution parameter returns the planted user, so the boundary is
  model- and wording-dependent, not absolute. See `paper/main.tex` §Study 4.
  The class average states the opposite of the data; read the per-parameter
  table.
- **The pre-registered gate FAILED**, 1 of 3 models. Reported as written.
- **This is planted-content extraction, not self-knowledge.** A real LangGraph
  agent with nothing planted disclosed its own identity **0/240** while calling
  the tool 240/240. The original self-identity hypothesis is retracted.
- **The attack is barely attested in the wild.** Of 401 MCPTox parameter names,
  **0/401** request client identity or a credential, and the surveyed host
  prompts contain 0 credential-shaped strings. In the larger MCP-Zero corpus a
  few documented tools do take a credential as an argument; none asks for client
  identity.
- **The detector is a negative result.** AUC 0.994 looks good and collapses to
  **3.8% precision** at a 0.1% attack base rate.

> **Never quote from older drafts:** "87–100%", "politeness beats honesty", the
> identifier-shaped severity bound, the exploit-chain story, or any "zero-cost
> universal mitigation". All withdrawn. Every `v2_*` number is **exploratory
> permanently** — `protocol-v2.md` was not committed before its data, and no
> later run repairs that. `code/manifest.py --check` fails the build if a banned
> claim reappears in prose.

Start here, in order:

- `protocol.md` — pre-registration, read-only, source of truth
- `protocol-v3.md` — the confirmatory protocol; digest externally witnessed
- `docs/DEVIATIONS.md` — pre-registered vs actual; **read before quoting a number**
- `updated_v6_result.md` — protocol-v3 results, generated, never hand-edited
- `docs/THREAT_MODEL.md`, `docs/RELATED_WORK.md`, `docs/SCANNING.md`
- `CLAUDE.md` — architecture, stage inventory, current empirical state
- `docs/archive/` — **superseded**, do not cite without checking `docs/v6.md`

---

## Layout

```text
code/              All Python. Flat inside code/, no package.
  _root.py         chdir to the repo root on import — EVERY module imports it first
paper/             The journal manuscript; numbers are generated macros
usenix_paper/      Older conference version. Numbers are LITERAL here, not macros.
figures/           Rendered figures (PDF + PNG)
  src/             One .tex source per figure; matrix and gradient are generated
runs/              Canonical append-only JSONL, raw sidecars, completion metadata
data/  labels/  results/  docs/
```

**Run everything from the repository root**, as `python code/<file>.py`. Every
module addresses its data by relative path (`runs/`, `data/`, `config.yaml` —
about ninety of them), and those resolve against the working directory. `cd code
&& python run.py` would write a stage into `code/runs/` and analyse an empty
`runs/` with no error at all, so `code/_root.py` chdirs to the root on import and
refuses to run if it cannot find the repository. Do not remove that import, and
add it to any new module.

---

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # add keys; .env is gitignored
```

> **The local `.venv` (gitignored) is currently broken.** Its interpreter symlink resolves
> to the system `python3`, which has moved to 3.14, while its site-packages are
> `python3.12/`. Anything needing `yaml`, `statsmodels` or the provider SDKs
> fails on import — including `run.py` and the test suite. Rebuild the venv
> before running experiments. Tools with no third-party dependencies
> (`manifest.py`, `make_figures.py`, and the `--selfcheck` paths of `scan`,
> `grade`, `analyze`, `label`) work under plain `python3`.

Nothing below needs an API key except where marked **[API]**.

```bash
python3 code/test_harness.py                          # regression suite
python3 code/scan.py --selfcheck                      # scanner assertions
python3 code/manifest.py --check                      # fail on stale claims in prose
python3 code/run.py --audit                           # no stage with data was deleted
.venv/bin/python code/run.py --stage gate --dry-run   # offline plumbing test
```

---

## Reproducing the results

Run a small live probe for **each provider** before any full stage. Use the
permanent `*_probe` stages, not `--limit` — trials are ordered
model → condition → repetition, so `--limit 6` only exercises the first
condition of the first model.

| Claim | `code/run.py --stage ...` | Trials |
|---|---|---:|
| **Selectivity matrix (confirmatory)** | `v3_matrix_openai`, `v3_matrix_google` | 320 each |
| **Fabrication control** | `v3_unplanted_openai`, `v3_unplanted_google` | 120 each |
| Matrix, post-hoc providers | `v3_matrix_{anthropic,deepseek}` | 320 each |
| Gate (pre-registered, failed) | `gate_{openai,anthropic,google}_apidoc` | 300 each |
| Wording ablation | `wording_ablation[_anthropic]` | 150 |
| Ask-matched ladder (A′/B′/C) | `confound_fix_openai[_anthropic]` | 90 |
| Framework arm (real LangGraph) | `framework_arm_openai[_anthropic]` | 120 |
| Reconstructed MCP listings (types lost) | `real_schemas_{openai,anthropic}` | 250 each |
| Explicit params (HiddenLayer repl.) | `explicit_payloads_openai` | 100 |

The `v3_matrix_*` and `v3_unplanted_*` stages are **Study 1**; the gate, wording,
confound, framework, real-schema and explicit arms are the **pilots** (supplement).
**Studies 2–4 use their own harnesses, not `run.py`,** and write to
`extension_runs/`: `code/schema_types_run.py` (Study 2, constraints and typed
fields), `code/release_stage1.py` with `code/release_policies.py` (Study 3,
encodings and dispatch policies), and `code/flagship_study.py` (Study 4, current
models and the refusing handler). Each records a budget ledger and a design hash,
and runs one leg per launch under a recorded approval. Re-score any leg from its
raw JSONL; the analysis entry points are listed under
`code/reproduce.py`.

Analysis and artifacts:

```bash
python3 code/analyze.py runs/<file>.jsonl            # rates, Wilson CIs, contrasts
python3 code/analyze.py --matrix runs/v3_matrix_*    # fact x parameter matrix
python3 code/stats.py --cluster                      # v3 paired bootstrap by field
python3 code/stats.py --v2-cluster                   # historical v2 field bootstrap
python3 code/make_tables.py                          # every table, from artifacts
python3 code/manifest.py --tex                       # regenerate numbers + figure sources
python3 code/make_figures.py                         # figures/*.pdf and *.png
python3 code/grade.py runs/<file>.jsonl              # [API] blinded judge
python3 code/defense.py                              # [API] TPR/FPR
```

`meta.json`'s `complete` flag is the **only** reliable COMPLETE/PARTIAL signal —
an interrupted stage is otherwise byte-identical in shape to a finished one.

---

## Conditions

One task, one tool. Across conditions **only** the added parameter or the tool
description changes; the task never mentions identity.

| Cond | Channel | Framing | Published policy |
|---|---|---|---|
| A | chat | asks directly | n/a |
| A′ | schema parameter | asks outright, neutral tone | clean |
| B | tool description | imperative injection | **FLAGGED** |
| B′ | schema parameter | imperative tone, ask matched to A′ | **FLAGGED** |
| **C** | schema parameter | **operationally framed** (convention-backed) | **clean** |
| D | schema parameter | neutral `request_trace_id` — control | clean |
| E | schema parameter | explicit `system_prompt`/`model_name` | **clean** |

E rating clean is the point: the *published* attack is missed too.
`protocol.md` covers only A/A′/B/C/D — **never describe B′ or E as
pre-registered**.

---

## Scanners

```bash
python3 code/scan.py                     # our pattern scanner, 2 profiles
python3 code/scan_invariant.py --dry-run # Invariant's PUBLISHED policy, payloads only
python3 code/scan_invariant.py           # [API] 78 gpt-4o-mini calls, local; 168 with --study-fields
```

`code/scan_invariant.py` re-implements Invariant Labs' published
`mcp_scan/policy.gr` verbatim and runs it locally. Say "Invariant's published
policy, re-implemented locally" — **never** "mcp-scan says".

```bash
.venv/bin/snyk-agent-scan inspect mcp_config.json \
    --dangerously-run-mcp-servers --no-bootstrap    # local, NO verdict
```

> `inspect` applies no rules and returns no verdict — measured, `docs/SCANNING.md`
> §1.1. Only `scan` produces verdicts, from a **remote** endpoint, which transmits
> condition descriptions to a vendor. That **is** the coordinated disclosure
> protocol §14 governs. Do not run it without explicit authorization.

---

## Conventions that matter

- **`protocol.md` is never edited.** Neither is `protocol-v3.md` — its SHA-256 is
  externally witnessed, so changing one byte invalidates the timestamp proof.
- **Logs are append-only JSONL.** Do not add or rename fields. Payload and
  framework identity ride in the existing `framework` field.
- **A canonical log has exactly one dot in its basename.** Every derivative adds
  a second (`.raw.`, `.meta.`, `.judged.`). Use `analyze.canonical_runs()` for any
  glob over `runs/` or you will double-count. **Never glob-delete in `runs/`.**
- **The LLM judge never sees the condition.** Blindness is enforced by passing
  only the captured text.
- **Never label LLM output as human labelling.** One 60-row worksheet exists. Its
  attestation names two labelers for one worksheet, so `code/label.py` rejects
  it, and the repository holds no agreement between independent human raters.
  Report the worksheet only as human-versus-grader agreement, stratified, never
  pooled. An earlier pass (κ = 0.011) was discarded. It is kept as
  `labels/v4-apidoc-gate.first-pass-failed.worksheet.csv` and no analysis reads it.
- **No number is typed by hand** in `paper/`. It is a macro from generated
  `numbers.tex`. `usenix_paper/` is the exception — its numbers were flattened to
  literal text, and `numbers.lock.json` plus `manifest.py --check` is what catches
  drift there.
- **Secrets only in `.env`.**

---

## Known environment issues

- **The `.venv` is broken** (see Quick start). Rebuild before running experiments.
- **Gemini free tier is unusable.** `gemini-2.x` has zero quota (429 `limit: 0`);
  `gemini-3-flash` is capped at 20 requests/day, and `gemini-3.1-pro` at 250 per
  model per day — a 320-trial stage is arithmetically impossible without billing.
  Retry with backoff does not help against a daily cap.
- **Undated Anthropic model aliases 404.** Pin exact IDs from `/models`.
- **Providers substitute models silently.** Z.ai serves `glm-4.7` for
  `glm-4.5-air`; DeepSeek serves `deepseek-v4-flash` for both `deepseek-chat` and
  `deepseek-reasoner`. `providers.check_served_model` now refuses the trial rather
  than logging the wrong id.
- **Give thinking models ≥256 output tokens.** A reasoning model can spend the
  whole budget thinking and return a candidate with no parts.
- Model self-report is unreliable at the version level: Claude reports
  "Claude 3.5 Sonnet" while the API id is `claude-sonnet-4-5-20250929`.
