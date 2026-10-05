# Disclosure decision

**Decided 2026-10-04 by the study author, under the authority given in the
working session of that date. No notice has been sent yet.** Update the status
table below as each notice goes out and each reply arrives; the paper's ethics
statement (`paper/main.tex`, Section "Ethics and responsible disclosure") must
then be updated from this record, never ahead of it.

## Decision

Notify the parties below **before the manuscript is submitted or posted
publicly**, and wait 30 days after the last notice before either, unless every
recipient replies sooner.

Why notify although parameter-based extraction is already public (HiddenLayer,
MSB): the paper adds a measured, selective channel, a credential returned through
a field that names it, and evidence that schema validation and content filtering
at dispatch do not stop it. Those findings bear on how MCP clients and model
providers decide what a tool call may carry.

## Recipients and what each receives

Send through each organisation's published security-reporting channel; do not
guess addresses.

| Recipient | Why | Status |
|---|---|---|
| Model Context Protocol specification maintainers | Host-side release of tool arguments is the paper's main recommendation | not sent |
| OpenAI | GPT-4o and GPT-6.1 Sol were measured | not sent |
| Google | Gemini 3 Flash and Gemini 3.1 Pro were measured | not sent |
| Anthropic | Claude Sonnet 4.5 and Claude Opus 5.5 were measured | not sent |
| DeepSeek | DeepSeek V4 Flash was measured (exploratory) | not sent |
| Invariant Labs / Snyk | Their published tool-poisoning policy flags none of the study's added fields | not sent |

Each notice gives a summary of the findings, the paper draft, and the
host-side mitigations the paper discusses: release decided by the host from the
task's arguments, review of fields added after approval, and confidentiality
tests that cover tool arguments. Notices carry no schemas beyond those printed
in the paper.

The hosted scanner service is still not to be sent the study's schemas
(`protocol.md` §14); that is a separate decision and is not made here.

## Record

| Date | Recipient | Event |
|---|---|---|
| | | |
