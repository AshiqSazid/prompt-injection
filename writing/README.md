# `writing/` — the authoring base for the paper

This folder is a **self-contained starting kit for whoever writes the actual paper.**
It is *not* the submission (that lives in [`../paper/`](../paper/)). It gives the
writers a solid, honest base so they start right.

## What's here

| File | What it is | Read it for |
|---|---|---|
| **`base.tex`** | ⭐ The section-by-section writing scaffold (LaTeX). | The entry point. Each USENIX section has colour-coded callouts — **SAY THIS**, **DON'T HIDE**, **HOW TO PHRASE IT**, **REVIEWER TRAP**, and a **STARTER DRAFT**. The Abstract is drafted in full. |
| `SUPERVISOR_REVIEW.md` | Neutral assessment: what's proved, what isn't, is it a paper, and the related-work gap. | The honest read on how strong each claim is, and what to add. |
| `tutorial.md` | The teaching walkthrough of the whole study (esp. §7: framing + sentences to avoid). | Where the "how to phrase it" rules come from. |
| `PROJECT_JOURNEY.md` | Step-by-step history (esp. the "honest-claims cheat sheet"). | What you may/may not claim, and the evidence for each. |

## How to use it

1. Open **`base.tex`** and read the *"How to use this file"* section and the three
   hard rules at the top.
2. Write the **Abstract first** (it's drafted for you — cut it down into your voice),
   then work down the sections in order.
3. For every claim, check it against the callouts: make the **SAY THIS** claim at the
   stated strength, volunteer the **DON'T HIDE** caveat *in the same section*, and use
   the **HOW TO PHRASE IT** wording.
4. Before submitting, run the **master checklist** and the **"sentences never to
   write"** list at the end of `base.tex`.

## Compiling `base.tex`

```
pdflatex base.tex
```

Needs the `tcolorbox` package (standard in TeX Live / MiKTeX). The file passes a
structural check (balanced environments/braces) but was not compiled here — no LaTeX
toolchain was installed on this machine.

## Two things to remember

- **Target venue: USENIX Security.** Two appendices are mandatory and are drafted in
  `base.tex`: *Ethical Considerations* (with a stakeholder analysis) and *Open
  Science* (artifacts at submission). Both are strengths for this project.
- **The artifact always wins.** The authoritative numbers and their macros live in
  [`../paper/numbers.tex`](../paper/numbers.tex); the current empirical state lives in
  [`../CLAUDE.md`](../CLAUDE.md) §13 and [`../updated_v6_result.md`](../updated_v6_result.md).
  The numbers shown in `base.tex`'s starter drafts are for convenience — replace each
  with its `numbers.tex` macro in the real manuscript.

*These three `.md` files are **copies** taken 2026-08-15 so this folder is
self-contained; the living originals are in the repository root and may drift ahead.*
