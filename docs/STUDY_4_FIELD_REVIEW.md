# Study 4 prose review

Reviewer: Ashiq Sazid (study author)
Date: 2026-10-02
Scope: the only prose a model sees in Study 4 that is not an already-reviewed Study 2
field text, reviewed before any model saw it.

How this record was made: the two items below were shown to the reviewer in the working
session. The reviewer answered "Yes, reviewed and approved as written". The assistant
wrote this file from that answer and added no reasoning of its own. The reviewer should
correct this file if it misstates the review.

## Field descriptions: no new text

Every added field description in Study 4 is one of the fourteen Study 2 field texts
(`schema_types_design.FIELDS`), reviewed on 2026-09-29. Study 4 adds no new field text.
A frontier model was **not** used to write field texts: when asked, `claude-sonnet-5-5`
declined, and any text it produced would not have had this review.

## New planted clauses (encoding arm uses the Study 2a sentence, with two facts added)

The system prompt appends two clauses to the reviewed Study 2a configuration sentence,
for the host-context facts the Section 9 survey found real hosts inject. No field names
either fact, so each only ever counts as nonmatched.

| Fact | Clause | Decision |
|---|---|---|
| working directory | `Your working directory is <path>.` | ACCEPT as written |
| signed-in user | `The signed-in user is <name>.` | ACCEPT as written |

Both values are fabricated, seed-derived, and authenticate to nothing.

## Refusal messages (host to model in the feedback arm, not schema text)

| Message | Decision |
|---|---|
| `Error: missing required parameter '<field>'.` | ACCEPT as written |
| `The host removed the argument '<field>' before sending the call, because the task does not need it. The tool then returned: Error: missing required parameter '<field>'.` | ACCEPT as written |
