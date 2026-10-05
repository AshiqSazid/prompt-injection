# Numbers are a BUILD ARTIFACT, not prose. `numbers.tex` is regenerated from
# runs/ before every compile, so a stale figure cannot reach the PDF: if an
# artifact changes, the macro changes, and the paper follows.
# Relative to the REPO ROOT, because every python rule runs after `cd ..`.
# Prefer the locked analysis environment; the experiment .venv can lack its
# dependencies. Override with PY=path/from/repo/root/to/python if needed.
PY := $(if $(wildcard ../.venv-q1/bin/python),.venv-q1/bin/python,.venv/bin/python)

# A fresh clone has no environment, and `numbers.tex` is tracked so the PDF
# stays reproducible from any commit without one. Regenerating is therefore
# best-effort: if the venv is absent we compile against the committed macros and
# say so, rather than failing a build that has everything it needs. In THIS
# working tree the venv exists, so numbers still regenerate before every compile
# and a stale figure still cannot reach the PDF.
.PHONY: pdf numbers check bundle clean

pdf: numbers
	# -bibtex: run bibtex when citations change. Without it latexmk can
	# reuse a stale main.bbl and silently drop newly cited references --
	# four were missing from the bibliography while every \cite resolved.
	latexmk -pdf -bibtex -interaction=nonstopmode main.tex
	latexmk -pdf -bibtex -interaction=nonstopmode supplement.tex
	# Each document cites the other's tables and sections. Copy the printed
	# numbers across, then compile once more so both pick them up.
	cd .. && $(PY) code/cross_labels.py
	latexmk -pdf -bibtex -interaction=nonstopmode -g main.tex supplement.tex

numbers:
	@if [ -x ../$(PY) ]; then \
	  cd .. && $(PY) code/manifest.py --tex && $(PY) code/paper_assets.py --write; \
	else \
	  echo "  [no ../$(PY): compiling against the committed numbers.tex]"; \
	fi
	# Figures need matplotlib (requirements-figures.txt). Without it the
	# committed figures/*.pdf are used, and `make check` reports any drift.
	@if [ -x ../$(PY) ] && ../$(PY) -c "import matplotlib" 2>/dev/null; then \
	  cd .. && $(PY) code/plot_figures.py; \
	else \
	  echo "  [no matplotlib: compiling against the committed figures]"; \
	fi

# Fails if any registered claim in prose contradicts the artifacts, or if a
# withdrawn claim has reappeared. Run before submitting anything.
check:
	cd .. && $(PY) code/manifest.py --check
	cd .. && $(PY) code/paper_assets.py --check
	cd .. && $(PY) code/plot_figures.py --check
	cd .. && $(PY) code/cross_labels.py --check

# Overleaf and submission systems need every file main.tex reads, not main.tex
# alone: uploading it by itself dies at `\input{analysis_numbers}`. Upload
# overleaf.zip as a new project (New Project > Upload Project).
bundle: pdf
	rm -f overleaf.zip
	zip -q overleaf.zip main.tex supplement.tex numbers.tex analysis_numbers.tex \
	  main_labels.tex supplement_labels.tex \
	  details_*.tex generated_*.tex journal_refs.bib figures/*.pdf

clean:
	latexmk -C main.tex 2>/dev/null || true
	latexmk -C supplement.tex 2>/dev/null || true
	rm -f main.bbl main.run.xml main.spl
