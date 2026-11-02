# Great Lakes HPC (UMich) — Machine-Specific Notes

## Key Facts

- **Login shell**: bash (LDAP-managed, `chsh` doesn't persist). All interactive config in `.bashrc_local`.
- **Login node memory**: 4 GB per-user cgroup limit — heavy work gets killed silently. Use SLURM.
- **`py_general`** lives in `~/micromamba/envs/py_general`; findable by conda via `envs_dirs` in `.condarc`.

## SLURM

Account: **`hastingm0`** (Hastings lab) — always pass `--account hastingm0`.
Partitions: `standard` (general), `largemem`, `gpu`.
Find accounts: `sacctmgr show user $USER withassoc format=account -P` (`my_accounts` fails non-interactively).

```bash
srun --account=hastingm0 --partition=standard --cpus-per-task=4 --mem=16G --time=4:00:00 --pty bash
```

## Agent Reference

| Key | Value |
|---|---|
| `MACHINE` | UMich Great Lakes HPC |
| `HOSTNAME_VERIFY` | `echo $HOST` matches `gl-login*` |
| `BRAIN_PATH` | `/nfs/turbo/umms-hastingm/benfair/repos_not_projects/brain` _(verify/clone on machine)_ |
| `AGENT_PLOTS` | `~/agent_plots` |
| `KERNEL_CF` | `~/agent_kernel.json` (scratch not provisioned yet) |
| `STATE_MD` | `~/agent_plots/state.md` |
| `STATE_JSON` | `~/agent_plots/state.json` |
| `PROJECTS_DIR` | `/nfs/turbo/umms-hastingm/benfair/` |
| `SLURM_ACCOUNT` | `hastingm0` |

> **Note on state files**: kernel runs on a compute node; `/tmp` there is node-local. Write state files directly to `~/agent_plots/` (NFS-shared) — not to `/tmp/`. No symlinks needed.

## Local Clipboard

`pbcopy_to_local` is in PATH (`~/bin/`). Pipes stdin over the SSH reverse tunnel (port 2224) to the Mac's `pbcopy` daemon.

Use it whenever outputting something the user needs to paste — auth URLs, tokens, etc.:

```bash
echo "https://auth.example.com/device?code=XXXX" | pbcopy_to_local
```
