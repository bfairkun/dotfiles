---
name: dispatch
description: Spawn, list, or kill Claude sessions in other tmux windows. Invoke when the user asks to open a new Claude session in a tmux window, start Claude in a project directory, or manage existing Claude tmux windows.
argument-hint: [project path or name]
---

# Project Directory Listing

These are cached snapshots (last updated 2026-04-14). If the user references a project not listed here, run `ls /project2/yangili1/bjf79/` and `ls /project/yangili1/bjf79/` to get the current list.

## `/project/yangili1/bjf79/` (repos, tools, reference genomes)
```
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
ReferenceGenomes
repos_not_projects
scratch
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
- The dispatcher session is always named `dispatcher` — never kill or replace it.
- Never skip `--dangerously-skip-permissions` if the user explicitly asks for it.

---

## CRITICAL RULES — apply to every tmux action

**RULE 1: Never target panes by window name.**
`tmux send-keys -t "dr_work.1"` is WRONG — tmux parses `"dr_work"` as a session name, not a window name.
Always use the **integer window index**: `tmux send-keys -t "4.1"` ✓

**RULE 2: Pane indices start at 1, not 0.**
In this environment `pane-base-index` is 1. Panes are numbered 1, 2, … never 0.
Always run `tmux list-panes` to confirm before sending keys.

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

**Claude — fresh session:**
```bash
tmux send-keys -t "<IDX>.<P>" "claude -n '<window-name>'" Enter
```

**Claude — resuming a specific session by ID:**
```bash
tmux send-keys -t "<IDX>.<P>" "claude -r <session-id>" Enter
```

Concrete example — IDX=5, P=2, fresh: `tmux send-keys -t "5.2" "claude -n 'my-project'" Enter`

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
```
(Use `codex` instead if that was the original tool.) Then do Step G.

**Sub-case 2c — Only one pane (no bottom pane yet):**
```bash
tmux split-window -v -t <IDX> -c "/path/to/project"
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
tmux send-keys -t "<IDX>.2" "claude -r <session-id>" Enter
```
Then do Step G.

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

`~/.claude/agents/dispatcher.md` (model: haiku) is a standalone always-on session for Remote Control use.

Start it:
```bash
tmux new-window -n "dispatcher" "claude --agent dispatcher"
```

Then run `/loop 3m date` inside it to keep Remote Control alive.

**Note:** Custom agents in `~/.claude/agents/` can only be launched with `claude --agent <name>` — not via Claude's internal Agent tool. Dispatching from within a conversation is always done directly via `tmux new-window`.

## IMPORTANT: Updating the skill directory cache
When edits to the directory cache are needed, use the Write tool or a heredoc — never `sed -i` with substitutions, as this risks corrupting or wiping the file.
