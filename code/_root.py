"""Make every script in code/ behave as if it were run from the repository root.

WHY THIS EXISTS. These modules address their data by relative path -- there are
roughly ninety of them, `runs/`, `data/`, `paper/`, `labels/`, `figures/src/`,
`config.yaml`. Those resolve against the process's working directory, not
against the module's location. While the Python sat in the repository root the
two were the same thing and nothing had to say so.

They are no longer the same thing. `python code/run.py` from the root still
works, because the working directory is still the root. `cd code && python
run.py` does not: `runs/` becomes `code/runs/`, the glob that looks for prior
artifacts finds none, and a stage writes a fresh log into a directory nobody
analyses. Nothing raises. You get an empty result instead of an error, which is
the failure this project has spent three review rounds learning to fear.

So the fix is not a warning, it is a correction: chdir to the repository root on
import, and refuse to run at all if this file is not sitting inside a tree that
looks like the repository. Import it first, before any module that reads a
relative path.

It is a side effect at import time, which is normally bad manners. It is
defensible here because nothing in this directory is a library -- every file is
a command-line tool that already assumed a repository-root working directory.
This makes the assumption true instead of merely hoped for.
"""
import os

# code/_root.py -> code/ -> repository root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories that only ever exist at the root. `runs/` is the load-bearing one:
# if it is absent we are not where we think we are, and continuing would create
# it somewhere wrong.
_MARKERS = ("runs", "docs", "protocol.md")


def _looks_like_root(path):
    return all(os.path.exists(os.path.join(path, m)) for m in _MARKERS)


if not _looks_like_root(ROOT):
    raise RuntimeError(
        f"code/_root.py resolved the repository root to {ROOT!r}, but that "
        f"directory is missing one of {_MARKERS}. Every relative path in this "
        f"codebase is written against the repository root, so running from "
        f"anywhere else would read and write the wrong files. Move code/ back "
        f"beside runs/ and docs/, or fix ROOT here."
    )

if os.path.realpath(os.getcwd()) != os.path.realpath(ROOT):
    os.chdir(ROOT)
