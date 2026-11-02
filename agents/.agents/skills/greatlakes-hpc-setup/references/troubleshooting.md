## Known Quirks and Gotchas

### stow --restow is broken (v1.3.2)
See [Stow setup](../SKILL.md#phase-1-clone-the-dotfiles-and-link-them-in-with-stow). Never use `--restow`/`-R` — it runs away and eats GBs of RAM until killed. Use
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
