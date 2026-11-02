"""Generate every figure in the manuscript.

Writes each figure twice: a vector PDF (used by LaTeX) and a 300 dpi PNG
(used by `make docx`, because Word cannot display PDF images).

Panel letters are drawn HERE, not in LaTeX -- \\subref{} exports to Word as an
empty "()". See AGENTS.md.

    python make_figures.py       # or: make figures
"""
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
# If figures/source is a symlink to an analysis project, read its outputs from
# there so a pipeline rerun flows into the paper.
SOURCE = os.path.join(OUT, "source")

os.makedirs(OUT, exist_ok=True)

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "legend.frameon": False,
    "pdf.fonttype": 42,      # embed real text, not outlines
})


def panel_label(ax, letter):
    """Draw a bold panel letter above-left of an axes."""
    ax.text(-0.18, 1.06, letter, transform=ax.transAxes,
            fontsize=10, fontweight="bold", va="bottom", ha="left")


def save(fig, name):
    """Write both the PDF LaTeX uses and the PNG the Word export needs."""
    fig.savefig(os.path.join(OUT, f"{name}.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {name}.pdf + {name}.png")


# ---------------------------------------------------------------- Figure 1
# Replace this with the real thing. The shape is the point: build the figure,
# label the panels, call save() with the name used in \includegraphics.
fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.7))

rng = np.random.default_rng(0)
axes[0].scatter(rng.normal(size=200), rng.normal(size=200), s=4, lw=0)
axes[0].set_xlabel("x")
axes[0].set_ylabel("y")
panel_label(axes[0], "A")

axes[1].plot(np.linspace(0, 10, 100), np.sin(np.linspace(0, 10, 100)), lw=1.2)
axes[1].set_xlabel("x")
axes[1].set_ylabel("sin(x)")
panel_label(axes[1], "B")

fig.tight_layout(w_pad=2.4)
save(fig, "fig1_example")
