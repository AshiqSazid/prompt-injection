# Experiment 25 — protocol amendment 1

Date: 2026-09-30. Amends the sealed protocol `JOURNAL_EXTENSION_PROTOCOL.md`
(SHA-256 `b3c1c3bbc90e7f1e979a0182b9f9e199a9efa81dba4f76e5805594c381568545`),
which is not edited. Made **before any planted stage B call**. This file is
committed and its SHA-256 submitted to OpenTimestamps
(`JOURNAL_EXTENSION_AMENDMENT_1.md.ots`) before stage B runs.

## What changed

One line of code: `FIXTURE_STATUS = "approved"` in `code/native_fixtures.py`
(commit `99d376c`), after the human native-fixture review
(`EXPERIMENT_25_FIXTURE_REVIEW.md`, Md. Rafiur Rahman, 2026-09-30). The review
accepted all eight correct calls and changed no fixture, request or adapter.

The protocol already requires this approval before stage B ("fixture approval
remain[s an] author review item"); the flag is the gate that records it. No
stage B field, size, schema, scoring rule or analysis changes.

## Why the design hash changes

`design_digest()` hashes every Experiment 25 source file, including
`native_fixtures.py`, for every stage. Changing the flag therefore changes both
digests, although stage A never uses the native fixtures:

| Stage | Sealed hash | Hash after this amendment |
|---|---|---|
| A | `886842230fd2f48276b1ab3b7d668ecd9bec70ed644e53bcd02fd1da82be151e` | `4e62358310a8c98a217121daf50d217059d1b14f451114f1cf0170e0b8fc411c` |
| B | `8e2a2eae730844f32e1c0abe9bf508cc9f8c0bb9993790be01ce209399573cb2` | `b26321f16057743903f9e473df40bb666deddc60c51b304128f3ce80ed15f8e6` |

**Stage A is unaffected.** Both stage A legs were collected and committed
(`2e27080`, `0aa504d`) under the sealed hash `886842…151e`, which their meta
files record. They are analysed as collected and are not re-run.

**Stage B runs under `b26321…f8e6`.** Its approval files must name this hash.

## What was observed before this amendment

Stage B has no planted observation. The only stage B calls were the unplanted
compatibility check (`extension_runs/compat_B-20260929-185852.jsonl`, 32 calls,
plus 3 repeat calls recorded in `EXPERIMENT_25_RUN_LOG.md` §5). The reviewer
saw those results and declared it. Stage A's results were also known when this
amendment was made; stage B's funding and execution were not made conditional
on them, and B's design is unchanged from the sealed protocol.
