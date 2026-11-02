---
name: dispatch
description: Spawn, list, or kill Claude sessions in other tmux windows. Invoke when the user asks to open a new Claude session in a tmux window, start Claude in a project directory, or manage existing Claude tmux windows.
---

# Project Directory Listing

These are cached snapshots (last updated 2026-09-02). If the user references a project not listed here, run `ls /project2/yangili1/bjf79/` and `ls /project/yangili1/bjf79/` to get the current list.

## `/project/yangili1/bjf79/` (repos, tools, reference genomes)
```
20200302_ColaSeq
2024_comparativesplicing
2024_NMD_Junction_Classifier
20250331_clinvar_spliceai
20250521_poisonjuncs
20250624_panexperiment_nmd_candidatejuncs
20250818_figsforsplicingtimingr21proposal
20260206_a431_rnaseq
20260216_cp3_humanizedprnp_mouse
20260307_narnaseq_sse
20260310_diversesm_dr
20260324_xon_mpra
20260430_xon_titration
20260902_randomanalyses
ChromatinSplicingQTLs
conda_envs
conda_pkgs
data
my_project
OldProjects
repos_not_projects
scratch
snakemake_conda_envs
snaptron-experiments
```

## `/project2/yangili1/bjf79/` (analysis projects, reference files)
```
20200421_CutAndTag
20210618_Pangolin
20210618_zhao
20211209_JingxinRNAseq
202503_bo_rnaseq
202503_stat1_rnaseqprocessing
20250401_insulinandnmdflux
20250407_sm_interactions_bo
20250505_sm_splicing
20250519_other_sm
20250520_diverse_sm_splice_modifiers
20250922_kinetinanalogsrnaseq
20250922_risdidream_chen_et_al
20250925_Bo_RNAseq
20250925_simulateshortreadsfromlongreads
20250928_treatmentplusrisdiplamcombinationtitrations
ChromatinSplicingQTLs
containerize-conda
Fastq
GenometracksByGenotype
gwas_summary_stats
R
ReferenceGenomes
repos_not_projects
rstudioserver
rstudio-server-conda_share
scratch
singularity_sifs
sm_splicingmodulators
snakemake_conda_envs
snakemake-workflow_rna-seq
snaptron-analysis
SZS_pipeline
```

---

# Dispatching Sessions in tmux

Run tmux directly. Confirm completed actions briefly and show captured output after launch
or resume. Choose descriptive window names. Never kill or replace the `dispatcher` window.
Honor explicit requests for `--dangerously-skip-permissions`.

## Targeting and layout

- Inspect panes before sending keys. Pane indices start at 1 here; managed windows have a
  plain shell on top (pane 1) and the agent below (pane 2).
- Use a verified `window-index.pane-index`, `session:window.pane`, or `%pane_id` for pane
  commands. Do not use ambiguous bare integers or `window-name.pane`.
- Create and split windows in separate shell calls, verifying success between them.
- List saved sessions before asking new versus resume; do not repeat a choice already made.

## Other tasks

- [Resume an existing window](references/resume.md).
- [Inspect account tags or switch accounts](references/accounts.md).
- [Close windows/panes or run the dispatcher itself](references/management.md).

For waiting sessions, read status markers (`●` waiting, `✔` finished elsewhere; `prefix+a`
jumps to attention) rather than scraping panes:

```bash
tmux list-windows -F "#{window_index}: #{window_name} [#{@agent_win_state}]"
```

## How to open a session for a project directory

Run these steps in order, checking each result before the next action.

### Step A — List existing sessions and show them to the user

```bash
~/.claude/list-sessions.sh "/absolute/path/to/project"
```

Display the full output to the user. Each line shows:
```
  <last-modified-datetime>  <session-id>  <title or last message snippet>
```

Sessions are sorted newest-first. If the user has not specified new versus resume, ask
which they want after showing the list. Honor an already specified choice without asking again.

> The script uses `customTitle` if set, otherwise falls back to the last assistant message snippet. All sessions are shown — none are silently skipped.

### Step B — Create the window

```bash
tmux new-window -n "<window-name>" -c "/absolute/path/to/project"
```

### Step C — Find the new window's integer index

```bash
tmux list-windows -F "#{window_index}: #{window_name}"
```

Find the line matching your window name. Note the integer on the left — call it **IDX**.
Example: `5: my-project` → IDX = 5

### Step D — Split the window to create the bottom pane

Use **IDX** from Step C. This adds a plain shell pane below.

```bash
tmux split-window -v -t <IDX> -c "/absolute/path/to/project"
```

### Step E — Verify pane numbers

```bash
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
```

You should see two panes. The **first listed** is the top shell (pane 1). The **second listed** is the bottom pane where Claude will run — call its index **P** (almost always 2).

### Step F — Launch Claude or Codex in the bottom pane

**Account selection:** Claude Code has two isolated identities on this machine, selected via `CLAUDE_CONFIG_DIR`:
- **Personal account**: no env var needed. Remote Control-enabled (phone access).
- **Enterprise account** (UChicago): `CLAUDE_CONFIG_DIR=~/.claude-enterprise`. No Remote Control (disabled by org policy).

Default account: check `~/.claude/dispatch_default_account` — if it contains `enterprise`, default new sessions to enterprise; otherwise (file absent or `personal`) default to personal. The user toggles this by telling you "I'm at work" / "switch to work mode" (write `enterprise` to the file) or "back to personal" / "leaving work" (write `personal`, or just delete the file). An explicit account request in the user's message always overrides the default for that one session. Tag each window independently of this default.

Generate the session UUID before launch and tag the window. Never infer identity from the
newest transcript in a project directory; two windows can share that directory.

```bash
SID=$(python3 -c "import uuid; print(uuid.uuid4())")
```

**Claude — fresh session, personal account:**
```bash
tmux send-keys -t "<IDX>.<P>" "claude --session-id $SID -n '<window-name>'" Enter
tmux set-option -t <IDX> -w @claude_session_id "$SID"
tmux set-option -t <IDX> -w @claude_account "personal"
```

**Claude — fresh session, enterprise account:**
```bash
tmux send-keys -t "<IDX>.<P>" "CLAUDE_CONFIG_DIR=~/.claude-enterprise claude --session-id $SID -n '<window-name>'" Enter
tmux set-option -t <IDX> -w @claude_session_id "$SID"
tmux set-option -t <IDX> -w @claude_account "enterprise"
```
(For interactive typing at a shell prompt instead of dispatching, `claude-ent` is a shell function — defined in `local_dotfiles_RCCMidwayGeneral/.zshrc_local` — that wraps `CLAUDE_CONFIG_DIR=~/.claude-enterprise claude` and forwards all args, e.g. `claude-ent --resume <id>`.)

**Claude — resuming a specific session by ID:**
```bash
tmux send-keys -t "<IDX>.<P>" "claude -r <session-id>" Enter
tmux set-option -t <IDX> -w @claude_session_id "<session-id>"
tmux set-option -t <IDX> -w @claude_account "personal"
```
(Prefix with `CLAUDE_CONFIG_DIR=~/.claude-enterprise ` — and tag `@claude_account enterprise` — if that session should run under the enterprise account. Sessions/history are shared via a symlinked `projects` dir, but credentials/settings.local state are not, so resuming under the wrong config dir may prompt a fresh login.)

**Codex — fresh session:**
```bash
tmux send-keys -t "<IDX>.<P>" "codex" Enter
```

Or with an initial prompt:
```bash
tmux send-keys -t "<IDX>.<P>" "codex '<initial-prompt>'" Enter
```

Use the requested tool; otherwise default to Claude. For Codex resume requests, inspect
the installed CLI help rather than using the fresh-session command.

### Step G — Wait and capture output

```bash
sleep 5
tmux capture-pane -p -t "<IDX>.<P>"
```

Show the output to the user. If Claude is asking a question, relay it, wait for the user's answer, then:
```bash
tmux send-keys -t "<IDX>.<P>" "<user's answer>" Enter
sleep 3
tmux capture-pane -p -t "<IDX>.<P>"
```

---

## Updating the directory cache

Keep project listings in this entrypoint. Refresh them when requested or when a project is
missing; use a structured edit or heredoc rather than broad substitution commands.
