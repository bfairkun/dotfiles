---
name: greatlakes-hpc-setup
description: "UMich Great Lakes HPC only. Full dotfiles setup guide for new accounts on gl-login*.arc-ts.umich.edu. Invoke when setting up a new Great Lakes account, onboarding a colleague, or debugging setup quirks on this cluster."
argument-hint: "[phase or topic]"
---

# Great Lakes HPC — New Account Setup

Cluster: `gl-login*.arc-ts.umich.edu`, user home: `/home/<uniqname>`
Dotfiles repo: `git@github.com:bfairkun/dotfiles.git` (stow-based)

---

## Phase 0: Prerequisites / SSH

- SSH in: `ssh <uniqname>@greatlakes.arc-ts.umich.edu`
- No mosh available (unlike Midway). SSH only.
- Set up SSH key for GitHub (HTTPS push is blocked by GUI askpass errors):
  ```bash
  cat ~/.ssh/id_rsa.pub   # or id_ed25519.pub
  # Add to https://github.com/settings/keys
  git remote set-url origin git@github.com:bfairkun/dotfiles.git
  ```

---

## Phase 1: Clone dotfiles and stow

```bash
cd ~
git clone git@github.com:bfairkun/dotfiles.git
cd dotfiles
perl local_dotfiles_RCCMidwayGeneral/bin/stow sh bash zsh ohmyzsh fzf git tmux vim config bin claude local_dotfiles_GreatLakesUMich
```

**Stow packages for Great Lakes**: `sh bash zsh ohmyzsh fzf git tmux vim config bin claude local_dotfiles_GreatLakesUMich`
(Do NOT stow `local_dotfiles_RCCMidway*` or `local_dotfiles_MyMacbookAir`)

The repo includes a stow binary at `local_dotfiles_RCCMidwayGeneral/bin/stow`. Use `perl` to run it directly before anything is on PATH.

---

## Phase 2: Shell — stay in bash

Great Lakes uses LDAP for user accounts. `chsh` changes to local `/etc/passwd` are
overridden by LDAP and do not persist. **Login shell stays bash.** Do not attempt to
change it permanently — it will revert.

All interactive config goes in `.bashrc_local`. The `zsh`/`ohmyzsh` stow packages are
harmless to keep (in case zsh is invoked manually) but bash is the working shell.

---

## Phase 3: Install vim plugins

vim-plug crashes at startup if the gruvbox colorscheme is missing — PlugInstall must
be run with a fake TTY to avoid the crash:
```bash
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
script -q -c "vim +PlugInstall +qa" /dev/null
```

---

## Phase 4: Install fzf

```bash
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install --all
```

---

## Phase 5: Install miniconda

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
bash /tmp/miniconda.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init bash
```

**Accept conda ToS** (required before any env create):
```bash
~/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
~/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

---

## Phase 6: Install micromamba

Login nodes have a **4 GB per-user cgroup v2 memory limit**. `conda env create` for
large environments (e.g. `py_general`) is killed during solving. Use micromamba instead:

```bash
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | tar -xvj -C ~/bin/ --strip-components=1 bin/micromamba
```

`~/bin` is already in PATH via `.profile_local`. micromamba is a standalone C++ binary —
no conda required to install it.

---

## Phase 7: Create py_general conda environment

**Do not use `conda env create` for large envs on login nodes — it will be killed.**
**Must run on a SLURM compute node** (even micromamba's two solve passes exceed 4 GB).

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

## Phase 8: Install Quarto

Quarto is not available as a module. Install to `~/.local/`:
```bash
VER=$(curl -sLI https://github.com/quarto-dev/quarto-cli/releases/latest | grep -i location | grep -oP 'v\K[0-9.]+')
wget -q "https://github.com/quarto-dev/quarto-cli/releases/download/v${VER}/quarto-${VER}-linux-amd64.tar.gz" -O /tmp/quarto.tar.gz
tar -xzf /tmp/quarto.tar.gz -C ~/.local/
ln -sf ~/.local/quarto-${VER}/bin/quarto ~/.local/bin/quarto
quarto --version
```

`~/.local/bin` is already in PATH via `.profile_local`.

---

## Known Quirks and Gotchas

### tmux: system version is 2.7 (too old)
System tmux at `/usr/bin/tmux` is version 2.7. The dotfiles tmux config uses features
requiring 2.9+ (`status-style`, `window-status-current-style`, `#{?window_start_flag}`).
**Fix**: `.profile_local` loads `module load tmux/3.3a` before the tmux auto-attach.
The tmux version-specific config dir `~/.tmux/3.3a/` is a symlink to `3.2a/` in the
dotfiles repo — do not create a new file, just keep the symlink.
Always kill the old tmux server after first login to get the new version:
```bash
tmux kill-server
```

### TMOUT readonly error breaks shell
`/etc/profile.d/tmout.sh` does `declare -r TMOUT=86400`. `/etc/profile` (for bash login
shells) explicitly sources `/etc/bashrc`, which also sources `profile.d/` — double-sourcing
makes TMOUT readonly, then any subsequent bash login shell crashes with:
`/etc/profile.d/tmout.sh:10: read-only variable: TMOUT`
**Fix**: Kill the tmux server (`tmux kill-server`) and start a fresh session. This resets
the inherited shell environment. No permanent fix — recurs if a bash login shell is
started inside a tmux that already has TMOUT readonly.

### conda not in PATH for non-interactive shells
The conda shell function is only initialized in interactive bash via `.bashrc_local`.
For scripts, SLURM jobs, and the Claude Code Bash tool, use full paths:
- `~/miniconda3/bin/conda`
- `~/.local/bin/micromamba`
`~/miniconda3/bin` is in PATH for all shells via `.profile_local`.

### Login node 4 GB memory cgroup limit
Path: `/sys/fs/cgroup/user.slice/user-$(id -u).slice/memory.max`
Affects: conda solver, large Python scripts, Jupyter kernels.
**Always use SLURM compute nodes for real work.** Interactive session:
```bash
srun --account=hastingm0 --partition=standard --cpus-per-task=4 --mem=16G --time=4:00:00 --pty bash
```

### SLURM account and partitions
Lab SLURM account: **`hastingm0`** (Hastings lab). Always pass `--account hastingm0` to sbatch/srun.
Find accounts: `sacctmgr show user $USER withassoc format=account -P` (`my_accounts` fails non-interactively).

Partitions:
- `standard` — general CPU work
- `largemem` — high-memory jobs
- `gpu` — GPU jobs

Storage: `/scratch/$USER` (must be provisioned; not available by default for new accounts), `/nfs/turbo/<labname>/`

Interactive session:
```bash
srun --account=hastingm0 --partition=standard --cpus-per-task=4 --mem=16G --time=4:00:00 --pty bash
```

### Internet access from compute nodes

Compute nodes don't have internet by default but can reach the web via the ARC-TS proxy.
Add this line to sbatch scripts **after** the SLURM options (already in `agent_kernel.sbatch`):

```bash
source /etc/profile.d/http_proxy.sh
```

This sets `http_proxy=http://proxy1.arc-ts.umich.edu:3128/` and related vars.
**Do not hardcode the proxy hostname** — the system file picks the correct one (`proxy1`, not `proxy`).

Verified 2026-06: `curl` and Python `urllib` work from compute nodes after sourcing this file.

### No mosh
mosh is not available on Great Lakes. SSH only.

### Mac SSH config
Add to `~/dotfiles/local_dotfiles_MyMacbookAir/.ssh/config`:
```
Host greatlakes
  HostName greatlakes.arc-ts.umich.edu
  User <uniqname>
  RemoteForward 2224 localhost:2224
  LocalForward 8765 localhost:8765
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 10m
  ServerAliveInterval 60
```
