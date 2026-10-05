# Focused journal draft: citation and novelty review

Checked 2026-09-28 using public primary pages/full text; no paid research API.
Scope: the ten references cited by `journal_paper/main.tex`, not a claim that
all 35 references in the earlier expanded narratives have passed a full review.
The literature skill's distinction between discovery, metadata, and in-body
verification guided this pass. Searches covered selective tool-parameter
disclosure, system-prompt/schema extraction, and structured-output schema influence.
This is a targeted, nonsystematic search, not an exhaustive literature review.

| Citation | Primary passage checked | Supported use and boundary |
|---|---|---|
| HiddenLayer / McCauley, Kan, Bonner (2025) | [Article byline, introduction, fake-function section](https://www.hiddenlayer.com/research/beyond-mcp-expanding-agentic-function-parameter-abuse) | Parameter abuse is established prior work; the article distinguishes prior real MCP tools from its fake user-message function definitions. Journal byline corrected to the named authors. Do not describe all demonstrations as the same adversary as this study. |
| Zhang et al., MSB (2025) | [§4.2 and Appendix B.1.2](https://arxiv.org/html/2510.15994v1) | Out-of-scope parameters already solicit unauthorized information. This paper's matrix is a measurement distinction, not discovery of parameter attacks; MSB also evaluates execution and task/security tradeoffs. |
| Lin (2026) | [§2.1–2.3, §3.2 and §5](https://arxiv.org/html/2608.08254v1) | Structured-output schema descriptions influence nonce-label classification under conflicting definitions. That endpoint differs from prompt-fact recovery; both studies are task-limited. Added rather than dismissing this close recent work. |
| Greshake et al. (2023) | [Authors and abstract](https://arxiv.org/abs/2302.12173v2) | External retrieved content can redirect an LLM application without a direct adversarial user query. This supports only the broad background claim; no exclusive taxonomy or universal instruction-shape claim remains. |
| Wang et al., MCPTox (2025) | [Author list, §3 and §4.3](https://arxiv.org/html/2508.14925v1) | Metadata-poisoning benchmark and source of rendered listings. The source's authentic servers do not make our reconstructed string-only schemas native or prove our runs executed real servers. |
| Debenedetti et al., AgentDojo (2024) | [NeurIPS proceedings record and paper](https://proceedings.nips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html) | Dynamic environment for task, attack and defense evaluation. Title, six authors, year and proceedings match the retained entry. We make no unsupported claim that this benchmark cannot support a future extension. |
| Yergattikar, ShieldMCP (2026) | [Archival metadata](https://aclanthology.org/2026.acl-industry.58/) and [paper's runtime framework](https://aclanthology.org/2026.acl-industry.58.pdf) | Runtime defense is relevant neighboring work. Added one-author ACL Industry reference, pages 865–871, DOI 10.18653/v1/2026.acl-industry.58. Its existence prevents treating one static-policy miss as a verdict on all defenses; no untested transfer result is asserted. |
| Debenedetti et al., CaMeL (2025) | [Author list and §4.2–4.3](https://arxiv.org/html/2503.18813v1) | Control/data-flow separation and capability policies motivate external release control. The draft does not claim that our fixtures were tested against CaMeL or that a label automatically solves all leakage. |
| OWASP LLM07 (2025) | [Prevention guidance](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/) | Avoid secrets in system prompts. This is guidance, not evidence that secrets are prevalent in deployed prompts. |
| MCP contributors (2025) | [Versioned tools specification, Security Considerations](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) | Tools use input schemas and calls; host confirmation and input review are relevant. Replaced the unversioned 2024 attribution in the journal bibliography with the explicit 2025-06-18 specification. The protocol does not mandate unchecked release. |

## Position after review

The defensible contribution is a reproducible, simultaneous-fact selectivity
measurement with field-level uncertainty and negative controls. Neither
parameter-mediated extraction nor behavioral influence of schemas is new.
No “first,” universal scanner-failure, benchmark-absence, or deployment-wide
prevalence assertion is justified. The journal draft removes those claims.

The selected arXiv entries identify the preprints used; this does not certify
that no later archival version exists. Before actual submission, check updated
versions and venue records, update the search through that date, and have a
human domain author sign off the comparison. Other potentially relevant work
remains catalogued in the expanded manuscript; reducing its main-text citation
count is editorial focus, not a finding that the omitted papers are irrelevant.

## Venue checks are separate

Current category/year-specific SJR Q1 status has **not** been certified. Direct
SCImago access was unsuccessful. IEEE TDSC and ACM TOPS remain candidate venues,
not chosen destinations; third-party quartile summaries are not treated as
primary verification. Publisher author-guideline pages were also intermittently
unavailable, so no exact page limit, fee, review model or template compliance is
asserted. Computers & Security remains excluded under the publisher's stated
AI/ML-system-security scope restriction documented in the readiness audit.
