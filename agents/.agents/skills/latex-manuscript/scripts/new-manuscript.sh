#!/usr/bin/env bash
# Start a new manuscript from ../assets/manuscript-template.
#
#   new-manuscript.sh ~/projects/my_paper [/path/to/analysis/project]
#
# Copies the template, sets up git, installs the tidy pre-commit hook, and
# optionally links figures/source at the analysis project that produces the
# plots -- so a pipeline rerun flows into the paper.
#
# A plain copy, no templating: the title and authors are edited in main.tex
# afterwards, and the template stays buildable in place.
set -euo pipefail

TEMPLATE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../assets/manuscript-template" && pwd)"
DEST="${1:-}"
FIGSRC="${2:-}"

if [[ -z "$DEST" ]]; then
    echo "usage: $0 <destination-dir> [analysis-project-dir]" >&2
    exit 1
fi
if [[ -e "$DEST" ]]; then
    echo "error: $DEST already exists" >&2
    exit 1
fi

mkdir -p "$DEST"
# Everything except build products left behind by testing the template in place.
rsync -a --exclude '.git' --exclude 'export' \
      --exclude 'main.pdf' --exclude 'main.bbl' --exclude 'main.blg' \
      --exclude 'main.aux' --exclude 'main.log' --exclude 'main.out' \
      --exclude 'main.fls' --exclude 'main.fdb_latexmk' --exclude 'main.synctex.gz' \
      --exclude 'figures/*.pdf' --exclude 'figures/*.png' --exclude 'figures/source' \
      "$TEMPLATE"/ "$DEST"/
cd "$DEST"

# --- figures source ---------------------------------------------------------
if [[ -n "$FIGSRC" ]]; then
    if [[ -d "$FIGSRC" ]]; then
        ln -s "$(cd "$FIGSRC" && pwd)" figures/source
        echo "linked figures/source -> $(cd "$FIGSRC" && pwd)"
    else
        echo "warning: '$FIGSRC' is not a directory; skipped the symlink" >&2
    fi
fi

# --- git --------------------------------------------------------------------
# The manuscript may be its own repo, or a subdirectory of an analysis project.
# Nesting a git repo inside another one causes more trouble than it solves, so
# only init when we are not already inside a working tree.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    PARENT_ROOT="$(git rev-parse --show-toplevel)"
    echo "inside existing repo ($PARENT_ROOT) -- skipped git init"
    echo "the manuscript will be tracked by that repo"
    HOOK_DIR="$(git rev-parse --git-path hooks)"
    HOOK_SUBDIR="$(realpath --relative-to="$PARENT_ROOT" "$PWD")"
else
    git init -q
    HOOK_DIR=".git/hooks"
    HOOK_SUBDIR="."
fi

# Reflow prose before each commit so diffs stay sentence-level. Written to run
# from the repo root, whichever repo that turns out to be.
if [[ -d "$HOOK_DIR" && ! -e "$HOOK_DIR/pre-commit" ]]; then
    cat > "$HOOK_DIR/pre-commit" <<HOOK
#!/bin/sh
cd "\$(git rev-parse --show-toplevel)/$HOOK_SUBDIR" || exit 0
python tidy.py main.tex sections/*.tex || exit 0
git add main.tex sections/*.tex
HOOK
    chmod +x "$HOOK_DIR/pre-commit"
    echo "installed pre-commit hook (runs tidy.py)"
elif [[ -e "$HOOK_DIR/pre-commit" ]]; then
    echo "note: a pre-commit hook already exists; add 'python tidy.py' to it yourself"
fi

if [[ "$HOOK_SUBDIR" == "." ]]; then
    git add -A
    git commit -qm "Manuscript skeleton from manuscript-template"
fi

echo
echo "created $DEST"
echo
echo "Next:"
echo "  1. edit the title and authors at the top of main.tex"
echo "  2. edit the running header (\\fancyhead) in preamble.tex"
echo "  3. make figures    # build the placeholder figure and the PDF"
echo "  4. read AGENTS.md  # the export constraints, and why they exist"

[[ -d "$HOME/.TinyTeX" ]] || echo $'\nWARNING: ~/.TinyTeX not found. Install with: quarto install tinytex'
