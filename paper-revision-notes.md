# Paper Revision Notes

## Part 1: Experimental Improvements

### 25. Test JSON Schema type constraints

This is probably the best additional experiment.

**Compare:**

- Free-form string
- Enum-constrained string
- Pattern-constrained string
- Integer
- Boolean

The paper itself identifies this as an unresolved question. This directly tests whether the channel depends on having a free-form textual sink.

### 26. Test multiple unrelated tasks

Current synthetic/matrix experiments use one core task. Add several:

- Email search
- Calendar lookup
- File retrieval
- Database query
- Weather lookup

Even modest replication would strengthen external validity.

### 27. Complete Gemini 3.1 Pro

The partial result:

> issuing_surface → platform = 20/20

is interesting but currently only a hypothesis because the overall arm was quota-capped.

Complete it only if you can do so without creating another awkward provenance problem.

### 28. Run the second temperature at scale

The current matrix is essentially one-temperature evidence. A second temperature would address: Is the effect intrinsic to tool-call generation, or amplified by sampling randomness?

Useful, but not essential.

### 29. Test whether leaked content moves to another parameter

Your optional-parameter experiment says making a parameter optional reduces recovery. But you correctly say you don't know whether the model might move the information elsewhere.

A follow-up could have:

- Parameter A: optional
- Parameter B: available

and test whether the model redirects information. This would tell us more about the actual information-flow mechanism.

### 30. Test a real client/UI surface

The paper currently demonstrates the transport, but not whether a specific commercial interface visibly displays that argument.

A small human-inspection experiment could settle that claim cleanly.

---

## Part 2: Paper Writing Fixes

### 1. Fix the "deployed scanner" wording

**Problem:** The paper sometimes says a "deployed" scanner misses the attack, but the experiment actually re-implements Invariant Labs' published `policy.gr` locally; the hosted service was not run.

**Change:**

Replace:
> "Why a Deployed Scanner Misses This"

with something like:
> "Why an Injection-Oriented MCP Policy Misses This"

And replace broad wording such as:
> "A deployed tool-poisoning policy misses…"

with:
> "Invariant Labs' published `policy.gr`, re-implemented locally, does not flag…"

This eliminates a very easy reviewer objection.

### 2. Fix the definition of "benign parameter"

**Problem:** The paper defines a parameter as benign partly because tested detectors classify it as clean. That risks sounding circular.

**Change:**

Use:
> "benign-looking operational parameter"

or:
> "operationally plausible parameter"

Define it based on its semantics/convention, independently of whether a scanner flags it. Then separately state:
> "The parameter was clean under the detector configurations we tested."

This is a small but important conceptual fix.

### 3. Strengthen the novelty distinction from HiddenLayer

**Problem:** A reviewer can reduce the work to: "HiddenLayer already showed parameter-based prompt extraction; this paper just measures it." The paper currently explains the difference, but the novelty needs to be much more forceful.

**Change** the central framing to:

- Prior work: parameter → prompt leakage
- This work: parameter semantics → selective prompt-fact retrieval

Then explicitly identify the two key contributions as:

(a) selective field→fact retrieval, and
(b) mismatch between injection-oriented detection predicates and parameter-mediated exfiltration.

Do not make "benign framing" the central novelty claim because the non-naming experiment does not support that broad claim.

### 4. Make "selectivity" the central mechanism contribution

The strongest new result is:

- requested fact → 68% / 59%
- unrequested facts → 1% / 1%
- neutral control → 0

on the two confirmatory models.

Right now this is excellent, but it appears relatively late. Change the Introduction so the reader understands immediately:

> This is not merely a generic leakage channel. The semantic content of the declared parameter determines which prompt-resident fact is preferentially returned.

That should be one of the paper's first major claims.

### 5. Make the 68% denominator impossible to misinterpret

**Problem:** Table 5 says 68%, but later the paper reveals that the naming-only rate is 94%, because the confirmatory denominator deliberately includes negative non-naming parameters. A reviewer could see 68% and think the attack is mediocre.

**Change:**

Add an explicit sentence immediately around Table 5:
> "The 68% rate intentionally includes preregistered non-naming parameters that serve as deliberate negative treatments; restricted to naming parameters, recovery is 94%."

Then visually distinguish:

| Category | Recovery rate |
|---|---|
| All confirmatory parameters | 68% |
| Naming parameters | 94% |
| Non-naming parameters | generally 0% |

That makes the denominator intellectually transparent.

### 6. Be precise about the real-schema dataset

**Problem:** The paper says "25 tools from 25 different live MCP servers," but your external-validity evidence comes from MCPTox data, and the paper later acknowledges that MCPTox publishes rendered listings rather than complete JSON Schemas.

**Change:**

Prefer something like:
> "25 authentic tool schemas from 25 MCPTox server entries"

unless the actual servers were contacted live. Also avoid implying that their full type information was preserved.

### 7. Explain the MCPTox tool/request matching

**Problem:** The paper says each tool was paired with the server's own request, but does not explain the matching mechanism in enough detail.

**Add one sentence:**
> "Because the published tool-name and request arrays are not index-aligned, we paired requests to tools by greedy token overlap and retained the match score for audit."

This heads off a reproducibility question.

### 8. Fix the user-visibility/UI claim

**Problem:** The paper says the user never sees the arguments and that no consent event occurs, but the research dossier says the actual deployed-client UI question has not yet been experimentally verified.

**Change:**

Use:
> "The API-level tool call succeeds without an error or refusal. Whether a particular deployed client visibly surfaces the additional argument is outside our current measurement."

This is much safer than making a universal UI claim.

### 9. Fix the "no query" phrasing

**Problem:** The paper says the adversary "issues no query," but the whole title describes the schema as a query language.

**Change:**

Use:
> "The adversary needs no separate interactive extraction query or optimization loop; the schema itself serves as the retrieval interface."

That is clearer and internally consistent.

### 10. Update the disclosure/ethics status

The paper currently says: "no completed coordinated notification" and the hosted scanner run remains gated. This is submission-sensitive.

**Before submission/revision:**

- Update the exact disclosure status
- Document any notification that has happened
- Keep the hosted scanner decision consistent with that status
- Make sure the Ethics section describes the current state, not an old snapshot

Do not leave stale disclosure language in the final manuscript.

### 11. Verify every bibliography entry

This is a must. The paper has 35 references, including recent MCP/security work.

**Verify for every citation:**

- Exact title
- Author list
- Venue
- Year
- arXiv ID
- URL
- Page numbers where applicable
- That the cited source actually supports the sentence attached to it

This is particularly important for the new MCP papers and any claims about what existing defenses do.

### 12. Audit anonymous artifact/Open Science compliance

**Verify:**

- Anonymous artifact URL
- No personal GitHub identity
- No identifying commit history
- No author metadata
- No identifying README
- No analytics/tracking that reveals identity
- Artifact accessible to reviewers

The paper says the artifacts are available for reconstruction, but the final submission package must be checked as an anonymous review artifact, not merely a public repository.

