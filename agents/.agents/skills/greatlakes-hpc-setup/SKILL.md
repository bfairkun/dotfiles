---
name: greatlakes-hpc-setup
description: "UMich Great Lakes HPC only. Full dotfiles setup guide for new accounts on gl-login*.arc-ts.umich.edu. Invoke when setting up a new Great Lakes account, onboarding a colleague, or debugging setup quirks on this cluster."
argument-hint: "[phase or topic]"
---

# Great Lakes HPC — New Account Setup

Cluster: `gl-login*.arc-ts.umich.edu`, user home: `/home/<uniqname>`
Dotfiles repo: `git@github.com:bfairkun/dotfiles.git` (stow-based)

## Applying this skill — agent behavior (read first)

This goal: set up a fresh Great Lakes account to behave like the maintainer's environment
(comfortable shell, conda/micromamba, tmux that survives disconnects, supporting tools). The
person at the keyboard may be brand new to HPC.

The reference below is terse on purpose. **When you apply it, do the opposite — explain
generously:**

1. **Before each step, say what it does and why, in plain language**, then run it. Never paste
   an opaque command. The one-line "**Why**" on each phase is your script — expand on it.
2. **Optional phases are marked `(optional)`. Offer them, don't assume them.** Briefly give the
   purpose and tradeoff, then let the user decline if they don't need it (e.g. skip vim if they
   don't use vim, skip Quarto if they won't render notebooks). Required phases (clone, stow,
   shell, conda/micromamba) are not opt-out — explain those too, but proceed.
3. **Run phases in order.** Later phases depend on earlier ones (e.g. `~/bin` must be on PATH
   before micromamba lands there).

Phases: clone dotfiles → stow → shell → vim/fzf → conda/micromamba/py_general → quarto →
MCPs & secrets.

---

## Phase 0: Fork or clone the dotfiles repo

**Why:** "Dotfiles" are the hidden config files in your home directory (`.bashrc`,
`.gitconfig`, `.tmux.conf`, …) that control how your shell and tools behave. Keeping them in
a git repo means a new machine or new HPC account is one `git clone` away from feeling like
home, instead of an afternoon of re-tweaking. This repo bundles all of them plus some helper
scripts.

**Fork vs. clone — pick one:**

- **Fork** (recommended if you have a GitHub account, or are willing to make one now):
  Go to `https://github.com/bfairkun/dotfiles`, click **Fork**. You now own a copy at
  `github.com/<you>/dotfiles`. Clone *that*. This is the right choice if you ever want to
  **git-track your own dotfiles** — the moment you change a config to suit yourself, your
  files diverge from the maintainer's, and a fork is the only way to commit and keep those
  changes under version control.
- **Just clone** (fine for now if you don't have a GitHub account and don't feel like making
  one): clone the maintainer's repo directly. You'll get everything and it'll work. The
  catch: you can `git pull` updates but you **cannot commit your own changes upstream**, and
  if your local edits diverge you'll eventually hit merge friction. If that day comes, make a
  fork then. Forking later is easy; you won't lose work.

Set the clone URL accordingly in Phase 1 (`<you>` for a fork, `bfairkun` for a plain clone).

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

**Why stow:** The repo is organized into "packages" — `bash/`, `tmux/`, `bin/`, etc. — each
mirroring where its files belong under `~`. **GNU Stow** is a tiny tool that creates
*symlinks* from your home directory into the repo. So `~/.bashrc` becomes a link pointing at
`~/dotfiles/bash/.bashrc`. Edit the file in the repo, and `~` sees the change instantly; the
single source of truth stays git-tracked. Nothing is copied, so there's no "which copy is
real?" confusion.

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

### Using stow day-to-day (and a sharp edge to avoid)

- **Add the links for a package:** `stow <package>` (run from `~/dotfiles`). Safe to re-run —
  it skips links that already exist correctly and only creates missing ones. This is also how
  you pick up **new files after a `git pull`**: just `stow <package>` again.
- **Remove a package's links:** `stow -D <package>`.
- **⚠️ Do NOT use `stow --restow` / `stow -R` with this stow (v1.3.2).** That option is broken
  in this old version: instead of relinking, it runs away — it crawls the filesystem and
  balloons to multiple GB of RAM, which the login node's 4 GB cgroup will eventually kill (or
  you'll have to `kill` it by hand). If you genuinely need to refresh links (e.g. a file was
  *deleted* upstream and you want the stale symlink gone), do it explicitly:
  `stow -D <package> && stow <package>`. For the common case (pull added new files), plain
  `stow <package>` is all you need.

---

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
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | tar -xvj -C ~/bin/ --strip-components=1 bin/micromamba
```

`~/bin` is already in PATH via `.profile_local`. micromamba is a single binary — no conda
required to install it.

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

## Phase 9: Secrets and MCPs (optional — set up the integrations you'll use)

**Why:** MCPs let agents reach external services (a live Jupyter kernel, Slack, Google
Drive/Gmail/Calendar). Most need a per-machine secret or auth step, so they're **not** carried
by stow — set up only the ones the user wants. Offer each; skip what they don't need.

### 9a. The `~/.secrets` file (API keys and tokens)

**Why:** `.bashrc_local` and `.zshrc_local` both do `[ -f ~/.secrets ] && source ~/.secrets`,
so anything exported there is available to interactive shells and agent shell tools
tool after `source ~/.secrets`). It lives in `$HOME`, never in the repo, so secrets are never
git-tracked. Create it `chmod 600`:

```bash
umask 077
cat > ~/.secrets <<'EOF'
# Exported secrets — sourced by .bashrc_local / .zshrc_local. Never commit this file.
export ALPHAGENOME_API_KEY="..."          # AlphaGenome API (alphagenome_utils)
export SLACK_PLOT_TOKEN="xoxb-..."         # Slack bot token for post_plot_to_slack (9d)
export SLACK_PLOT_CHANNEL="UXXXXXXXX"      # Slack user ID (DM self) or channel ID for plots
# export ANTHROPIC_API_KEY="sk-ant-..."    # only if running Claude with a raw API key
EOF
chmod 600 ~/.secrets
```

The maintainer's file currently exports: `ALPHAGENOME_API_KEY`, `SLACK_PLOT_TOKEN`,
`SLACK_PLOT_CHANNEL`. Add only the keys the user actually has — leave the rest out.

### 9b. Jupyter-kernel MCP (local, already wired up by stow)

The only MCP whose code lives on this machine. The script ships in
`~/bin/jupyter_kernel_mcp.py`; register it as a user-scope stdio server in each client.
See the `jupyter-kernel` skill.

### 9c. Account/plugin MCPs — Google Drive, Gmail, Calendar, Slack (remote, no local code)

**Why:** These are **remote** MCP servers (HTTP endpoints hosted by Google/Slack) — no code is
downloaded here. They differ only in how they're registered, and **each machine must
authenticate once** even though the registration travels:

- **Google Drive / Gmail / Calendar** — account-level **connectors**. Enable them once in the
  Claude desktop app or at claude.ai (Settings → Connectors). They then appear in Claude Code
  anywhere you're signed in with that Anthropic account. Nothing to configure on the cluster.
- **Slack** — registered as the `slack@claude-plugins-official` **plugin**, already enabled in
  the tracked `settings.json`, so it travels with the dotfiles. But the OAuth token is
  per-machine: in Claude Code run `/mcp`, pick `slack`, and complete authentication. (This
  Slack MCP — for reading/searching Slack — is **separate** from the plot-upload script in 9d.)

Verify what's live on the current machine: `claude mcp list`.

### 9d. Slack plot upload — `post_plot_to_slack` (optional, great for Remote Control)

**Why this exists:** plots saved to the agent-plots dir are normally viewed in a browser over
an SSH tunnel. But when driving Claude from **Remote Control on a phone** (e.g. voice-commanding
Claude while walking), there's no tunnel and no browser — you can't see the plots. Pushing a
plot straight into a Slack DM means it shows up on your phone instantly. It's purely about a
nicer remote/mobile experience.

This is a standalone script (`~/bin/post_plot_to_slack`), **not** the Slack MCP. It uses a Slack
**bot token**, independent of the 9c plugin auth:

1. Set `SLACK_PLOT_TOKEN` (`xoxb-...`) and `SLACK_PLOT_CHANNEL` in `~/.secrets` (9a). The token
   is a Slack **bot** token; the bot needs scopes `files:write`, `chat:write`, and `im:write`
   (the last for DMing yourself). Alternatively write the token to `~/.config/slack_plot_token`
   and the target to `~/.config/slack_plot_channel` (both `chmod 600`).
2. `SLACK_PLOT_CHANNEL` can be your own Slack **user ID** (starts `U`, e.g. `UC94MAVLL`) to DM
   yourself, or a **channel ID** (starts `C`) the bot has been invited to (`/invite @yourbot`,
   else `not_in_channel`).
3. Test (remember the Bash tool is non-interactive — source secrets first):
   ```bash
   source ~/.secrets
   post_plot_to_slack /path/to/plot.png          # optional 2nd arg overrides the channel
   ```
   Success prints `posted <file> to Slack channel <id>` and the image appears in that DM/channel.

Verified working on gl-login3 (2026-06): DM to self via user ID resolves through
`conversations.open` to a `D...` DM channel and the upload lands.

---

## Known Quirks and Gotchas

### stow --restow is broken (v1.3.2)
See Phase 1. Never use `--restow`/`-R` — it runs away and eats GBs of RAM until killed. Use
plain `stow <package>` to add/refresh links, or `stow -D <package> && stow <package>` to force
a clean relink.

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

### No crontab on Great Lakes
The cluster does not provide per-user crontab; sourcing a startup script that calls `crontab`
prints an error. Startup scripts here must **not** register cron jobs (this is why
`.profile_local` carries no crontab block). If you need periodic work, use a SLURM job or a
long-running tmux loop instead.

### conda not in PATH for non-interactive shells
The conda shell function is only initialized in interactive bash via `.bashrc_local`.
For scripts, SLURM jobs, and agent shell tools, use full paths:
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
