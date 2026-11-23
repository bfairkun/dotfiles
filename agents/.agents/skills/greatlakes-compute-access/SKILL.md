---
name: greatlakes-compute-access
description: "UMich Great Lakes HPC only. How an agent (Claude Science, or any agent driving the cluster over ssh from the Mac) reaches Great Lakes without Okta: the `greatlakes-node` ssh alias, which submits a lightweight `cs-node` job on demand and lands on its node; then sized jobs for real work, `srun --overlap`/node ssh to work inside them (GPU too), and a stateful Python kernel via `kexec`. Invoke when connecting an agent or app to Great Lakes, registering a compute host, working interactively on a compute/GPU node, or debugging `greatlakes-node` failures (no live master, cs-node not RUNNING, Bad packet length, corrupted sftp)."
---

# Great Lakes compute access for agents

## How it works

Login nodes refuse ssh keys: every fresh login needs password + Okta number-match, which no agent can answer. Compute nodes running one of the user's jobs accept publickey. So:

```
Mac ──ControlMaster (user did Okta once)──▶ gl-login3 ──ssh -W──▶ node of job "cs-node"
```

- `greatlakes` alias: Okta-authenticated ControlMaster (`ControlPersist 24h`).
- `greatlakes-node` alias (Mac `~/.ssh/config`, source `~/dotfiles/local_dotfiles_MEDGEN_MacbookAir/.ssh/config`): through the master it runs `~/bin/cs-node-ensure` on the login node, then tunnels to the printed node.
- `cs-node-ensure` returns the node of the RUNNING `cs-node` job. If there is none, it submits `~/bin/cs-node.sbatch` (1 core / 2 GB, `hastingm0`) and waits up to 10 min for it to start.
- `cs-node.sbatch` **exits by itself after 30 idle minutes.** Idle means no CPU use by ssh sessions or `srun` steps in the job and no running process other than sshd/ssh-agent; an open but unused connection is idle. The next connection submits a new one. Log: `/scratch/hastingm_root/hastingm0/benfair/cs-node.log`.
- Key `~/.ssh/id_ed25519_gl_app` (Mac, no passphrase) is in Great Lakes `~/.ssh/authorized_keys` as `from="141.211.192.40",no-agent-forwarding,no-X11-forwarding …`. 141.211.192.40 is gl-login3, so the key works only through the master.
- Claude Science registration (Customize → Compute): host `greatlakes-node`, user `benfair`, key file `~/.ssh/id_ed25519_gl_app`.

## The user's only manual step

```bash
ssh -fN greatlakes        # password + Okta, once per day
```

Everything else is the agent's job: do not ask the user to submit, cancel, pull, or stow anything. **Never start a fresh `greatlakes` login non-interactively.** Every inner ssh uses `-o BatchMode=yes -o ControlMaster=no`, so it reuses a live master or fails. Unanswerable Okta pushes and repeated failures can lock the UMich account. If the master is down (`ssh -O check greatlakes` fails, or `greatlakes-node` says `no live greatlakes master`), ask the user to rerun the command above.

## Doing work: size a separate job for it

`cs-node` is a doorway, not a workspace. Run anything beyond light commands (`squeue`, `sbatch`, `ls`, small edits) in a job requested with the resources it needs:

```bash
# batch work
sbatch --account=hastingm0 --partition=standard --cpus-per-task=8 --mem=32G --time=2:00:00 script.sh
# interactive hold (CPU, GPU, big-mem), then work inside it
J=$(sbatch --parsable --account=hastingm0 --partition=gpu --gpus=1 --cpus-per-task=4 --mem=32G \
      --time=4:00:00 --job-name=dbg-gpu --wrap "sleep infinity")
squeue -j $J -h -o "%T %N"                  # wait for RUNNING; note node
ssh <node> '<cmd>'                          # lands inside the job (its cgroup, so its GPUs)
srun --jobid=$J --overlap <cmd>             # alternative to ssh
scancel $J                                  # release as soon as done
```

- ssh to a node is allowed only while you have a job on it; otherwise "Connection closed".
- **GPU:** prefer `ssh <node>`. Whether an `srun --overlap` step sees the GPUs without `--gpus`/`--gres` is untested; check `nvidia-smi` before relying on it.
- Partitions: `standard`, `largemem`, `gpu` (gl1000-1023), `spgpu`, `gpu_mig40`, `gpu-rtx6000`. Account `hastingm0` may use all of them. Check the wait with `sbatch --test-only …` first; GPU waits can be hours to days, and GPU hours bill far above CPU, so keep interactive holds short.
- Each `ssh`/`srun` call is a fresh shell (no `cd` or env carry-over). For stateful work, use a kernel (next section).
- Sized jobs are separate from `cs-node`: they keep running if `cs-node` idles out, and they do not keep it alive.

## Interactive Python kernel (stateful, with plots)

This works over a plain ssh host such as `greatlakes-node`: no port forward and no MCP server. The kernel binds its node's cluster IP, and `kexec` connects to it from any Great Lakes node. Use full paths, because `~/bin` is not on `PATH` in non-login shells.

```bash
~/bin/start_agent_kernel --account hastingm0 --mem 16G --time 4:00:00 --cpus 4   # blocks until ready
~/bin/kexec --status
~/bin/kexec <<'PY'
import pandas as pd; df = pd.read_parquet("/scratch/...")   # stays loaded for later calls
PY
~/bin/kexec <<'PY'
df.plot(); plt.show()          # prints: [image] /scratch/hastingm_root/hastingm0/benfair/kexec_out/<ts>.png
PY
echo "get <that path> /local/dir/" | sftp -b - greatlakes-node      # fetch the plot to show the user
scancel <kernel jobid>          # when done
```

- Size the kernel job for the data (`--mem`, `--cpus`, `--time`). It is a separate job, so it survives `cs-node` idling out.
- Connection file: `/scratch/hastingm_root/hastingm0/benfair/agent_kernel.json`. `start_agent_kernel` **deletes and replaces it**, so first check `squeue --me -n agent_kernel.sbatch` for a kernel another session is using. For a second kernel, write your own `--wrap` with another file (see `compute-kernel`) and pass `kexec -f <file>`.
- `kexec` exit codes: 0 ok; 1 the code raised (traceback on stderr); 2 the kernel is unreachable (job ended?); 124 timeout (`-t`, default 600 s), after which the code keeps running in the kernel.
- Use it for exploration. Move finished analyses into scripts or notebooks run as batch jobs.
- Claude Code sessions on the login node can instead attach to the same kernel through the jupyter-kernel MCP (`compute-kernel` skill).

## Environment facts

- **Compute nodes reach the internet only through the ARC-TS HTTP proxy.** Run `source /etc/profile.d/http_proxy.sh` first; then HTTPS (pip, conda, curl, `git` over `https://github.com/...`) works. ssh to github.com (port 22) is blocked, so `git@github.com:` remotes hang. For those, use `git pull https://github.com/<owner>/<repo>.git main`. Pushing needs ssh: run it on the login node from the Mac (`ssh -n -o BatchMode=yes -o ControlMaster=no greatlakes '<cmd>'`), because a session on `greatlakes-node` cannot reach a login node without Okta.
- `$SCRATCH` is set only in login shells (`.profile_local`), so it is empty over `greatlakes-node`. Use `/scratch/hastingm_root/hastingm0/benfair`.
- All compute nodes checked (gl1000-1001, gl3018-3021, gl3036) share one ed25519 host key, so `HostKeyAlias greatlakes-node` with `accept-new` is stable.
- Shell rc banners go to stderr (`Running  bash...`). That is harmless.

## Failure modes

| Symptom | Cause / fix |
|---|---|
| `greatlakes-node: no live greatlakes master` | Ask the user to run `ssh -fN greatlakes`. |
| `greatlakes-node: ERROR: cs-node still not RUNNING after 600s` | Queue is busy; the job stays pending and the next connection reuses it. Check `ssh -n -o BatchMode=yes -o ControlMaster=no greatlakes 'squeue --me -n cs-node -o "%T %R"'`. |
| Connection drops mid-session after a quiet spell | `cs-node` idled out (see its log). Reconnect; a new one is submitted. |
| `Bad packet length <n>` / `message authentication code incorrect` | Bytes in the ssh stream. Decode `n` as hex → ASCII to see the text. Either an rc file printed to stdout, or a helper ssh inside a `ProxyCommand` lacked `-n` and read the outer handshake from stdin. |
| sftp/scp/`git fetch` over ssh fails with garbage or `protocol error: bad line length` | Something in `.bashrc`/`.shellrc_local`/conda/module hooks writes to stdout. Test: `ssh greatlakes true 2>/dev/null \| wc -c` must print 0. |
| Auth fails only for the app key | The login node's IP changed, so the `from=` restriction no longer matches. From a node, print `${SSH_CLIENT%% *}` via a main-key login and update `authorized_keys`. |

## Setting this up for another user

The pieces live in the public repo `github.com/bfairkun/dotfiles`. Another user doesn't need these dotfiles; copy the pieces and change the user-specific values. The steps below are written for an agent on her Mac to carry out. Her only manual steps are Okta logins and approving prompts.

1. **Mac ssh config.** Add a `greatlakes` block with ControlMaster: copy `Host greatlakes` from `local_dotfiles_MEDGEN_MacbookAir/.ssh/config`, change `User`, and drop the `LocalForward`/`RemoteForward` lines she doesn't need. Keep `ControlMaster auto`, `ControlPath`, and `ControlPersist 24h`. Then copy the `Host greatlakes-node` block, changing `User`. She opens the master once with `ssh -fN greatlakes`.
2. **Great Lakes scripts.** Copy `cs-node-ensure`, `cs-node.sbatch`, `kexec`, `start_agent_kernel`, and `agent_kernel.sbatch` from `local_dotfiles_GreatLakesUMich/bin/` into her `~/bin/`, and make them executable. If her Slurm account isn't `hastingm0`, change the account and the `/scratch/hastingm_root/hastingm0` defaults. Point `kexec` at a Python env with `jupyter_client` + `ipykernel` (`KEXEC_PYTHON`, or edit `PY_GENERAL`). Check `start_agent_kernel --env` and the conda path in `agent_kernel.sbatch` against her setup.
3. **App key.** Generate `~/.ssh/id_ed25519_gl_app` on her Mac. Through her master, append `from="141.211.192.40",no-agent-forwarding,no-X11-forwarding <pubkey>` to her Great Lakes `~/.ssh/authorized_keys`. If her ControlMaster uses a login node other than gl-login3, use that node's IP, which `hostname -I` prints there.
4. **Clean stdout.** `ssh greatlakes true 2>/dev/null | wc -c` must print 0. Otherwise move rc-file `echo`s to stderr or guard them with `[[ $- == *i* ]]`.
5. Register in Claude Science (host `greatlakes-node`, her user, key file `~/.ssh/id_ed25519_gl_app`), then run the verification below.

## Rebuilding on a new Mac

1. `ssh-keygen -t ed25519 -N "" -C claude-science-greatlakes -f ~/.ssh/id_ed25519_gl_app`.
2. Through the master, append the restricted line above to Great Lakes `~/.ssh/authorized_keys` (back it up first).
3. Copy the `Host greatlakes-node` block into that machine's `local_dotfiles_*/.ssh/config`.
4. Verify: `ssh greatlakes-node 'hostname; echo OK'`, `echo pwd | sftp -b - greatlakes-node`, and `SSH_AUTH_SOCK= ssh greatlakes-node true` (the app key alone).
