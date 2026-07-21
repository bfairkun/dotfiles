# My set up guide for HPC work

This guide documents the HPC setup and workflow patterns that have made my work on UChicago HPC more comfortable over the years. Nothing here is the only way to do things — these are tools and habits that happen to work well together for me. As you get started, you'll find things you want to change, skip, or replace with something you prefer. That's expected and encouraged: fork the dotfiles repo, make it yours, and commit your own conventions.

The setup provides:

- A comfortable shell environment (zsh, tmux, fzf) that persists across SSH disconnects
- Conda environments for Python and R analysis
- Snakemake + Slurm integration for running pipelines on the cluster
- Quarto notebooks that render to a browsable HTML docs site
- Claude Code as an interactive co-author for analysis notebooks
- Plot visualization tunneled directly to your browser

The guide is organized as: set up your HPC environment → configure your local Mac → understand the project structure and workflow patterns.

---

## Prerequisites

- **RCC Midway account** — request via [rcc.uchicago.edu](https://rcc.uchicago.edu)
- **Mac laptop** — the clipboard-sync and port-forwarding instructions assume Mac; Linux users can adapt
- **SSH key pair** — generate with `ssh-keygen -t ed25519` and add the public key to your GitHub account
- **GitHub account** and basic git familiarity

---

## Part 1: HPC Setup

### 1.1 Fork and Clone the Dotfiles Repo

**What are dotfiles?** Configuration files like `~/.zshrc`, `~/.gitconfig`, and `~/.tmux.conf` live in your home directory and control how your shell, editor, and tools behave. They're called dotfiles because they start with a dot (hidden by default). Over time you accumulate a lot of these, and when you get a new machine or a new HPC account, recreating them from scratch is tedious and error-prone.

Tracking dotfiles in a git repository solves this: your entire environment is version-controlled, documented, and reproducible. Setting up a new account becomes `git clone` + a few stow commands instead of hours of manual configuration. It also means you can share your setup, collaborate on improvements, and roll back changes that break something.

**Why Stow?** Rather than copying config files into `~` (which makes them hard to track), [GNU Stow](https://www.gnu.org/software/stow/) creates symlinks. Each top-level folder in the repo is a "package," and `stow <pkg>` symlinks its contents into `~`. The actual files stay in `~/dotfiles/` under git control, but programs find them at the expected paths. Edit a file, `git commit`, push — done.

A `stow` binary is included in the repo at `local_dotfiles_RCCMidwayGeneral/bin/stow` (a Perl script) so it's available immediately after cloning, before anything else is set up. If you'd rather not run a binary from someone's dotfiles repo, install it yourself — from source, via your system package manager, or via Homebrew on Mac — and it'll work the same way.

**Fork** the repo on GitHub so you can commit your own personalizations, then clone it:

```bash
git clone git@github.com:YOURNAME/dotfiles.git ~/dotfiles
```

If you run into conflicts with existing files (e.g., a `~/.bashrc` already exists), use the helper script to move them out of the way first:

```bash
python3 ~/dotfiles/bin/bin/MoveStowConflicts.cli.py
```

**Personalize these files before stowing** (search for `bjf79` or `pi-yangili1`):

| File | What to change |
|------|----------------|
| `git/.gitconfig` | Your name and email |
| `config/.config/snakemake/slurm_midway3/cluster-config.yaml` | `account: pi-YOURPI`, your scratch path in `shadow-prefix` |
| `config/.config/snakemake/slurm_midway3/config.yaml` | `conda-prefix` — shared snakemake conda env cache (pick a path on `/project/`) |
| `local_dotfiles_RCCMidwayGeneral/.condarc` (if using it) | `envs_dirs` and `pkgs_dirs` to your own `/project/` paths |

#### How the `*_local` Pattern Works

One recurring design throughout this repo is having a general config file that sources or imports a machine-specific counterpart. This lets the shared dotfiles stay clean and machine-agnostic, while each machine's quirks are isolated in a separate file that only gets stowed on the right machine.

**`.zshrc` → `.zshrc_local`**
The shared `~/.zshrc` ends with `source ~/.zshrc_local`. The `local_dotfiles_RCCMidwayGeneral` package provides the `.zshrc_local` that handles HPC-specific things: loading modules (`module load node`), the `sq`/`watchjobs` aliases, starting the agent_plots server, and the X11 display fix. On your Mac, a different stow package provides a different `.zshrc_local` with Mac-specific settings. Neither machine ever sees the other's config.

**`AGENTS.md` → `AGENTS.local.md`**
The shared `~/.agents/AGENTS.md` imports `~/.agents/AGENTS.local.md`. Each machine package supplies the local file with paths, cluster settings, and other machine-specific facts. Client-required instruction files import the shared `AGENTS.md`.

The same pattern applies to `.profile` → `.profile_local` and `.bashrc` → `.bashrc_local`. When you set up a new machine, you create a new `local_dotfiles_MACHINENAME` package with just the overrides for that machine, and the general packages stay untouched.

---

### 1.2 Manual Tool Installs

These tools are not available as HPC modules or in conda — install them once into your user account:

#### Miniconda3
All Python environments and Snakemake run through conda.

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init zsh bash
```

After this, install `mamba` for faster solves:
```bash
conda install -n base -c conda-forge mamba
```

#### Quarto
Quarto renders `.qmd` notebooks to HTML, PDF, or slides. Download the Linux binary (no root needed):

```bash
mkdir -p ~/opt
# Check quarto.org for the latest version number
wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.7.29/quarto-1.7.29-linux-amd64.tar.gz
tar -xzf quarto-1.7.29-linux-amd64.tar.gz -C ~/opt/
ln -s ~/opt/quarto-1.7.29/bin/quarto ~/bin/quarto
```

#### uv
A fast Python script runner used by the Claude Code Jupyter kernel bridge:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# installs to ~/.local/bin/uv
```

#### Claude Code CLI
The AI assistant that co-authors notebooks, writes Snakemake rules, and connects to Jupyter kernels:

```bash
curl -fsSL https://claude.ai/install.sh | sh
# installs to ~/.local/bin/claude
```

You'll need to authenticate (`claude auth login`) and have an Anthropic account.

---

### 1.3 Stow the Right Packages

**First: switch your login shell to zsh.** Bash is the default on RCC Midway. The zsh and ohmyzsh packages below won't do anything useful until you change this. Follow the instructions at [docs.rcc.uchicago.edu/ssh/faq](https://docs.rcc.uchicago.edu/ssh/faq/) to request a shell change (it typically requires emailing RCC support). Once changed, log out and back in to confirm you're in zsh (`echo $SHELL`).

From `~/dotfiles`, stow these packages for HPC use:

```bash
cd ~/dotfiles
stow sh bash zsh ohmyzsh fzf git tmux config other local_dotfiles_RCCMidwayGeneral claude
```

What each package provides:

| Package | What it does | Notes |
|---------|-------------|-------|
| `sh` | `.profile` — PATH setup, sources `.profile_local` | Install first; everything else depends on it |
| `bash` | `.bash_profile`, `.bashrc` | Minimal; sources `.profile` |
| `zsh` + `ohmyzsh` | zsh config with oh-my-zsh: git status in prompt, `z` for fast directory jumping, syntax highlighting, fzf integration | |
| `fzf` | Fuzzy finder — `Ctrl+R` for history, `Ctrl+T` for files | |
| `git` | Global gitconfig with useful aliases (`co`, `st`, `gr` for graph log, `up` for pull+rebase) | **Personalize name/email** |
| `tmux` | tmux config: vim-style pane navigation, tab bar, mouse, clipboard sync | |
| `vim` | Vimrc with Snakemake syntax highlighting, R/Python plugins | Optional — skip if you prefer another editor |
| `config` | Snakemake Slurm profiles, matplotlib/uv defaults | **Personalize account and paths in snakemake profile** |
| `other` | `.Rprofile` (httpgd graphics, session utils), `conda_minimal_yamls/py_general.yaml` | |
| `local_dotfiles_RCCMidwayGeneral` | SSH agent, module loads, tmux auto-attach, conda init, aliases, `~/bin` scripts, Claude Code settings | **Personalize conda paths** |
| `agents` | Shared instructions and skills plus Claude, Codex, and Gemini configuration | |

**Do NOT stow on HPC:** `local_dotfiles_MEDGEN_MacbookAir` (Mac only — see Part 2), `local_dotfiles_HPStream`, `local_dotfiles_MyMacbookAir`, `local_dotfiles_RCCMidway2Specific`, `local_dotfiles_RCCMidway3Specific`.

After stowing, log out and back in (or `source ~/.profile`) for all changes to take effect.

#### Resolving Conflicts After Stowing

If existing agent configuration conflicts with stow, back it up before merging.

The recommended approach:

```bash
# Back up existing client configuration:
cp -r ~/.claude ~/.claude.bak

# Stow the package (this may fail on conflicts — that's OK)
stow agents

# For any files that conflicted, diff the backed-up version against the new stowed version:
diff ~/.claude.bak/CLAUDE.md ~/dotfiles/agents/.claude/CLAUDE.md
```

Then open each conflicting file and go through it line by line — keep what you want from your old config, and adopt the conventions from the new one. Claude Code itself is a good tool for this: open the two versions side by side and ask Claude to help merge them, explaining the purpose of each section.

Once you're happy, commit your merged versions to your dotfiles fork:

```bash
cd ~/dotfiles
git add agents
git commit -m "Personalize agent configuration for YOURNAME"
git push
```

This is particularly important for `CLAUDE.md` (which teaches Claude your workflow conventions) and `settings.json` (which controls permissions).

---

### 1.4 Conda Environments

#### Philosophy: One Broad Env + Small Specialized Envs

The recommended approach is to have **one primary environment** (`py_general` or similar) that you use for almost everything — interactive analysis in notebooks, running Snakemake, rendering Quarto documents, and general data wrangling. Keep this env stable and rarely modify it; adding too many packages over time leads to slow solves and dependency conflicts that are hard to debug.

For tools with unusual or heavy dependencies (a specific aligner, a deep learning library, a tool that requires an old Python version), create small named environments instead of polluting your primary one. Snakemake's `conda:` directive makes this natural: each rule can specify its own env yaml in `code/envs/`, and Snakemake builds and caches them automatically.

**Summary:**
- `py_general` — your daily driver: notebooks, Snakemake orchestration, Quarto, pandas/numpy/scipy/matplotlib/pysam/bedtools and friends
- `code/envs/specific_tool.yaml` — per-rule envs for pipeline steps (built automatically by Snakemake)
- Named specialized envs (e.g., `spliceai`, `alphafold`) — for tools too heavy or conflicting to put in `py_general`

#### Creating the Environments

**Base environment** — provides `mamba`, JupyterLab, basic tools:
```bash
mamba env update -n base -f ~/dotfiles/local_dotfiles_RCCMidwayGeneral/conda_yamls/base.yaml
```

**`py_general`** — your primary analysis environment (pandas, numpy, scipy, matplotlib, seaborn, pysam, bedtools, scikit-learn, Snakemake, and more):
```bash
mamba env create -f ~/dotfiles/other/conda_minimal_yamls/py_general.yaml
```

> **Personalize:** The bottom of `py_general.yaml` has pip packages (`my-utils`, `alphagenome`, `pikachu-chem`) that are specific to this lab. Remove those lines unless you need them, then rebuild.

The `sm_splicingmodulators.yaml` in `conda_yamls/` is an example of a heavier project-specific env that bundles many bioinformatics tools (STAR, samtools, etc.) for convenience. It can serve as a reference or starting point, but for most work `py_general` + rule-specific envs is the cleaner approach.

Per-project conda environments (for individual Snakemake rules) live in `code/envs/` inside each project and are built automatically by Snakemake — you don't need to create those manually.

---

### 1.5 Snakemake + Slurm Profile

The Snakemake Slurm profile (stowed from `config/.config/snakemake/slurm_midway3/`) automatically submits each rule as a Slurm job, monitors status, and handles retries. Key defaults:

- `jobs: 150` max concurrent jobs (well below RCC limits)
- `local-cores: 5` (RCC login node concurrency limit — don't exceed this)
- `use-conda: true` — each rule uses its own conda env from `code/envs/`
- `rerun-incomplete: true` — restart interrupted jobs on next run

**After personalizing** (`account`, `shadow-prefix`, `conda-prefix`), test with a dry run:

```bash
cd yourproject/code
snakemake --profile slurm_midway3 -n   # dry run — always do this first
snakemake --profile slurm_midway3      # real run
```

Monitor jobs:
```bash
sq          # formatted squeue (alias from .zshrc_local)
watchjobs   # watch -n5 sq
```

---

### 1.6 Agent Setup

After stowing the `agents` package:

- `~/.agents/AGENTS.md` provides shared instructions.
- `~/.agents/skills/` provides shared workflows.
- Client-specific directories provide settings and discovery entry points.

#### Second Claude Code identity (e.g. a work/enterprise account)

The package also stows `~/.claude-enterprise/`, a second Claude Code config dir. It shares `CLAUDE.md`, `skills`, `agents`, `list-sessions.sh`, `dispatcher_watchdog.sh`, and `statusline-command.sh` with `~/.claude/` via relative symlinks — these are safe to share because Claude Code only ever reads them. Use the second identity by exporting `CLAUDE_CONFIG_DIR=~/.claude-enterprise` before running `claude` — see the `dispatch` skill for how sessions pick an identity. The status line shows which config dir is active.

`settings.json` is **not** shared — each identity has its own independently tracked copy (`agents/.claude/settings.json` vs `agents/.claude-enterprise/settings.json`), seeded equal but free to diverge. See the `dotfiles` skill for why (Claude Code rewrites this file live, e.g. on `/model`, which breaks a symlink the first time it happens).

One thing `stow` can't carry across machines, since it points to a real runtime dir that only exists under `~/.claude/` (never tracked in git) — redo this once per machine after stowing:

```bash
ln -sfn ../.claude/projects ~/.claude-enterprise/projects
```

This is what keeps memory/session history unified across both identities instead of forking — safe to share because it's a directory symlink (new files land inside it without touching the symlink itself).

Optionally, also do a one-time copy of `settings.local.json` to start the enterprise identity with your existing personal-account permission grants instead of re-approving everything from scratch — it will not stay in sync after that:
```bash
cp ~/.claude/settings.local.json ~/.claude-enterprise/settings.local.json
```

Then, one-time per machine: `CLAUDE_CONFIG_DIR=~/.claude-enterprise claude` → `/login` with the second account.

#### The Jupyter Kernel MCP: Persistent Interactive Sessions

The Jupyter kernel MCP provides a persistent, stateful Python session rather than a new subprocess for every execution.

Variables remain in memory between turns, allowing iterative analysis without reloading data.

The MCP script lives at `agents/.agents/skills/jupyter-kernel/jupyter_kernel_mcp.py`. Register it as a user-scope stdio server in each client. It communicates over the Jupyter wire protocol (ZMQ), without an HTTP server.

**Installation steps:**

```bash
# 1. Symlink the script onto PATH (~/bin is on PATH from .profile):
ln -sf ~/.agents/skills/jupyter-kernel/jupyter_kernel_mcp.py ~/bin/jupyter_kernel_mcp.py

# 2. Register the py_general kernelspec (one-time per machine):
conda activate py_general && python -m ipykernel install --user --name py_general
# For R: conda activate base && R -e "IRkernel::installspec()"
```

If the MCP tools do not appear, invoke the `jupyter-kernel` skill.

To start Claude Code in a project:
```bash
cd /path/to/yourproject
claude
```

---

## Part 2: Local Mac Setup

### 2.1 SSH Config

Add the following to `~/.ssh/config` on your Mac (or stow `local_dotfiles_MEDGEN_MacbookAir` if you clone the dotfiles there too):

```
Host midway*
    User YOURHPCUSERNAME
    RemoteForward 2224 127.0.0.1:2224   # tunnels remote clipboard → Mac
    LocalForward 8765 localhost:8765     # tunnels HPC plot server → browser
    ControlMaster auto
    ControlPath ~/.ssh/control-%r@%h:%p
    ControlPersist 24h
    ServerAliveInterval 60
    ServerAliveCountMax 5

Host midway
    HostName midway2-login1.rcc.uchicago.edu

Host midway3
    HostName midway3-login3.rcc.uchicago.edu
```

What each option does:
- **`RemoteForward 2224`** — lets the HPC push text to your Mac clipboard (via `Ctrl+C` in tmux)
- **`LocalForward 8765`** — makes the HPC plot server available at `http://localhost:8765` in your browser
- **`ControlMaster`/`ControlPersist`** — subsequent SSH connections reuse the existing connection (fast, no re-authentication)
- **`ServerAliveInterval`** — keeps the connection alive through Mac sleep/wake

### 2.2 Clipboard Sync (Mac)

The tmux `Ctrl+C` keybinding copies the tmux buffer to your Mac clipboard via the SSH tunnel. For this to work, your Mac needs to listen on port 2224 and maintain a persistent reverse tunnel to each HPC.

Stow the Mac package on your Mac (not on HPC):
```bash
# On your Mac:
cd ~/dotfiles
stow local_dotfiles_MEDGEN_MacbookAir
launchctl load ~/Library/LaunchAgents/pbcopy.plist
launchctl load ~/Library/LaunchAgents/localhost.autossh-tunnels.plist
```

Two launchd services are installed:
- **`pbcopy.plist`** — listens on port 2224 and pipes anything received to `/usr/bin/pbcopy`
- **`localhost.autossh-tunnels.plist`** — maintains persistent reverse SSH tunnels (port 2224) to each HPC, restarting automatically if the connection drops

The list of HPC hosts is in `~/.config/autossh_tunnel_hosts` (stowed from the Mac package). To add a new host, add its SSH alias (from `~/.ssh/config`) to that file and reload:
```bash
launchctl unload ~/Library/LaunchAgents/localhost.autossh-tunnels.plist
launchctl load ~/Library/LaunchAgents/localhost.autossh-tunnels.plist
```

Tunnel logs go to `/tmp/autossh-tunnels.log` if you need to debug.

---

## Part 3: Projects

### Workflow Philosophy

The core idea is a clean separation between **data processing** and **data exploration**:

**Data processing (Snakemake)** is the heavy lifting — alignment, quantification, statistical modeling. You write rules once, run the pipeline, and it produces output files. Ideally you only need to re-run this when the underlying data or methods change. Reproducibility matters here: every step is explicit, versioned, and reproducible from scratch.

**Data exploration and visualization (notebooks + Claude)** is inherently iterative. You load the pipeline outputs, make plots, adjust, explore, generate hypotheses, and repeat. This loop should be fast and interactive — you don't want to wait for a Slurm job every time you tweak a color palette or filter threshold.

These two phases map onto different tools:

```
Raw data → Snakemake pipeline → output files
                                     ↓
                    Quarto notebook + Claude + Jupyter kernel
                                     ↓
                         analysis/ → docs/ (rendered site)
```

The project structure directly reflects this split: `code/` holds the pipeline, `analysis/` holds the notebooks, and `output/` holds the small committed results that bridge the two.

#### The Interactive Exploration Loop

The typical interaction with Claude during the exploration phase looks like this:

> "Start a new Python kernel and a new notebook. Let's start by plotting X vs Y from the output file — save it to the agent_plots directory so I can preview it before you write anything to the notebook."

Claude will:
1. Create a dated `.qmd` file in `analysis/`
2. Start a Jupyter kernel — on the login node by default, which is fine for most plotting and data wrangling. If you anticipate a computationally intensive session (large matrices, model fitting, many samples), ask Claude to connect to a compute node kernel instead (see `compute-kernel` skill in Part 4)
3. Write and run exploratory code in the kernel — **not yet in the notebook**
4. Save the plot to `$SCRATCH/$USER/agent_plots/` where you can immediately view it at `http://localhost:8765`
5. Once you're happy with how it looks, write that code as a chunk in the `.qmd` file

This preview-before-commit pattern is deliberate: you can iterate on a plot many times without cluttering the notebook with dead-end attempts. Only the clean, final version goes into the `.qmd`. The notebook stays readable and renders correctly from top to bottom.

**In practice:** keep a browser tab open at `http://localhost:8765` while you work. Every time Claude generates a plot, it appears there instantly. Redirect Claude ("make the x-axis log scale", "drop the outlier samples", "use a colorblind-safe palette") and it re-runs in the kernel and updates the plot — all before touching the notebook file.

---

### 3.1 Cookiecutter Project Template

New projects are scaffolded from a cookiecutter template that sets up Quarto notebooks, Snakemake, and git submodules together.

Install cookiecutter (once):
```bash
mamba install -n base cookiecutter
```

Create a new project:
```bash
cookiecutter gh:bfairkun/cookiecutter-quarto-smk
# Prompts: project name (use YYYYMMDD_ProjectName format), optional submodules
```

The project is created in the current directory. Move it to your HPC project space:
```bash
mv 20260529_MyProject /project/yangili1/YOURNAME/
```

### 3.2 Project Structure

```
20260529_MyProject/
├── analysis/               # Quarto notebooks (.qmd files)
│   ├── _quarto.yml         # Site config (renders all notebooks → docs/)
│   ├── index.qmd           # Landing page
│   └── 20260529_*.qmd      # Date-prefixed analysis notebooks
├── code/
│   ├── Snakefile           # Main workflow entry point
│   ├── rules/              # Snakemake rule files (.smk)
│   ├── envs/               # Per-rule conda environment yamls
│   ├── config/             # config.yaml, samples.tsv
│   ├── scripts/            # Helper scripts called by rules
│   ├── scratch/            # Large intermediate files (not git-tracked)
│   ├── logs/               # Rule-specific logs (stdout/stderr from each Snakemake rule)
│   └── module_workflows/   # Git submodules (e.g., rna_seq pipeline)
├── data/                   # Raw data (small files committed; large files symlinked)
├── output/                 # Small committed results (tables, summaries)
└── docs/                   # Rendered HTML site (auto-generated by Quarto)
```

**Key conventions:**
- Notebooks are date-prefixed: `analysis/20260529_QC_exploration.qmd`
- Large intermediate files go in `code/scratch/` (gitignored) — never in `output/`
- Every Snakemake rule needs a `log:` directive (Slurm captures stdout/stderr there)
- Per-rule conda envs in `code/envs/descriptive_name.yaml` — don't reuse `py_general` for pipeline rules

### 3.3 RNA-seq Submodule

For RNA-seq projects, add the Snakemake RNA-seq workflow as a git submodule:

```bash
cd yourproject/code/module_workflows
git submodule add git@github.com:bfairkun/snakemake-workflow_rna-seq.git rna_seq
git submodule update --init --recursive
```

Or include it at project creation time via the cookiecutter prompt.

The submodule provides rules for STAR alignment, QC (MultiQC), and quantification. Configure it via `code/config/rna_seq/` and include its rules from your main `Snakefile`.

### 3.4 Quarto Docs Site

All notebooks in `analysis/` render to a browsable HTML site in `docs/`:

```bash
quarto render analysis/              # render everything
quarto render analysis/20260529_QC_exploration.qmd   # render one notebook
```

Enable GitHub Pages on your repo (set source to `docs/` on `main` branch) and the rendered site will be publicly accessible — useful for sharing results with collaborators.

**Sharing a single notebook as a self-contained file:** By default, rendered HTML references external files (CSS, JS, data). If you want to email or share a single portable `.html` file that works without a server, render with embedded resources:

```bash
quarto render analysis/20260529_QC_exploration.qmd --embed-resources --standalone
```

This produces a single larger HTML file with everything bundled in — useful when sharing with collaborators who just want to open the file directly.

---

## Part 4: Interactive Workflow with Claude

Claude Code is the AI assistant running in your terminal. Beyond answering questions, it can actively co-author analysis: executing code in a live kernel, viewing the outputs, writing finalized chunks to your notebook file, and generating Snakemake rules following project conventions. This is driven by a set of **skills** — context documents that tell Claude how each part of the workflow operates. They are invoked automatically when relevant, or explicitly with `/skill-name`.

Here is what each skill does:

### `hpc` skill
Provides Claude with RCC Midway cluster context: which partition to use (caslake on Midway3, broadwl on Midway2), the lab account (`pi-yangili1`), how to write sbatch headers, and how to run Snakemake dry runs before submitting. Invoke when asking about job submission or cluster configuration.

### `new-project` skill
Scaffolds a new project using the `cookiecutter-quarto-smk` template. Prompts for a date-prefixed project name and optional submodules (e.g., the RNA-seq workflow), then creates the full project directory structure.

### `new-notebook` skill
Creates a new date-prefixed Quarto notebook (`analysis/YYYYMMDD_description.qmd`) with the correct YAML header for the kernel (Python or R), standard imports, and relative paths already set up.

### `jupyter-kernel` skill
Manages the connection between Claude and a Jupyter kernel running on the **login node**. Claude can start a kernel (Python or R), list running kernels, and execute code interactively. This is the MCP server you set up in section 1.6. Use this for lightweight analysis that doesn't need compute resources.

### `compute-kernel` skill
Connects Claude to a Jupyter kernel running on a **compute node**. You start the kernel yourself first:

```bash
start_agent_kernel --mem 48G --time 4:00:00 --cpus 4
# Options: --lang r  (for an R kernel)
#          --env py_general  (specify conda env)
```

This submits a Slurm job, waits for it to start, and writes a connection file to `$SCRATCH/$USER/agent_kernel.json`. Then tell Claude: "connect to the compute kernel." All subsequent code runs on the compute node with full memory and CPU access.

### `interactive-notebook` skill
The core co-authoring skill. Guides Claude through the full iterative loop: run exploratory code in the kernel → save plots → discuss results → write validated chunks to the `.qmd` file one at a time. Handles session state checkpointing so work can survive context compaction in long sessions.

### `agent-plots` skill
Tells Claude where to save plots (`$SCRATCH/$USER/agent_plots/`) and how to make them viewable. Plots are served at `http://localhost:8765` via the SSH `LocalForward` in your Mac's SSH config — just open that URL in your browser. The server (`agent_plots_server.py`) starts automatically on login.

Preferred formats:
- **PDF** for most plots — vector graphics, zoomable, small file size
- **PNG** for plots with thousands of text labels (e.g., large heatmaps)

### `snakemake-rule` skill
Generates or edits Snakemake rules following project conventions: `log:` directive on every rule, relative paths from `code/`, proper resource specifications, and a rule-specific conda env. Also covers the testing workflow: validate env → test on one sample → full run.

### `r-quarto` skill
R-specific Quarto notebook conventions: correct YAML header, `#|` chunk options (not old `{r, ...}` style), common packages, and the `quarto render` command (not `rmarkdown::render`, which can fail on HPC due to library version issues).

### `dispatch` skill
Spawns parallel Claude sessions in new tmux windows — useful when you want separate Claude instances working on different parts of a project simultaneously. See the tmux section in Part 5 for how windows and panes work.

### 4.1 Typical Session Flow

```
ssh midway                          # auto-attaches to tmux session
cd /project/yangili1/YOURNAME/myproject
claude                              # start Claude Code

# Light analysis (login node kernel):
"Create a notebook for QC exploration"       # → new-notebook skill
"Start a Python kernel and connect"          # → jupyter-kernel skill
"Load the data and make a PCA plot"          # → interactive-notebook + agent-plots skills

# Heavy analysis (compute kernel):
start_agent_kernel --mem 64G --time 6:00:00  # (in separate tmux pane)
"Connect to the compute kernel"              # → compute-kernel skill
"Run DESeq2 on all samples and plot results"
```

---

## Part 5: Tips & Gotchas

### Tmux

tmux is a terminal multiplexer: it runs a persistent server on the HPC so your work survives SSH disconnects. If your connection drops mid-analysis, you SSH back in and everything is exactly where you left it — running jobs, open editors, shell history, all of it.

The key concepts:
- **Sessions** — a collection of windows, persistent across disconnects
- **Windows** — like browser tabs, each with its own shell (or Claude process)
- **Panes** — splits within a window; one window can show multiple terminals side by side

**Auto-attach on login:** The `.profile_local` contains:
```bash
tmux attach-session -t ssh_tmux || tmux new-session -s ssh_tmux
```
This means every SSH login automatically drops you into a persistent session named `ssh_tmux`. If it doesn't exist yet, it creates it. You never lose work to a dropped connection.

**Running multiple Claude sessions:** The `dispatch` skill and `claude_dispatcher` alias (from `.zshrc_local`) open a new tmux window running a Claude dispatcher agent, which can in turn spawn additional Claude sessions each in their own window. This is useful when you want to work on multiple things in parallel — e.g., one Claude session writing a Snakemake rule while another is in the middle of a notebook exploration. Each window is independent, and you can switch between them instantly.

**Panes within a window:** You can split any window manually to see multiple terminals at once — useful for running `start_agent_kernel` in one pane while Claude runs in another, or watching `sq` while a pipeline runs.

Key bindings (configured in `.tmux.conf`):

| Key | Action |
|-----|--------|
| `Ctrl+T` | New window |
| `Alt+Left/Right` | Previous/next window |
| `Alt+1-9` | Jump to window N |
| `"` | Split pane horizontally (new pane below) |
| `%` | Split pane vertically (new pane to the right) |
| `Ctrl+hjkl` | Navigate between panes (vim-style) |
| `F11` | Zoom/unzoom current pane |
| `Ctrl+C` | Copy tmux buffer to local Mac clipboard |
| `PageUp/Down` | Enter/navigate copy mode (scroll back) |

---

**First login after stowing:** Run `source ~/.profile` or log out and back in. Modules, conda, and PATH changes only take effect on a fresh login.

**X11 / display issues in tmux:** If R graphics or GUI tools complain about `DISPLAY`, run:
```bash
update_display
```
This function (defined in `.zshrc_local`) re-reads the current X11 display variable from the tmux environment.

**R on compute nodes:** The `.Rprofile` auto-detects when you're on a compute node and starts an `httpgd` graphics server, printing SSH tunnel instructions so you can view R plots in your browser.

**`module load node` is required for Claude Code** — this is handled automatically by `.zshrc_local` after stowing, but if Claude Code isn't found, check that node is loaded: `module list`.

**Clipboard sync not working:** Check that both launchd services are loaded (`launchctl list localhost.pbcopy` and `launchctl list localhost.autossh-tunnels`). If the tunnel service is loaded but port 2224 is still not reachable on HPC, check `/tmp/autossh-tunnels.log`. The `autossh-tunnels` service maintains the tunnel automatically — you no longer need to restart your SSH connection to restore it.

**Running Snakemake:** Always do a dry run first (`-n` flag). The `local-cores: 5` limit in the profile respects RCC's login node policy — don't raise it.

**Large files:** Never commit large files to git. Put intermediates in `code/scratch/` (gitignored) and large raw data in `data/` with a `.gitignore` or as symlinks to `/project/` storage.

---

## Verification Checklist

After completing setup, run through these to confirm everything works:

- [ ] `which quarto && quarto --version` — Quarto installed and on PATH
- [ ] `which claude && claude --version` — Claude Code installed
- [ ] `which mamba && mamba --version` — Conda/mamba working
- [ ] `tmux new-session -d && tmux kill-server` — tmux available
- [ ] `snakemake --profile slurm_midway3 --list` (from a project's `code/`) — Snakemake profile recognized
- [ ] `start_agent_kernel` — kernel starts on compute node (takes ~1 min)
- [ ] Open `http://localhost:8765` in browser — plot server accessible
- [ ] In tmux: copy text, press `Ctrl+C` → paste on Mac — clipboard works
