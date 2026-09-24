---
name: dispatch
description: Spawn, list, or kill Claude sessions in other tmux windows. Invoke when the user asks to open a new Claude session in a tmux window, start Claude in a project directory, or manage existing Claude tmux windows.
argument-hint: [project path or name]
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

# Dispatching Claude Sessions in tmux

Claude dispatches directly via the Bash tool — no intermediate agent needed.

## Style rules
- Be brief. Confirm what you did in one sentence after completing each action.
- Always show captured pane output after every spawn or resume.
- Pick a descriptive window name based on what the user says the task is.
- The dispatcher tmux window is always named `dispatcher` — never kill or replace it.
- Never skip `--dangerously-skip-permissions` if the user explicitly asks for it.

---

## CRITICAL RULES — apply to every tmux action

**RULE 1: Never target panes by window name.**
`tmux send-keys -t "dr_work.1"` is WRONG — tmux parses `"dr_work"` as a session name, not a window name.
Always use the **integer window index**: `tmux send-keys -t "4.1"` ✓

**RULE 2: Pane indices start at 1, not 0.**
In this environment `pane-base-index` is 1. Panes are numbered 1, 2, … never 0.
Always run `tmux list-panes` to confirm before sending keys.

Because of this, a **bare integer is an ambiguous target** for the commands that take a
pane target — `display-message`, `show-options -p`, `capture-pane`. tmux tries pane index
in the *current* window first, so `tmux display-message -t 1 -p '#{window_name}'` reports
the current window's pane 1, **not** window 1. It only falls through to a window index
when that pane does not exist, which makes the bug intermittent. Use `session:index`
(`-t ssh_tmux:1`) or an unambiguous `%pane_id` / `@window_id`.

**RULE 3: Never chain new-window + split-window in one `&&` call.**
Run each tmux command as a separate Bash tool call and verify success before the next step.

**RULE 4: Always run list-sessions.sh and display results BEFORE asking new vs. resume.**
Never ask the user "new or resume?" without first showing them what sessions exist.

---

## Window layout convention

Every managed window has **two panes**:
- **Top pane (pane 1):** Plain shell — created automatically with the window
- **Bottom pane (pane 2):** Claude session — added with `split-window -v`

Claude always runs in the **bottom** pane. The top pane is a plain shell.

### Attention markers

Managed windows flag themselves in the tmux status bar via `~/bin/tmux-agent-state`,
driven by Claude Code hooks: a red `●` before the window name means that session is
blocked on the user (permission prompt or waiting for input), a green `✔` after it means
its turn finished while the user was looking at a different window. `prefix+a` jumps to
the next window needing attention.

So when asked which sessions are waiting, read the markers instead of scraping panes:

```bash
tmux list-windows -F "#{window_index}: #{window_name} [#{@agent_win_state}]"
```

---

## How to open a session for a project directory

Follow these steps **in order**, one Bash call at a time.

### Step A — List existing sessions and show them to the user

```bash
~/.claude/list-sessions.sh "/absolute/path/to/project"
```

Display the full output to the user. Each line shows:
```
  <last-modified-datetime>  <session-id>  <title or last message snippet>
```

Sessions are sorted newest-first. After displaying, ask: "Which session would you like to resume, or shall I start a fresh one?" Wait for the user's answer before proceeding.

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

Example with IDX=5: `tmux split-window -v -t 5 -c "/path/to/project"`

### Step E — Verify pane numbers

```bash
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
```

You should see two panes. The **first listed** is the top shell (pane 1). The **second listed** is the bottom pane where Claude will run — call its index **P** (almost always 2).

### Step F — Launch Claude or Codex in the bottom pane

**Account selection:** Claude Code has two isolated identities on this machine, selected via `CLAUDE_CONFIG_DIR`:
- **Personal account**: no env var needed. Remote Control-enabled (phone access).
- **Enterprise account** (UChicago): `CLAUDE_CONFIG_DIR=~/.claude-enterprise`. No Remote Control (disabled by org policy).

Default account: check `~/.claude/dispatch_default_account` — if it contains `enterprise`, default new sessions to enterprise; otherwise (file absent or `personal`) default to personal. The user toggles this by telling you "I'm at work" / "switch to work mode" (write `enterprise` to the file) or "back to personal" / "leaving work" (write `personal`, or just delete the file). An explicit account request in the user's message always overrides the default for that one session. See "Account tracking" below for why this file is the *default*, not a substitute for tagging each window.

**Always generate the session ID yourself and tag the window** — this makes the session unambiguous later (for resuming, and for `switch-account.sh`), instead of having to guess it from `list-sessions.sh` by directory+timestamp, which is ambiguous whenever two windows share a project directory (confirmed to go wrong in practice — see "Account tracking" below).

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

Concrete example — IDX=5, P=2, fresh, personal: `tmux send-keys -t "5.2" "claude --session-id $SID -n 'my-project'" Enter`

**Codex — fresh session** (stateless; no session resume):
```bash
tmux send-keys -t "<IDX>.<P>" "codex" Enter
```

Or with an initial prompt:
```bash
tmux send-keys -t "<IDX>.<P>" "codex '<initial-prompt>'" Enter
```

Ask the user which tool they want (claude or codex) if not specified. Default to claude.

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

## How to resume into an existing tmux window

First check if the window already exists:
```bash
tmux list-windows -F "#{window_index}: #{window_name}"
```

### Case 1 — Window does not exist
Follow the full "open a session" flow above (Steps A–G).

### Case 2 — Window exists, check pane state
```bash
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
```

**Sub-case 2a — Two panes, bottom pane is running `claude` or `codex`:**
Session is already active. Tell the user and ask what they want to do.

**Sub-case 2b — Two panes, bottom pane is a shell (exited):**
```bash
tmux send-keys -t "<IDX>.2" "claude -r <session-id>" Enter
tmux set-option -t <IDX> -w @claude_session_id "<session-id>"
tmux set-option -t <IDX> -w @claude_account "personal"   # or "enterprise" — match whichever config dir you used
```
(Use `codex` instead if that was the original tool — codex has no account tagging.) Then do Step G.

**Sub-case 2c — Only one pane (no bottom pane yet):**
```bash
tmux split-window -v -t <IDX> -c "/path/to/project"
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
tmux send-keys -t "<IDX>.2" "claude -r <session-id>" Enter
tmux set-option -t <IDX> -w @claude_session_id "<session-id>"
tmux set-option -t <IDX> -w @claude_account "personal"   # or "enterprise"
```
Then do Step G.

---

## Account tracking, work-mode default, and switching accounts

### Why every window is tagged

Every dispatcher-managed window carries two tmux window options, set at launch (Step F)
or resume:
- `@claude_session_id` — the exact session UUID running in that window
- `@claude_account` — `"personal"` or `"enterprise"`

These are the **source of truth** for which account a window is on and what its session
ID is. Don't try to reverse-engineer either one from `~/.claude/projects/<dir>/*.jsonl`
by directory + newest-mtime — **two windows can share a project directory**, and picking
"the newest file in that directory" can silently resolve to a *different* window's live
session. This happened once during testing: resuming what was assumed to be a freshly
spawned, still-blank session actually pulled in another window's active transcript,
because that other window's session file had a later mtime. No data was lost (it was
caught before any message was sent into the wrongly-resumed pane), but it could have
caused two concurrent `claude` processes to write the same transcript file. Always tag
at creation time instead of inferring later.

Check tags (use `show-window-options`, NOT `show-options -t <idx> -wv` — the latter
silently falls back to the *current/active* window's value when the target window has
no per-window value set, which looked like every window shared one value until caught):
```bash
tmux show-window-options -t <IDX> -v @claude_session_id
tmux show-window-options -t <IDX> -v @claude_account
```

### Work-mode default (manual, no auto-detection)

`~/.claude/dispatch_default_account` holds the default account for *new* sessions when
the user doesn't specify one:
- Missing or contains `personal` → default to personal (the normal case)
- Contains `enterprise` → default to enterprise

Toggle it when the user says so ("I'm at work" / "switch to work mode" → write
`enterprise`; "I'm home" / "back to personal" → write `personal` or `rm` the file). There
is no automatic detection of "at work" (IP-based detection was tried and rejected — the
user is on VPN both at home and at work, so client IP doesn't distinguish them). An
explicit account request in the user's message always wins over this default for that
one request.

### Switching a window's account (enterprise ↔ personal)

```bash
~/.claude/switch-account.sh <personal|enterprise> [window-name ...]
```

- No window names: switches every tagged, dispatcher-managed window currently on the
  *opposite* account.
- Window names given: switches exactly those windows (must already be tagged).
- Untagged windows are skipped with a warning, never guessed at.

Mechanics: kills the `claude` process in the pane (SIGTERM, graceful), relaunches
`claude --resume <session-id>` in the same pane under the target `CLAUDE_CONFIG_DIR`
(none for personal, `~/.claude-enterprise` for enterprise), and updates the
`@claude_account` tag. **No `--fork-session`** — this is an in-place switch of the same
conversation, not a copy, because `~/.claude-enterprise/projects` is symlinked to
`~/.claude/projects` (both identities already read/write one shared transcript tree;
`CLAUDE_CONFIG_DIR` only selects credentials, not history). Verified live: switching
loses no history, and the header correctly flips between "Claude Pro"/`config-dir:
default` and "Claude Enterprise"/`config-dir: enterprise`.

Scope: only touches windows *you* (the dispatcher) manage — the two-pane convention with
`claude` running in the bottom pane and both tags set. It won't find or touch `claude`
processes running outside tmux windows you created, or in windows missing the tags.

### `claude-ent` shell wrapper

For the user typing directly at a shell prompt (not via dispatch), `claude-ent` in
`local_dotfiles_RCCMidwayGeneral/.zshrc_local` wraps
`CLAUDE_CONFIG_DIR=~/.claude-enterprise command claude "$@"` — forwards all flags
untouched, so `claude-ent --resume <id>`, `claude-ent -c`, etc. all work without having
to remember the env var.

---

## Other operations

```bash
# List current tmux windows
tmux list-windows -F "#{window_index}: #{window_name} [#{pane_current_command}]"

# Spawn with a specific agent (Step F variant)
tmux send-keys -t "<IDX>.<P>" "claude -n '<window-name>' --agent <agent-name>" Enter

# Close Claude session only (leave window open)
tmux kill-pane -t "<IDX>.2"

# Kill entire window
tmux kill-window -t <IDX>
```

---

## The dispatcher agent

`~/.claude/agents/dispatcher.md` (model: sonnet) is a standalone always-on session for Remote Control use. **Always run this under the personal account (default, no `CLAUDE_CONFIG_DIR` override)** — Remote Control only works for the account that's actually logged in, and the enterprise account doesn't have it enabled.

Start it:
```bash
tmux new-window -n "dispatcher" "claude --agent dispatcher -n \"dispatcher-$(hostname -s)\""
```

Then run `/loop 3m date` inside it to keep Remote Control alive.

**The `-n` name must stay hostname-suffixed.** `$HOME` is shared across the login
nodes but tmux servers are not, so each node needs its own dispatcher
conversation. `~/bin/dispatcher_watchdog.sh` derives the same name and can
restart a dead dispatcher, but is not registered in cron — see `.profile_local`.

**Note:** Custom agents in `~/.claude/agents/` can only be launched with `claude --agent <name>` — not via Claude's internal Agent tool. Dispatching from within a conversation is always done directly via `tmux new-window`.

## IMPORTANT: Updating the skill directory cache
When edits to the directory cache are needed, use the Write tool or a heredoc — never `sed -i` with substitutions, as this risks corrupting or wiping the file.
