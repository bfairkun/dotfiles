#!/usr/bin/env python3
"""Reflow .tex prose to one sentence per line. Write however you like; run this.

Only touches ordinary paragraph text. Left alone: comment lines, anything
starting with a backslash command on its own line, and the contents of
verbatim-ish and math environments.

    python tidy.py sections/*.tex main.tex
"""
import re
import sys

SKIP_ENVS = {"equation", "equation*", "align", "align*", "verbatim",
             "lstlisting", "tabular", "tikzpicture"}

# Block-level commands that own their line. Inline macros (\gene, \cref, \num,
# \textbf, ...) are deliberately NOT here -- a line starting with one of those
# is still prose and should be reflowed with the sentence around it.
STRUCTURAL = re.compile(
    r"\\(?:documentclass|usepackage|input|include|bibliography\w*|"
    r"(?:sub)*section\*?|paragraph\*?|chapter\*?|part\*?|"
    r"begin|end|item|label|caption\*?|subcaption\*?|captionsetup|"
    r"maketitle|appendix|title|author|affil|date|"
    r"(?:re)?newcommand|(?:re)?newenvironment|def|let|setcounter|"
    r"centering|noindent|clearpage|newpage|vspace|hspace|hfill|"
    r"toprule|midrule|bottomrule|cmidrule|includegraphics|tnote)\b")

# End of sentence: . ? ! optionally followed by a closing quote/bracket/footnote,
# then whitespace, then a capital letter or a backslash command.
SENTENCE_END = re.compile(
    r"(?<![A-Z])"                      # not an initial like "J. Smith"
    r"(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<!\bcf)(?<!\bet al)"
    r"([.?!]['\")\]}]*)"
    r"\s+"
    r"(?=[A-Z\\])"
)


def reflow_paragraph(text):
    text = " ".join(text.split())
    return SENTENCE_END.sub(r"\1\n", text)


def _delta(line):
    """Net bracket balance of a line, ignoring escaped brackets."""
    line = re.sub(r"\\[\[\]{}]", "", line)
    return (line.count("[") - line.count("]")
            + line.count("{") - line.count("}"))


def tidy(src):
    out, para, env_depth, open_brackets = [], [], 0, 0
    for line in src.splitlines():
        stripped = line.strip()

        if m := re.match(r"\\begin\{(\w+\*?)\}", stripped):
            if m.group(1) in SKIP_ENVS:
                env_depth += 1
        structural = (
            env_depth > 0
            or open_brackets > 0     # still inside a multi-line [options] block
            or not stripped
            or stripped.startswith("%")
            or stripped.startswith("}")
            or STRUCTURAL.match(stripped)
        )
        if structural:
            open_brackets = max(0, open_brackets + _delta(stripped))
        if m := re.match(r"\\end\{(\w+\*?)\}", stripped):
            if m.group(1) in SKIP_ENVS and env_depth:
                env_depth -= 1

        if structural:
            if para:
                out.append(reflow_paragraph(" ".join(para)))
                para = []
            out.append(line)
        else:
            para.append(stripped)

    if para:
        out.append(reflow_paragraph(" ".join(para)))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path) as fh:
            src = fh.read()
        new = tidy(src)
        if new != src:
            with open(path, "w") as fh:
                fh.write(new)
            print(f"tidied {path}")
