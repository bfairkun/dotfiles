---
name: greatlakes-hpc-setup
description: "UMich Great Lakes HPC only. Full dotfiles setup guide for new accounts on gl-login*.arc-ts.umich.edu. Invoke when setting up a new Great Lakes account, onboarding a colleague, or debugging setup quirks on this cluster."
---

# Great Lakes HPC — New Account Setup

Cluster: `gl-login*.arc-ts.umich.edu`, user home: `/home/<uniqname>`
Dotfiles repo: `git@github.com:bfairkun/dotfiles.git` (stow-based)

## Workflow

Run the setup phases in order. Explain each briefly in plain language, adapting detail to
an HPC beginner when needed. Offer optional phases unless the user already requested them.
For a partial setup request, run only the relevant phases and missing prerequisites.

- For optional secrets, MCPs, or Slack uploads, read [integrations](references/integrations.md).
- For tmux/shell failures, account/partition details, network proxy, or SSH configuration,
  read [troubleshooting](references/troubleshooting.md).

## Phase 0: Fork or clone the dotfiles repo

Use the user's fork if they want to maintain and push their own configurations; otherwise
clone `bfairkun/dotfiles`. Local commits work in either case; pushing to the maintainer's
repository requires access. Set the clone URL accordingly in Phase 1.

### SSH key for GitHub

**Why:** Great Lakes blocks the GUI password prompt that HTTPS git push relies on, so use an
SSH key. (Cloning over HTTPS read-only also works if you never push.)

```bash
cat ~/.ssh/id_ed25519.pub 2>/dev/null || cat ~/.ssh/id_rsa.pub   # generate with ssh-keygen -t ed25519 if neither exists
# Paste the printed key into https://github.com/settings/keys
```

Note: **no mosh** on Great Lakes (unlike Midway) — plain SSH only:
`ssh <uniqname>@greatlakes.arc-ts.umich.edu`

---

## Phase 1: Clone the dotfiles and link them in with stow

Stow links package contents into `$HOME`; edit the source files in `~/dotfiles`.

```bash
cd ~
git clone git@github.com:bfairkun/dotfiles.git    # or git@github.com:<you>/dotfiles.git for your fork
cd dotfiles
# The repo ships a stow binary; run it with perl since nothing is on PATH yet:
perl local_dotfiles_RCCMidwayGeneral/bin/stow sh bash zsh ohmyzsh fzf git tmux vim config bin agents local_dotfiles_GreatLakesUMich
```

**Stow packages for Great Lakes** (this exact list):
`sh bash zsh ohmyzsh fzf git tmux vim config bin agents local_dotfiles_GreatLakesUMich`

Do **not** stow other machines' packages (`local_dotfiles_RCCMidway*`,
`local_dotfiles_Midway*`, `local_dotfiles_*MacbookAir*`, `Library`, etc.) — they hold
config for different computers and will create symlinks you don't want here.

After this step `~/bin/stow` exists (the `bin`/GreatLakes packages provide it), so from now on
you can just type `stow` instead of `perl …/stow`.

Use `stow <package>` to add missing links, including after a pull. Avoid `--restow`/`-R`:
this bundled version (1.3.2) has been observed to loop and exhaust memory. If links must be
removed, inspect conflicts before `stow -D <package> && stow <package>`; a failed second
command leaves the package unlinked.

## Phase 2: Shell — stay in bash

**Why:** You might prefer zsh, but on Great Lakes you can't make the switch stick.

Great Lakes uses LDAP for user accounts. `chsh` changes to local `/etc/passwd` are
overridden by LDAP and do not persist. **Login shell stays bash.** Do not attempt to
change it permanently — it will revert.

All interactive config goes in `.bashrc_local`. The `zsh`/`ohmyzsh` stow packages are
harmless to keep (in case zsh is invoked manually) but bash is the working shell.

---

## Phase 3: Install vim plugins (optional — skip if the user doesn't use vim)

**Why:** The vim config expects a set of plugins (and the gruvbox colorscheme). They have to
be fetched once. vim-plug crashes at startup if gruvbox is missing, so the first
`PlugInstall` must run under a fake TTY to dodge the crash:

```bash
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
script -q -c "vim +PlugInstall +qa" /dev/null
```

---

## Phase 4: Install fzf (optional but recommended)

**Why:** fzf is a fuzzy finder — it powers `Ctrl-R` history search and fuzzy file completion
that the shell config wires up.

```bash
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install --all
```

---

## Phase 5: Install miniconda

**Why:** conda manages Python/R environments. It's the baseline; the heavy environment
solving happens with micromamba (next phase) because of the login-node memory limit.

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init bash
```

**Accept conda ToS** (required before any env create — conda refuses otherwise):
```bash
~/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
~/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

---

## Phase 6: Install micromamba

**Why:** Login nodes have a **4 GB per-user memory cap**. conda's solver for a big
environment blows past that and gets silently killed. micromamba is a fast, standalone C++
reimplementation of conda's solver — same channels, far less memory — so it's the tool we
actually create environments with.

```bash
mkdir -p ~/.local/bin &&
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | tar -xvj -C ~/.local/bin/ --strip-components=1 bin/micromamba
```

`~/.local/bin/micromamba` matches `MAMBA_EXE` in the machine's `.bashrc_local`;
`~/.local/bin` is on PATH via `.profile_local`.

---

## Phase 7: Create the py_general conda environment (optional — only if doing Python/R analysis)

**Why:** `py_general` is the default environment for Python notebooks and analysis. It's
large, so even micromamba's solve exceeds 4 GB — it **must run on a SLURM compute node**, not
the login node.

Strip the pip section first (use home dir, not /tmp — /tmp is node-local):
```bash
pip_line=$(grep -n '^\s*pip:' ~/dotfiles/other/conda_minimal_yamls/py_general.yaml | head -1 | cut -d: -f1)
head -$((pip_line - 1)) ~/dotfiles/other/conda_minimal_yamls/py_general.yaml > ~/py_general_no_pip.yaml
```

Then run on a compute node — use `--channel-priority flexible` to avoid a solver conflict
with `bioconda::logomaker` under strict channel priority:
```bash
srun --account=hastingm0 --partition=standard --cpus-per-task=4 --mem=16G --time=2:00:00 \
  ~/.local/bin/micromamba env create -f ~/py_general_no_pip.yaml -y --channel-priority flexible \
  > ~/mamba_create.log 2>&1
tail -f ~/mamba_create.log
```

Then pip install the remaining packages (also on a compute node):
```bash
srun --account=hastingm0 --partition=standard --cpus-per-task=2 --mem=4G --time=0:30:00 \
  /home/$USER/micromamba/envs/py_general/bin/pip install alphagenome==0.5.1 pikachu-chem==1.1.5
# my-utils==0.1.0 does NOT exist on PyPI (only 0.0.1) — install from GitHub:
/home/$USER/micromamba/envs/py_general/bin/pip install git+https://github.com/bfairkun/my_utils.git
# or if local dev copy exists: pip install -e ~/Documents/repos_not_projects/my_utils/
```

**Gotchas**:
- `/tmp` is node-local — always save intermediate files to `~/` or scratch
- `bioconda::logomaker` conflicts under `channel_priority: strict`; use `--channel-priority flexible`
- `my-utils==0.1.0` is not on PyPI; install from local repo or skip until repo is cloned

---

## Phase 8: Install Quarto (optional — only if rendering .qmd notebooks)

**Why:** Quarto renders the `.qmd` analysis notebooks to HTML. It isn't available as a
module, so install it into `~/.local/`:

```bash
VER=$(curl -sLI https://github.com/quarto-dev/quarto-cli/releases/latest | grep -i location | grep -oP 'v\K[0-9.]+')
wget -q "https://github.com/quarto-dev/quarto-cli/releases/download/v${VER}/quarto-${VER}-linux-amd64.tar.gz" -O /tmp/quarto.tar.gz
tar -xzf /tmp/quarto.tar.gz -C ~/.local/
ln -sf ~/.local/quarto-${VER}/bin/quarto ~/.local/bin/quarto
quarto --version
```

`~/.local/bin` is already in PATH via `.profile_local`.

---
