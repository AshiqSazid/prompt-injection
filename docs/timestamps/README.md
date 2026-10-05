# Upgraded OpenTimestamps proofs (checked 2026-10-01)

The three original proofs (`protocol-v3.md.ots`, `docs/JOURNAL_EXTENSION_PROTOCOL.md.ots`,
`docs/JOURNAL_EXTENSION_AMENDMENT_1.md.ots`) are unchanged. The files here are
copies that were run through `ots upgrade` (opentimestamps-client), so they also
carry the Bitcoin block attestations.

## What was checked

For each proof, the file's SHA-256 equals the digest in the proof, and the
Merkle root of every Bitcoin attestation equals the `merkle_root` of that block
as served by `blockstream.info`. All 12 attestations matched.

This used a public block explorer, not a local full node. `ots verify` against
a Bitcoin node has not been run.

| Protocol file | SHA-256 (first 16 hex) | Earliest block | Block header time (UTC) |
|---|---|---:|---|
| `protocol-v3.md` | `4c4557e9022508af` | 961955 | 2026-08-11 04:14:11 |
| `docs/JOURNAL_EXTENSION_PROTOCOL.md` | `b3c1c3bbc90e7f1e` | 969188 | 2026-09-29 18:11:16 |
| `docs/JOURNAL_EXTENSION_AMENDMENT_1.md` | `d3e8872ea55e9d18` | 969197 | 2026-09-29 20:35:31 |

Other attested blocks: 961958, 962013, 962551 (v3); 969190, 969201, 969204
(extension protocol); 969201, 969204, 969244 (amendment).

## What the anchors do and do not show

A Bitcoin attestation proves the digest existed no later than the block time.

- **Study 1 (v3).** Block 961955 (04:14:11 UTC) precedes the first v3 trial,
  recorded at 11:05:32 on 2026-08-11 without a time zone (05:05:32 UTC if local
  time at UTC+6, later if UTC).
- **Study 2 protocol.** Committed and submitted to the calendars at about 17:31
  UTC; the first planted trial started at 17:36:52 UTC. The earliest Bitcoin
  anchor (18:11:16 UTC) is **after** the Gemini leg of stage A began, and before
  the GPT-4o leg (18:28:31 UTC) and stage B. For the Gemini leg, precedence
  rests on the calendar receipts and the commit record, not on the Bitcoin block.
- **Amendment 1.** Committed and submitted at about 19:13 UTC; the first planted
  stage B trial started at 19:15:21 UTC. The earliest anchor (20:35:31 UTC) is
  **after** stage B was collected. Precedence rests on the calendar receipts and
  the commit record.

## Study 3 stage 1 protocol (checked 2026-10-01 20:06 UTC)

`docs/STUDY_3_STAGE1_PROTOCOL.md`, SHA-256 `21db2c9cfbe4c699…`, was submitted to
the calendars at 18:44:46 UTC on 2026-10-01. Its upgraded proof
(`STUDY_3_STAGE1_PROTOCOL.md.upgraded.ots`) carries a Bitcoin attestation for
block **969484**, header time **2026-10-01 19:19:47 UTC**. The Merkle root
matches the block header served by `blockstream.info`. No planted stage 1 call
existed when the check was made: the first live leg started after it. As
with the Study 1 protocol, and unlike Study 2, the Bitcoin anchor precedes every
planted call.

## Reproduce

```bash
pip install opentimestamps-client
ots info docs/timestamps/protocol-v3.md.upgraded.ots
ots verify -f protocol-v3.md docs/timestamps/protocol-v3.md.upgraded.ots   # needs a Bitcoin node
```
