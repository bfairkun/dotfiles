---
name: globus-transfer
description: "Transfer data with globus-cli between clusters (UChicago Midway, UMich Great Lakes, any Globus collection). Invoke for moving directories between clusters, globus-cli setup, or Globus failures (consent, LOGIN_DENIED, expired)."
---

# Globus transfers (UChicago RCC ↔ UMich Great Lakes)

## Environment

`globus-cli` is not in the default envs. Install once:

```
mamba create -y -p /project/yangili1/bjf79/conda_envs/agent_globus -c conda-forge python=3.12 globus-cli
```

Activate by full path — `/project/yangili1/bjf79/conda_envs/` is not in `envs_dirs`, so
`mamba activate agent_globus` fails:

```
mamba activate /project/yangili1/bjf79/conda_envs/agent_globus
```

Note `globus version` (subcommand), not `--version`. Tokens live in `~/.globus/`, shared
across both Midway login nodes, so one login covers any session on either node.

## Collection IDs

| Collection | ID |
|---|---|
| UChicago RCC Midway3 | `2fde89c0-6fb4-11eb-8c47-0eb1aa8d4337` |
| UChicago RCC Midway (Midway2) | `af7bda53-6d04-11e5-ba46-22000b92c6ec` |
| umich#greatlakes | `454f457e-a41b-4807-8775-d132f15a228f` |
| UMich ARC Non-Sensitive Turbo | `8c185a84-5c61-4bbc-b12b-11430e20010f` |

Two entries share the name "UChicago RCC Midway3". `c493e978-…` is the GCS **endpoint**;
`2fde89c0-…` is the **mapped collection** and is the one to transfer against. Confirm with
`globus endpoint search "UChicago RCC"` — the collection's owner column shows the endpoint's
client ID.

Midway3 exposes real absolute paths, so `/project/…` and `/project2/…` work directly.

**Prefer `umich#greatlakes` over the Turbo collection.** Great Lakes mounts Turbo at
`/nfs/turbo/<volume>/`, and the standalone Turbo collection has been observed to reject
logins outright (see Failure modes). Great Lakes also reaches `/home/<uniqname>` and `/scratch`.

UMich lab volume paths are recorded in `~/dotfiles/local_dotfiles_GreatLakesUMich/.agents/AGENTS.local.md`
(`PROJECTS_DIR`, `BRAIN_PATH`). Grep there before guessing volume names — they are abbreviated
and truncated in non-obvious ways.

## Setup, once per account

Both steps need a browser and cannot be automated from a login node — hand them to the user.

1. **Link identities.** A transfer authenticates to both ends from one Globus account, so
   separate institutional logins cannot do a cross-site transfer. At
   https://app.globus.org/settings/identities → "Link another identity" → pick the second
   institution. Verify with `globus whoami --linked-identities`, which should list both.

2. **Log in:** `globus login --no-local-server`

## Data-access consents

Every GCSv5 mapped collection needs a one-time consent before it will even list files:

```
The collection you are trying to access data on requires you to grant consent...
```

Request every collection in a single browser round-trip by putting all the dependent scopes
inside one bracket group:

```
globus session consent --no-local-server \
  'urn:globus:auth:scope:transfer.api.globus.org:all[*https://auth.globus.org/scopes/<ID1>/data_access *https://auth.globus.org/scopes/<ID2>/data_access]'
```

Verify access with `globus ls <ID>:<path>/` before submitting a transfer.

`globus ls` **hides dotfiles**; use `globus ls --all` to see `.git`, `.gitignore`, `.snakemake`.
Without it a correctly transferred tree looks like it is missing files.

## Excluding large subdirectories

Use a batch file rather than `--exclude` filter rules — filter rules match on names, not paths,
so a name like `logs` or `scratch` silently matches at every depth. A batch file states exactly
what moves.

Each line is `[--recursive] SOURCE DEST`, with paths **relative** to the endpoint paths given on
the command line. `#` comments and blank lines are allowed.

```
--recursive analysis analysis
--recursive code/rna_seq/bigwigs code/rna_seq/bigwigs
code/Snakefile code/Snakefile
```

Enumerate siblings explicitly to drop one child: to skip `code/rna_seq/Alignments`, list every
other `code/rna_seq/*` entry. Include dotfiles (`.git`, `.gitignore`, `.snakemake`) deliberately —
`ls` without `-A` hides them and they are easy to omit by accident.

Validate before submitting, since a bad path fails mid-transfer:

```
grep -vE '^\s*#|^\s*$' batch.txt | sed 's/^--recursive //' | awk '{print $1}' \
  | while read p; do [ -e "$p" ] || echo "MISSING: $p"; done
```

## Submitting

```
globus transfer \
  "$SRC:/project/yangili1/bjf79/<project>" \
  "$GL:/nfs/turbo/<volume>/<user>/<project>" \
  --batch batch.txt \
  --sync-level mtime --preserve-mtime \
  --label "<project> 20260810"
```

The flag is `--preserve-mtime`, not `--preserve-timestamps`. `--sync-level mtime` makes reruns
resumable — it re-sends only what changed, so a failed transfer can simply be resubmitted.

Always transfer into a named destination subdirectory. Pointing the destination at the projects
root scatters `analysis/`, `code/`, `data/`, … directly into it, mixed in with real project
directories.

## Watching a transfer

```
globus task show <TASK_ID> | grep -E "Status|Bytes|Faults|Subtasks Succ"
```

Block until done:

```
until [ "$(globus task show <ID> --format json | python -c 'import json,sys; print(json.load(sys.stdin)["status"])')" != "ACTIVE" ]; do sleep 30; done
```

`Bytes Transferred: 0` early on is normal — Globus creates the whole directory tree first, so
thousands of subtasks succeed before any data moves. Judge health by **`Faults`**, not bytes.
Rates of 300+ MB/s are typical for large files; many-small-file trees run far slower.

## Failure modes

Diagnose any failed task with `globus task event-list <TASK_ID>` — `task show` alone reports
only the final symptom and hides the repeating cause.

**`EXPIRED — The task deadline was reached` after ~24h with `Bytes Transferred: 0`.** A symptom,
not the cause. Globus retried a failing subtask every ~5 min until the deadline. Read the `AUTH`
or `PERMISSION_DENIED` events beneath it.

**`AUTH` / `530 Login incorrect` / `LOGIN_DENIED` with `GridFTP-Message: Attempt to create a
resource that already exists`.** Observed against the UMich Turbo collection, which failed every
login while `umich#greatlakes` reached the identical `/nfs/turbo/...` path without trouble.
Switch to `umich#greatlakes` and prefix the path with `/nfs/turbo/`.

**`EndpointPermissionDenied` (403) on `globus ls`.** The volume exists but the account is not on
its ACL — a different problem from a missing consent, which returns a consent-required message
instead.

**Directories created but no files.** A transfer that failed with 0 bytes still leaves its full
directory skeleton behind at the destination. Empty trees from a past attempt are not evidence of
partial success; check `globus task list` for the real outcome before trusting them.

**Web app fails where the CLI works.** The web app reports consent and auth errors vaguely. Retry
via the CLI, which names the exact missing scope and prints the command to grant it.
