---
name: greatlakes-compute-access
description: "UMich Great Lakes HPC only. How an agent (Claude Science, or any agent driving the cluster over ssh from the Mac) reaches Great Lakes without Okta: the `greatlakes-node` ssh alias to a compute node held by Slurm job `cs-node`, then `srun --overlap` or node-to-node ssh to work interactively inside any other job, including GPU jobs. Invoke when connecting an agent or app to Great Lakes, registering a compute host, working interactively on a compute/GPU node, or debugging `greatlakes-node` failures (no RUNNING cs-node job, Bad packet length, corrupted sftp)."
---

# Great Lakes compute access for agents

## How it works

Login nodes refuse ssh keys: every fresh login needs password + Okta number-match, which no agent can answer. Compute nodes running one of the user's jobs accept publickey. So:

```
Mac ──ControlMaster (user did Okta once)──▶ gl-login3 ──ssh -W──▶ node of job "cs-node"
```

- `greatlakes` alias: Okta-authenticated ControlMaster (`ControlPersist 24h`).
- `greatlakes-node` alias (Mac `~/.ssh/config`, source `~/dotfiles/local_dotfiles_MEDGEN_MacbookAir/.ssh/config`): asks `squeue` through the master for the node of the RUNNING job named `cs-node`, then tunnels to it.
- Key `~/.ssh/id_ed25519_gl_app` (Mac, no passphrase) is in Great Lakes `~/.ssh/authorized_keys` as `from="141.211.192.40",no-agent-forwarding,no-X11-forwarding …`. 141.211.192.40 is gl-login3, so the key works only through the master.
- Claude Science registration (Customize → Compute): host `greatlakes-node`, user `benfair`, key file `~/.ssh/id_ed25519_gl_app`.

## Safety

**Never start a fresh `greatlakes` login non-interactively.** Every inner ssh uses `-o BatchMode=yes -o ControlMaster=no`, so it reuses a live master or fails. Unanswerable Okta pushes and repeated failures can lock the UMich account. If `ssh -O check greatlakes` reports no master, stop and ask the user to run `ssh -fN greatlakes`.

## Daily routine (user)

```bash
ssh -fN greatlakes        # password + Okta, once per day
ssh greatlakes 'sbatch --account=hastingm0 --partition=standard --cpus-per-task=1 --mem=2G --time=24:00:00 --job-name=cs-node --wrap "sleep 86400"'
```

`cs-node` is only an entry point (1 core / 2 GB). Keep exactly one running: the alias takes the last match.

## Working on other nodes (CPU, GPU, big-mem)

From `cs-node` (or a login-node shell), hold the resources in a separate job, then work inside it. No ssh-config change is needed per job or node type.

```bash
J=$(sbatch --parsable --account=hastingm0 --partition=gpu --gpus=1 --cpus-per-task=4 --mem=32G \
      --time=4:00:00 --job-name=dbg-gpu --wrap "sleep infinity")
squeue -j $J -h -o "%T %N"                  # wait for RUNNING; note node
srun --jobid=$J --overlap <cmd>             # run a command inside the job
ssh <node> '<cmd>'                          # also lands inside the job (SLURM_JOB_ID set)
scancel $J                                  # release when done
```

- ssh to a node is allowed only while you have a job on it; otherwise "Connection closed".
- **GPU:** prefer `ssh <node>`, which joins the job's cgroup and so sees its GPUs. Whether an `srun --overlap` step sees the GPUs without `--gpus`/`--gres` is untested; check `nvidia-smi` before relying on it.
- Each `srun`/`ssh` call is a fresh shell (no `cd` or env carry-over). For stateful Python/R, start a kernel on the node: see the `compute-kernel` skill.
- Partitions: `gpu` (gl1000-1023), `spgpu`, `gpu_mig40`, `gpu-rtx6000`. Account `hastingm0` may use all of them. Check the queue with `sbatch --test-only …` first; GPU waits can be hours to days. GPU hours bill far above CPU, so use short walltimes for interactive holds.

## Environment facts

- `$SCRATCH` is set only in login shells (`.profile_local`), so it is empty over `greatlakes-node`. Use `/scratch/hastingm_root/hastingm0/benfair`.
- All compute nodes checked (gl1000-1001, gl3018-3021, gl3036) share one ed25519 host key, so `HostKeyAlias greatlakes-node` with `accept-new` is stable.
- Shell rc banners go to stderr (`Running  bash...`). That is harmless.

## Failure modes

| Symptom | Cause / fix |
|---|---|
| `no RUNNING cs-node job (or no live greatlakes master)` | Submit `cs-node`, or have the user reopen the master. |
| `Bad packet length <n>` / `message authentication code incorrect` | Bytes in the ssh stream. Decode `n` as hex → ASCII to see the text. Either an rc file printed to stdout, or a helper ssh inside a `ProxyCommand` lacked `-n` and read the outer handshake from stdin. |
| sftp/scp/`git fetch` over ssh fails with garbage or `protocol error: bad line length` | Something in `.bashrc`/`.shellrc_local`/conda/module hooks writes to stdout. Test: `ssh greatlakes true 2>/dev/null \| wc -c` must print 0. |
| Auth fails only for the app key | The login node's IP changed, so the `from=` restriction no longer matches. From a node, print `${SSH_CLIENT%% *}` via a main-key login and update `authorized_keys`. |
| Everything stops after ~24 h | `cs-node` walltime and `ControlPersist` both expire. Rerun the daily routine. |

## Rebuilding on a new Mac

1. `ssh-keygen -t ed25519 -N "" -C claude-science-greatlakes -f ~/.ssh/id_ed25519_gl_app`.
2. Through the master, append the restricted line above to Great Lakes `~/.ssh/authorized_keys` (back it up first).
3. Copy the `Host greatlakes-node` block into that machine's `local_dotfiles_*/.ssh/config`.
4. Verify: `ssh greatlakes-node 'hostname; echo OK'`, `echo pwd | sftp -b - greatlakes-node`, and `SSH_AUTH_SOCK= ssh greatlakes-node true` (the app key alone).
