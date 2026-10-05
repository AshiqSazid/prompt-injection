# Related work and novelty positioning

> **Working record, not the paper.** The claims live in `paper/main.tex`;
> this file keeps the evidence and the revision history behind them. Where
> the two differ, the paper is what is being submitted and this file is what
> explains how it got there.
>
> **Superseded in part (2026-10-04). Treat no number or novelty claim below as
> current — several predate the protocol-v3 matrix and Studies 2 to 4. Cite
> `paper/main.tex` only.** The reversals:
> - The A′/C inversion is a **failed** preregistered hypothesis (reported as such).
> - There is **no human-vs-human κ**. The one worksheet gives κ = 0.911
>   human-vs-keyword-grader on the scaffolded stratum, and its attestation is
>   rejected (two labelers, one rating column). The "κ = 1.00" cell below is wrong.
> - The eight-fact v2 rates and 0/1760 are exploratory; the paper reports five
>   facts (68% / 59% vs 2% / 1%).
> - protocol-v3 **has run** and the naming/adjacent gradient **has run** — the
>   adjacent (non-naming) fields fail on the confirmatory pair.
> - The pooled 92% joins two experiments and is not in the paper.
> - The paper **leads with selectivity, not detection**, and cites MSB as prior art
>   alongside HiddenLayer; "first quantification" / "nobody has published" framings
>   are dropped.

Literature reviewed 2026-07-27, revised 2026-08-11 after the mechanism claim
changed. In response to the USENIX reviewer's implicit question: *what exactly is
new here?* The short answer is that the phenomenon is **already known and partly
published** — what is missing from the literature, and what this project has, is
**quantification, selectivity, and the detection-shape gap**. Position the paper
on those, not on discovery.

---

## 1. The closest prior art — read this before writing anything

### HiddenLayer, "Beyond MCP: Expanding Agentic Function Parameter Abuse" (industry, 2025)

**This is the paper that most threatens your novelty, and you must cite it.**

They inject parameters named `system_prompt`, `model_name`, `chain_of_thought`,
`conversation_history` into an otherwise ordinary tool, and successfully extract
system prompts from **Claude Opus 4, GPT-4o, o4-mini, Qwen3-235B, Qwen2.5-72B,
DeepSeek-V3, and Cursor**.

So "a required tool parameter can extract system-prompt contents" is **not novel**.

**What they did NOT do — every one of these is your contribution:**

| | HiddenLayer | This project |
|---|---|---|
| Parameter framing | **Explicit** (`system_prompt`) | **Benign** (`client_user_agent`) — never asks for identity |
| Success rates | None — binary demos | Rates, n=30/cell, Wilson CIs |
| vs. asking directly | **Not tested** | A′ 37% vs C 87% — **the inversion** *[SUPERSEDED: this is the failed preregistered hypothesis; the retained gate has A′ 9/30 vs C 29/30 on gpt-4o and no difference on Claude or Gemini]* |
| Scanner evasion | **Not tested** | B/B′ flagged, A′/C/D clean |
| Controls | None | Bare arm 0/300, D 0%, ask-matched B′ |
| Grader validation | None | *[SUPERSEDED — see banner: no human-vs-human κ; κ = 0.911 human-vs-grader, attestation rejected]* |

**Consequence for your framing.** Do not claim "we discover that schema fields leak
system prompts." Claim *[SUPERSEDED wording: the quote below uses the exploratory
eight-fact v2 numbers and puts detection first; see the Status note after it]*:

> Prior work shows that *explicitly named* parameters extract system prompts. We
> show the disclosure is **selective and steerable**: with eight facts planted in
> every trial and each schema requesting exactly one, the model returns the
> requested fact ~99% of the time and withholds the seven it demonstrably holds
> (off-diagonal ~1%; neutral control 0/1760). A benign schema behaves less like a
> leak than like a query. And unlike the explicit version, it is invisible to the
> tool-poisoning policy the ecosystem ships — **as is the explicit version**,
> which is the more durable finding.

**Status:** *[SUPERSEDED 2026-10-04: `protocol-v3.md` has run. The selectivity
result is confirmatory on the two models that protocol names (five facts,
diagonal 68% / 59% vs off-diagonal 2% / 1%); the three later models are post-hoc.
The v2 arms stay exploratory. Cite `paper/main.tex`.]* The original note read: the
selectivity result is exploratory because `protocol-v2.md` was never committed
before its data, and `protocol-v3.md` had not yet run.

**The earlier framing is withdrawn.** A prior version of this section claimed
"a field that never mentions identity extracts more than one that asks outright…
politeness beats honesty". That ordering was measured on one model, disappears
once the planted content is not a recognisable product name, and is superseded by
selectivity. `code/manifest.py --check` now fails the build if it reappears.

### MCP-ITP: Implicit Tool Poisoning (arXiv 2601.07395)

Black-box optimization of poisoned tool metadata: **84.2% ASR** across 12 agents,
suppressing malicious-tool detection to **0.3%**.

**Threat to you:** "optimized poisoning evades detectors" is already published, so
your detection-gap claim is not new *in general*.

**Your delta:** MCP-ITP still embeds *malicious instructions* and needs an
optimization loop against detector feedback. Your condition C contains **no
instruction at all** and needs **no optimization** — it is a single hand-written
benign field. Frame it as: *evasion without an adversarial objective*. A defender
who assumes attacks must contain attack-shaped text is wrong even against a
zero-effort adversary.

### MCPTox (AAAI) — benchmark of tool poisoning on real-world MCP servers

Provides a dataset of **real MCP servers**. Directly usable to fix your W4 (one
synthetic tool). Running condition C's field against real server schemas would make
your generalization claim far stronger than n=1 tool.

### MindGuard (arXiv 2508.20412) — the defense to beat

Attention-based Decision Dependence Graph; **94–99% precision**, attribution, <1s.

**Two exploitable gaps:** (a) it requires **white-box attention access** — useless
to the operator of a hosted API, which is your threat model's defender; (b) the
paper reports **no false-positive rate on benign tools**. Your §10 defense should
be **black-box** and **must** report FP cost on genuinely benign telemetry fields —
`client_user_agent` is a *real* field in real APIs, so the FP question is the whole
difficulty. That is a clean contribution nobody has made.

### Others worth citing
- **OWASP MCP Top-10 (MCP03:2025 Tool Poisoning)** — establishes practitioner relevance.
- **Agent Security Bench (arXiv 2410.02644)** — the benchmark reviewers will ask why you didn't use.
- **"Your LLM Agent Can Leak Your Data" (arXiv 2604.05432)** — backdoored tool-use exfiltration; distinguish: they backdoor the tool, you don't.
- **MCPXKIT / MCPThreatHive** — MCP security tooling landscape.

---

## 2. What the literature says you must add

### 2.1 Replicate HiddenLayer as a condition (NEW: condition E)

Add an **explicit** parameter arm — `system_prompt` / `model_name`, HiddenLayer-style
— run alongside C in the same file. This does three things at once:

1. **Quantifies prior work.** They reported no rates; you would supply the first
   measured numbers for their attack. That is a citable contribution on its own.
2. **Makes the inversion airtight.** C vs E is benign-vs-explicit with the channel
   held constant — the exact comparison your thesis needs.
3. **Pre-empts "this is just HiddenLayer."** You cannot be scooped by work you
   measured.

### 2.2 Payload generality — RAN 2026-08-08, severity now known

HiddenLayer extracted **entire system prompts**. The question was whether a benign
field does the same or only pulls a product name. **Answer: neither extreme.**

gpt-4o, condition C held fixed, n=20/payload (`docs/archive/tp_result.md` §7 for the full table
and caveats): product name 80%, unreleased build codename **85%**, platform name
inside a six-sentence block **100%** — but operator policy text **0/20** and a
credential-shaped token **0/20**, and 4 of the 5 secrets in the long block never
left. Neutral-field control D = **0/97**.

**SUPERSEDED.** The paragraph that stood here read the single-field payload
results as a *content* bound and called the framing "shape-restriction". The v2
matrix falsified that: with a field that names a credential, the credential comes
back 20/20 on both providers, where the same fact returns 0/20 through a
User-Agent field. The bound was a property of the one field being asked, not of
the channel.

What replaces it is **selectivity** (§3, contribution 2), which is a stronger
claim and a measured one. Still true and worth keeping from the original: we do
**not** match HiddenLayer's whole-prompt result through a benign field, and
claiming so remains the easiest thing for a reviewer to falsify with our own data.

### 2.3 Real deployments, not just raw API

HiddenLayer tested **Cursor and desktop apps**. Your framework arm used LangGraph
and found 0% — but LangGraph injects no product identity. A real MCP client
(Claude Desktop, Cursor) has genuine deployment identity in its system prompt,
which is exactly the payload C is good at extracting. **Your `code/mcp_server.py`
already makes this testable**: install it in a real client and see what arrives.
This is the honest version of the "real framework" claim.

### 2.4 Real-world tool schemas (MCPTox dataset)

Fixes "n=1 synthetic tool." Append the benign field to real MCP server schemas and
measure. Cheap, and it converts a toy demonstration into a measurement study.

---

## 3. Revised contribution list (what the paper actually claims)

*[SUPERSEDED 2026-10-04. The paper's four contributions are now: selectivity
among simultaneously planted facts; schema validity and field type do not gate
release; models transform confidential content on request, so content matching
fails where structural removal does not; and an auditable measurement design
(`paper/main.tex`, Introduction). Items 1, 2, 3, 4 and the closing line of this
list no longer describe it: "first quantification" is dropped (MSB is credited),
selectivity is confirmatory on two models with five facts, detection is
secondary, and the self-knowledge result is reported only as a withdrawn
hypothesis. The list is kept as history.]*

1. **First quantification** of parameter-based prompt extraction — rates, CIs,
   controls — where prior work gave binary demos. Pooled 92% [82, 96] on gpt-4o
   for the benign field against a neutral-field floor of 0/228 across 25 real
   schemas.
2. **Selectivity — the strongest claim, and currently EXPLORATORY.** Eight facts
   planted in every trial, one requested per schema: diagonal ~99%, off-diagonal
   ~1%, neutral control 0/1760. The model releases what is asked for and withholds
   what is not. That is a mechanism, not a leak rate, and nobody has published it.
   *(Superseded the "inversion / politeness beats honesty" framing, which held on
   one model and only for a recognisable product name.)*
3. **The detection-shape gap — the most durable contribution.** Invariant's
   published policy flags B and B′ and misses A′, all five C wordings, D **and E**
   — the *published* attack whose parameters are literally named `system_prompt`
   and `model_name`. Deployed tool-poisoning scanners are injection-shaped and do
   not model parameter-based exfiltration at all. This holds regardless of what
   protocol-v3 shows, which is why it should lead the paper.
3b. **An occupied false-positive floor.** The most effective attack wording scores
   25 against legitimate `user_agent.original` at 15, and four parameters of the
   widely-deployed Sequential Thinking MCP server false-positive at the operating
   threshold — a legitimate server that asks agents to report their own
   chain-of-thought, one of HiddenLayer's four published exfiltration parameters.
   The attack surface already exists benignly in the wild.
4. **Negative result — harness anosognosia**: under a real framework with nothing
   planted, models leak **0/240** genuine framework identity, and when asked
   outright they **confabulate** (`"assistant"`, `"Claude AI assistant"`) rather
   than decline. Publishable independently; matters to anyone trusting agent
   self-report.
5. **Framework transparency**: LangGraph passed the adversarial field through in
   240/240 calls — the transport is not the mitigation people assume.
6. **Methodology**: an LLM judge over overlapping categories scored **below chance**
   (κ = −0.13) on the exact construct being measured; undetectable without an
   independent grader.

Contributions 4–6 are yours alone and nobody has published them.

**The delta against HiddenLayer is NARROW — say so before a reviewer does.**
*[SUPERSEDED 2026-10-04: the naming/adjacent/generic gradient has run. It did not
widen the delta: on the two confirmatory models the adjacent (non-naming) fields
recover their fact in 0/20 except a near-synonym, so the data show selectivity
and scanner-invisibility but **not** that a field which never names its target
retrieves it. Study 4 finds some adjacent wordings succeed on newer models and a
billing field returns the user, but it is exploratory. Claim selectivity, not
"benign framing extracts".]* The original note: all seven matrix fields name
their category, so the gradient (then staged, unrun) was what would decide it.

---

## 4. Honest risks to novelty

- **The core mechanism is published** (HiddenLayer). Your paper is a *measurement
  and framing* contribution. That is publishable at USENIX — but only if you say so
  first, in the intro, rather than letting a reviewer discover it.
- **Detection evasion is published** (MCP-ITP, 0.3%). Your angle must be
  *zero-effort* evasion, not evasion per se.
- ~~**If payload generality fails**~~ — **it half-succeeded** (§2.2). Codenames and
  platform identifiers extract at 85–100%; policy text and credentials do not. The
  abstract should claim a *bounded* prompt-disclosure primitive plus the
  shape-restriction mechanism, and must not imply secret exfiltration.
  *[SUPERSEDED: §2.2 above withdraws shape-restriction. A field that names the
  fabricated credential returns it in 20/20 calls on every Study 1 model.]*
- **The inversion is narrower than it looked.** C > A′ replicates only on gpt-4o
  AND only for a recognizable product name; on invented identifiers the explicit
  field ties or wins. Both framings that once led this section are now retired:
  the inversion, and shape-restriction. **Lead with selectivity and the
  detection-shape gap.** *[SUPERSEDED: the paper leads with selectivity only;
  detection is one subsection of the robustness section.]*

## 5. Prior work the paper cites that this file does not cover

Added 2026-10-05. Section 13 of `paper/main.tex` now positions the work against
several lines this record never discussed. Read them there, not here:

- **MCP Security Bench (MSB)**, which lists out-of-scope parameters as an attack
  surface. The paper credits it, with HiddenLayer, for the extraction mechanism.
- **Information-flow and capability control for agents**: CaMeL, RTBAS, FIDES,
  IsolateGPT, Progent, and the design-patterns paper. The paper evaluated none.
- **Contextual integrity and exfiltration through tool use**: ConfAIde,
  PrivacyLens, AirGapAgent, Imprompter.
- **MCP runtime defenses**: MCPGuard, MCPShield, ShieldMCP, and the
  defense-placement taxonomy, beside MindGuard above. The paper benchmarked none.

## Sources

- [HiddenLayer — Beyond MCP: Expanding Agentic Function Parameter Abuse](https://www.hiddenlayer.com/research/beyond-mcp-expanding-agentic-function-parameter-abuse)
- [MCP-ITP: Implicit Tool Poisoning in MCP](https://arxiv.org/abs/2601.07395)
- [MCPTox: Benchmark for Tool Poisoning on Real-World MCP Servers](https://arxiv.org/pdf/2508.14925)
- [MindGuard: Intrinsic Decision Inspection](https://arxiv.org/abs/2508.20412)
- [OWASP MCP03:2025 — Tool Poisoning](https://owasp.org/www-project-mcp-top-10/2025/MCP03-2025%E2%80%93Tool-Poisoning)
- [Agent Security Bench (ASB)](https://arxiv.org/pdf/2410.02644)
- [Your LLM Agent Can Leak Your Data](https://arxiv.org/html/2604.05432v1)
- [MCPXKIT](https://arxiv.org/pdf/2508.12538)
