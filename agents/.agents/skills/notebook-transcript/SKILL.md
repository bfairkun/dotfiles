---
name: notebook-transcript
description: >
  Embed the Claude Code conversation behind a Quarto notebook as a collapsible,
  dark-terminal-styled widget at the end of the notebook, so a coworker can see
  the human-agent exchange (and tool calls, on expand) that produced it. Invoke
  when the user asks to append, attach, or include a transcript, chat log, or
  conversation history in a notebook they are authoring interactively — not for
  every notebook, only when they ask.
---

# Embedding a transcript in a notebook

This is a rare, opt-in finishing touch for a notebook built with the
`interactive-notebook` workflow — not a default step. The notebook's prose and
plots already document the scientific reasoning; the transcript widget exists to
additionally show *how the conversation went*, including exploratory turns that
never made it into the notebook prose. Add it only when asked.

## Do not dump the raw session log

Never serialize a full raw transcript (exported JSON, session log file, etc.)
directly into the notebook. Two reasons:

- **Image/binary blobs.** Tool inputs/outputs routinely carry base64 image data,
  screenshots, or other binary payloads — these must never be inlined; they bloat
  the HTML for no reader benefit.
- **Signal vs. noise.** A coworker reading this wants the shape of the
  conversation — what was asked, what was decided, what tools touched what — not
  every raw stdout dump. Hand-summarize each turn and each tool call to a
  sentence or two of what happened, the way you would narrate it to a colleague.

Build the `transcript` list yourself from the actual conversation (you have it in
context) — do not invent turns. Each tool call becomes one entry with a short,
accurate `input`/`output` summary, not a verbatim payload. `sanitize_text()` (see
below) is a second line of defense — it strips anything base64/image-shaped and
caps length — but the primary judgment call (what's worth including at all) is
yours to make when writing the summaries, not something the truncation function
decides for you.

## Cost model — only do this from the live session

Hand-summarizing is cheap **only** when the conversation is already sitting in
your context, i.e. you're still in the same session that built the notebook.
Summarizing then costs just the output tokens for the summaries — no extra input
read.

It gets expensive if you're ever asked to attach a transcript from a *different*,
already-closed session (e.g. resumed from a saved session log). Do not bulk-load
that session's full transcript file just to compress it — those logs carry large
tool payloads and images, so reading the whole thing to throw away 95% of it can
cost far more input tokens than the resulting widget is worth. Tell the user the
cost tradeoff before doing it.

If they still want it: Claude Code session logs live at
`~/.claude/projects/<project-slug>/<session-id>.jsonl` — one JSON object per
line, `type` field marking `user`/`assistant`/`system`, `message.content` either
a plain string or a list of blocks (`text`, `tool_use`, `tool_result`). The
`tool_result` blocks are almost always what bloats a log (file reads, command
output, images) — never load those wholesale. Use `jq` (runs outside your
context, so only its filtered output costs tokens) to pull just role + narrative
text + tool *names*, skipping tool payloads entirely:

```bash
jq -c 'select(.type=="user" or .type=="assistant") |
  {role: .message.role,
   text: (if (.message.content|type)=="string" then .message.content
          else [.message.content[]? | select(.type=="text") | .text] | join(" ") end),
   tools: [.message.content[]? | select(.type=="tool_use") | .name]}' session.jsonl
```

Read individual `tool_use`/`tool_result` blocks only for the specific calls worth
narrating (match by shared `id`/`tool_use_id`), not in bulk.

## Steps

1. In a code-folded cell near the end of the notebook:
   ```python
   from my_utils.notebook_utils import render_transcript
   ```
   `sanitize_text()` and `render_transcript()` live in `my_utils` (editable-installed
   in `py_general`, which is where these notebooks render) — see
   `src/my_utils/notebook_utils.py` and `tests/test_notebook_utils.py` in the
   `my_utils` repo. Edit that module directly (and its tests) for any change to the
   widget itself; don't fork a copy into the notebook.
2. In the next cell, build `transcript`: a list of turn dicts, each
   `{"role": "user" | "assistant" | "context", "text": str, "tools": [...]}`,
   where each tool is `{"name": str, "input": str, "output": str}`. Use
   `role: "context"` for a single leading entry summarizing background material
   (loaded instructions, skills, prior state) at a category level — this is the
   "what's in your context" detail Claude Code shows on expand; a category
   summary is enough, not a verbatim dump of any file.
3. Render it:
   ```python
   from IPython.display import HTML
   HTML(render_transcript(transcript))
   ```
4. Render the notebook (`render_notebook render ...`) and eyeball the widget —
   confirm no binary data leaked through and nothing sensitive from `context`
   got over-included.

## Design notes

- Expand/collapse uses native `<details>`/`<summary>` — no JavaScript, so the
  widget survives Slack's HTML preview and any static file open.
- `render_transcript(turns, height="520px", title="Claude Transcript",
  max_chars=4000)` — raise/lower `max_chars` per notebook if tool summaries are
  unusually long or short.
- A full worked example (this widget applied to a real conversation) was sent to
  Slack on 2026-08-19 — ask the user if they still have it if you want a
  reference render rather than re-deriving the design from scratch.
