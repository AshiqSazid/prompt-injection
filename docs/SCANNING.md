# docs/SCANNING.md — running real external scanners against the conditions

Written 2026-08-08. `code/mcp_server.py` referenced this file for months and it did not
exist; this is that procedure, plus the constraint that governs when it may run.

The H3 detection gap is now the paper's **load-bearing claim**
(`docs/THREAT_MODEL.md` §5.1). Right now it rests on `code/scan.py`, which we wrote
ourselves. That is a plausible defender, not a measured one. This document is how
that gets fixed.

---

## 1. STOP — read before running anything

**Remote verification uploads tool names and descriptions to a vendor.**

`protocol.md` §14 requires coordinated disclosure to (a) affected framework
developers and (b) scanner vendors *before* condition C's patterns are published.
Sending the condition set to a scanner vendor's verification endpoint **is**
disclosure — an unplanned, unilateral, undated one, made to a single vendor, in a
form we do not control.

Consequences of doing it early:

- It starts the disclosure clock without a coordinated plan.
- It hands one vendor an advantage over the others we intend to notify.
- The upload is not reproducible or auditable from our side.

**Therefore: local-only inspection is authorised now. Remote verification is
NOT authorised until the §14 disclosure step is agreed and dated.** Every command
in §3 is local. The flags that keep it local are not optional.

### 1.1 Measured 2026-08-08: the local path CANNOT produce verdicts

This was tested, and the answer changes the plan. Snyk Agent Scan v0.5.15:

- `inspect` is explicitly *"without security verification"*. It enumerates tools
  and prints descriptions. **It applies no detection rules and returns no
  flagged/clean verdict.** Run log: `results/scan-snyk-inspect-20260808-120749.txt`.
- `scan` is the only subcommand that produces verdicts, and it obtains them from
  `--analysis-url`, a **remote verification server**. The installed package ships
  **no local rule, policy, or guardrail files** (verified by searching the package
  tree) — there is no offline detection mode to fall back on.
- The `mcp_scan` 0.4.3 package is the rename shim only (`__init__.py`, `code/run.py`),
  so it carries no Invariant rules either.

**Consequence: H3 cannot be independently validated without transmitting the six
condition schemas to a vendor endpoint — which is precisely the action §1 blocks.**
This is a decision for the authors, not an engineering problem to route around.

**RESOLVED for the rule set, 2026-08-08 — option 2 below worked.** mcp-scan's
detection policy is a FILE, not a service: `mcp_scan/policy.gr`, shipped in the
PyPI package (read from `mcp-scan==0.3.39`, the last Invariant-era release).
`code/scan_invariant.py` re-implements it verbatim and runs it locally against all six
conditions. **No scanner-vendor egress, so §14 is not triggered.** Result: B and B′
flagged; A′, all five C wordings, D, **and E** clean. The hosted service remains
unrun and still gated on §14, but the paper no longer depends on it.

Three ways forward, in order of preference:

1. **Do the §14 disclosure properly, then scan.** Notify the framework developers
   and scanner vendors on a dated timeline, and run `scan` as part of that process.
   This is the correct sequence and it converts the constraint into a contribution
   (the disclosure narrative belongs in the paper anyway).
2. ~~**Try an older Invariant `mcp-scan`**~~ **DONE — this is what resolved it.**
   `mcp-scan==0.3.39` in a throwaway venv ships `mcp_scan/policy.gr` with the
   complete rule set. Do not install it into `.venv/`; the run artifacts depend on
   that environment. See `code/scan_invariant.py` and
   `results/scan-invariant-policy.json`.
3. **Ship the claim scoped.** Report H3 explicitly as "evades a transparent,
   project-authored rule set of the kind static scanners use", caption every table
   accordingly, and state in limitations that external validation is pending
   coordinated disclosure. This is honest and publishable, but it leaves the
   paper's load-bearing section self-refereed — the weakest of the three.

## 2. What the scanner is allowed to see

Real scanners read MCP servers, not Python dicts, so `code/mcp_server.py` publishes
each condition as a real tool with exactly the schema `conditions.build()`
produces.

**Blinding.** Tools are published under uninformative ordinals
(`lookup_recent_orders_01` … `_06`). They previously carried the condition in the
name (`..__C`, `..__B_prime`), which would have contaminated a name-aware scanner
with our own bookkeeping before it read a single description.

Generate the de-blinding sidecar, and keep it away from anything the scanner
ingests:

```bash
.venv/bin/python code/mcp_server.py --write-map     # -> data/mcp_tool_map.json
```

| Published | Condition | Required fields |
|---|---|---|
| `lookup_recent_orders_01` | A′ | `query`, `agent_identity` |
| `lookup_recent_orders_02` | B | `query` (payload is in the description) |
| `lookup_recent_orders_03` | B′ | `query`, `agent_identity` |
| `lookup_recent_orders_04` | **C** | `query`, `client_user_agent` |
| `lookup_recent_orders_05` | D | `query`, `request_trace_id` |
| `lookup_recent_orders_06` | E | `query`, `system_prompt`, `model_name` |

## 3. The authorised local procedure

`mcp_config.json` hard-codes this workstation's absolute path — update it first on
any other machine.

```bash
# 1. Confirm the server starts and publishes six blinded tools
.venv/bin/python code/mcp_server.py --write-map

# 2. Snyk Agent Scan (the tool formerly published as mcp-scan).
#    --no-bootstrap          : do not fetch or call the remote verification service
#    --dangerously-run-mcp-servers : required because our server is stdio; it is
#                              inert (call_tool returns a constant), so this only
#                              starts a local process that declares tools
#    NOTE per §1.1: this ENUMERATES only. It is a plumbing and blinding check,
#    not a detection result. Do not report its output as scanner evidence.
.venv/bin/snyk-agent-scan inspect mcp_config.json \
    --dangerously-run-mcp-servers --no-bootstrap --print-full-descriptions \
    | tee results/scan-snyk-inspect-$(date +%Y%m%d-%H%M%S).txt
```

**Result of the 2026-08-08 run:** the scanner started the server and enumerated
`lookup_recent_orders_01` … `_06`. Two things confirmed: the server is scannable by
real external tooling, and the **blinding works end to end** — the scanner sees only
ordinals, no condition labels. Detection verdicts still require §1.1.

`mcp-scan` in `.venv/bin/` is now only a rename shim that prints a warning.

**Do not** run `snyk-agent-scan scan`, or any subcommand without
`--no-bootstrap`, until §1 is satisfied.

## 4. What to report

For each of the six conditions, record:

1. **Verdict** — flagged / clean.
2. **Which rule fired**, verbatim. "Report exactly which rules B trips and how C
   slips through" is a protocol §9 requirement, not a nicety.
3. **Whether the scanner read parameter names, descriptions, or both.** This is the
   discriminating variable: our own `code/scan.py` is clean on A′ with descriptions
   alone and flags it once names are included. Any external scanner that also
   misses A′ is description-only; one that catches A′ but misses C reproduces our
   `desc+name` result independently — which is the outcome that would make §5.1
   load-bearing.

Then update:

- `docs/archive/tp_result.md` §5 — replace or extend the two-profile table.
- `docs/THREAT_MODEL.md` §5.1 — remove the "project-authored scanner" caveat only if a
  real scanner reproduces the separation.
- `docs/DEVIATIONS.md` §5 — flip "Real external scanner: NOT RUN".

## 5. Expected outcome, written down in advance

Pre-committing this so the result cannot be rationalised afterwards:

- **B, B′, E flagged.** They contain imperative phrasing, a fake auth gate, or the
  literal string "system prompt".
- **D clean.** It is an opaque identifier.
- **A′** — genuinely uncertain. Description-only scanners miss it; name-aware ones
  should catch `agent_identity`.
- **C clean.** This is the prediction the paper depends on.

**If C is flagged, that is the result.** Report it, do not tune the conditions
until it goes clean. A flagged C would narrow the paper to the behavioural gap in
`docs/THREAT_MODEL.md` §5.2 — which is already known to be narrow — and that is a
finding worth publishing rather than hiding.

## 6. Second scanner

One scanner is a data point. Protocol §9 asks for a pattern-based scanner **plus a
meaning-based one**. Candidates, in order of preference:

1. **Invariant Labs mcp-scan** (the original §9 target) if a version independent of
   the Snyk rename is still installable.
2. **promptfoo** tool-poisoning checks — local, no upload.
3. Our own `code/defense.py` intent classifier as the semantic detector. Note it is
   ours, so it does not resolve the self-refereeing problem; it belongs in the
   §10 defense results, not as independent detection evidence.
