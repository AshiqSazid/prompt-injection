# Author decisions needed to finish submission preparation

The IEEE-formatted journal manuscript and separate supplement are in `journal_paper/`.
The editable cover letter is `journal_paper/COVER_LETTER.md`. They
present existing observations conservatively. They are a substantive revision,
not a claim of Q1 acceptance or permission to upload a manuscript.

To supply missing facts, use [author information](AUTHOR_INFORMATION.md).
The [independent review package](INDEPENDENT_REVIEW_PACKAGE.md) identifies the
scientific questions a human reviewer must resolve; no such review is claimed
completed. The four-task offline extension harness is now implemented as
engineering preparation, not additional model evidence.

## Decisions only the authors can make

1. **Venue:** TDSC is now the preparation target; see [target dossier](TDSC_TARGET.md).
   Direct SCImago 2025 Q1 evidence was retrieved on 2026-09-29; author sign-off
   remains pending. The regular-paper route is the current preparation target.
2. **Scientific route:** the recorded author decision retains the extension:
   controlled A first (1,200 calls on orders and email; Gemini leg, then GPT-4o),
   native-schema B conditional on funding (160).
   Both are tested offline; live observations, reviews, protocol witnessing and
   a funded collection remain outstanding. Current API approval is $0. Changing
   to an existing-evidence-only submission requires an explicit scope decision.
3. **Authorship:** confirm names, order, affiliations, corresponding author,
   contributions, ORCIDs if required, and every author's final approval.
4. **Declarations:** supply actual funding, conflicts, related publications,
   prior submissions/preprints and current review status. Missing information
   cannot be converted into “none.”
5. **Disclosure:** document completed notifications and dates, or approve a
   reasoned no-notification decision under the venue's ethics policy. No message
   has been sent on the authors' behalf.
6. **Release:** approve licensing and permissions for derived source listings,
   canonical/raw data release scope, permanent artifact location and the venue's
   anonymity requirements. Public history cannot be made anonymous merely by
   removing an author name from a PDF.
7. **Independent review:** obtain statistical and domain review of the small
   cluster design, secondary tests, deviations and novelty; verify timestamp
   provenance independently or further narrow its description.

Record confirmed decisions with reviewer, date, rationale and supporting evidence
in `data/submission_decisions.json`; the program does not infer confirmations.
After all substantive edits, approve both source hashes. A successful gate check
means those records are complete and current, not that an editor will accept the
paper or that their factual truth was established by software.

## AI assistance statement for author review

Proposed factual basis, to adapt to the chosen publisher's actual policy:

> An AI coding and writing assistant assisted with implementation review,
> reproducibility checks, literature discovery, and manuscript revision.
> No additional model experiment observations were generated for this revision.
> The human authors must verify all claims, references, code, and analyses and
> take responsibility for the submitted work.

Do not change the last sentence to a completed attestation until it is true.
The assistant is not an author. Add tool/version/date details if the publisher
requires them and the authors can verify them.

## Draft cover-letter substance (not sent)

Please consider “Selective Recovery of Prompt-Resident Facts through Tool-Schema
Parameters: A Controlled Measurement Study” for the selected article type.
The manuscript measures selective recovery of simultaneously planted facts in
tool arguments, attributes parameter-extraction prior art, and reports both
positive and negative findings. It includes paired field-bootstrap uncertainty,
explicit post-collection analysis corrections, and a reproducible artifact.
Its claims concern emitted arguments in the tested setting, not real-world
exfiltration prevalence or demonstrated end-to-end defense effectiveness.

Before using this text, add journal-specific fit and **verified** originality,
exclusive-review, authorship, funding/conflict and disclosure declarations.
No such attestations are implied by this draft.

## Final mechanical steps after decisions

- Review the applied IEEEtran journal/compsoc layout against the current template
  selector; fill confirmed author details and declarations without placeholders.
- Refresh citations and artifact hashes, build PDFs, inspect every page and
  metadata, and check that anonymization matches the venue's review model.
- Run `code/reproduce.py`, the clean-copy release check, and
  `code/submission_check.py`. Archive exact submitted files and approvals locally.
- The corresponding author reviews and submits. No automatic submission is
  part of this repository workflow.
