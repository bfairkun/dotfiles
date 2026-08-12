# ============================================================================
#  make          -> main.pdf
#  make figures  -> regenerate figures/, then rebuild
#  make tidy     -> reflow prose to one sentence per line (run before commits)
#  make check    -> fail if a non-exportable command crept in
#  make docx     -> export/<name>.docx for Google Docs (runs check first)
#  make watch    -> rebuild on every save
#  make clean    -> remove build junk, keep the PDF
# ============================================================================

# TinyTeX (installed by Quarto) is not on PATH on Midway, and latexmk shells
# out to `pdflatex` BY NAME -- so the directory must be on PATH, not just
# latexmk called by absolute path.
TEXBIN  := $(HOME)/.TinyTeX/bin/x86_64-linux
export PATH := $(TEXBIN):$(PATH)
LATEXMK := $(TEXBIN)/latexmk
PYTHON  ?= python

# Export is named after this directory, so a renamed repo just works.
NAME := $(notdir $(CURDIR))
SRC  := main.tex preamble.tex macros.tex $(wildcard sections/*.tex) refs.bib
TEX  := main.tex $(wildcard sections/*.tex)
FIGS := $(wildcard figures/*.pdf)

.PHONY: all figures tidy check docx watch clean distclean

all: main.pdf

main.pdf: $(SRC) $(FIGS)
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex

figures:
	$(PYTHON) make_figures.py
	$(MAKE) all

tidy:
	$(PYTHON) tidy.py $(TEX)

check:
	$(PYTHON) check_constraints.py $(TEX)

# Word/Google Docs cannot display PDF images, so the export swaps every
# figure reference to its .png twin. make_figures.py writes both.
docx: check main.pdf
	@mkdir -p export/figures
	@cp figures/*.png export/figures/ 2>/dev/null || \
	  { echo "no PNGs in figures/ -- run 'make figures' first"; exit 1; }
	@cp refs.bib preamble.tex macros.tex export/
	@mkdir -p export/sections
	@sed 's/\.pdf}/.png}/g' main.tex > export/main.tex
	@for f in sections/*.tex; do sed 's/\.pdf}/.png}/g' $$f > export/$$f; done
	cd export && pandoc main.tex --bibliography=refs.bib --citeproc \
	    -o ../export/$(NAME).docx
	@rm -rf export/sections export/main.tex export/preamble.tex \
	        export/macros.tex export/refs.bib export/figures
	@echo "wrote export/$(NAME).docx -- upload to Drive to get a Google Doc"

watch:
	$(LATEXMK) -pdf -pvc -interaction=nonstopmode main.tex

clean:
	$(LATEXMK) -c
	rm -f main.bbl main.blg

distclean:
	$(LATEXMK) -C
	rm -rf export
	rm -f main.bbl main.blg
