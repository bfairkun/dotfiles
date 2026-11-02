#!/usr/bin/env python3
"""Fail if a command that breaks the Word export crept into the manuscript.

Why this exists: coauthors comment in Google Docs, so `make docx` has to
produce a faithful document. Pandoc does not run LaTeX -- it parses it -- so
package commands it does not implement are silently mangled or dropped. A
wrong figure number in a shared draft costs more than the nicer syntax saves.

Each rule below records what actually happens on export, verified by testing.

    python check_constraints.py main.tex sections/*.tex
"""
import re
import sys

# (regex, what it exports as, what to write instead)
BANNED = [
    (r"\\[Cc]ref\b",
     'exports as a bare wrong number, e.g. "(3)"',
     r"Figure~\ref{...} / Table~\ref{...} -- type the word yourself"),
    (r"\\subref\b",
     'exports as an empty "()"',
     r"draw panel letters in make_figures.py and write \textbf{(A)} in the caption"),
    (r"\\SI\{",
     'exports with the unit dropped, e.g. "1  "',
     r"plain text: 1 \textmu M, or spell out the unit"),
    (r"\\si\{",
     "exports with the unit dropped",
     "plain text"),
    (r"\\num\{",
     "exports as an empty string",
     "type the number"),
    (r"\\begin\{tcolorbox\}",
     "the whole box vanishes, contents included",
     "ordinary prose, or a quote environment"),
    (r"\\begin\{subfigure\}",
     "becomes a bare table with empty panel labels",
     "one combined figure PDF with letters drawn in Python"),
    (r"\\ref\{eq:",
     'exports as the raw label, e.g. "Equation [eq:model]" -- pandoc numbers '
     "figures and tables but not equations",
     "refer to it in words: \"the model above\", \"Equation 1\" written out"),
]

# Not fatal, but you do not want these in a draft you hand to a coauthor.
WARN = [
    (r"\\todo\{", "unresolved TODO"),
]


def scan(paths):
    errors, warnings = [], []
    for path in paths:
        with open(path) as fh:
            for lineno, line in enumerate(fh, 1):
                code = line.split("%", 1)[0]      # ignore commented-out text
                if not code.strip():
                    continue
                for pattern, effect, fix in BANNED:
                    if re.search(pattern, code):
                        errors.append((path, lineno, pattern, effect, fix))
                for pattern, note in WARN:
                    if re.search(pattern, code):
                        warnings.append((path, lineno, note))
    return errors, warnings


if __name__ == "__main__":
    errors, warnings = scan(sys.argv[1:])

    for path, lineno, note in warnings:
        print(f"warning: {path}:{lineno}: {note}")

    if errors:
        print()
        for path, lineno, pattern, effect, fix in errors:
            cmd = pattern.replace("\\\\", "\\").replace(r"\b", "").replace(r"\{", "{")
            print(f"ERROR {path}:{lineno}")
            print(f"  found:   {cmd}")
            print(f"  exports: {effect}")
            print(f"  use:     {fix}")
            print()
        print(f"{len(errors)} constraint violation(s). "
              "These compile to a fine PDF but corrupt `make docx`.")
        sys.exit(1)

    print(f"check passed ({len(warnings)} warning(s))")
