---
name: post-to-slack
description: RCC Midway HPC only. Send or post any file (plot, rendered notebook, table, CSV, etc.) to Slack. Invoke whenever the user asks to send, post, share, or DM a file to Slack, independent of whether the file is a plot.
---

# Posting a file to Slack

Use an available native Slack file-upload tool; otherwise use `post_plot_to_slack`.

Wraps `post_plot_to_slack` (in `~/bin/`, stowed from dotfiles), a standalone script
that uploads any file to Slack via the `hpc_agent_plots` bot and posts it to a
channel or DM. Despite the script's name (historically plot-focused), it works for
**any file type** — notebooks, CSVs, PDFs, images, whatever.

## Usage

```bash
post_plot_to_slack <filepath> [channel_id]
```

- `filepath`: any existing file, absolute or relative path.
- `channel_id` (optional): defaults to the value in `~/.config/slack_plot_channel`
  (normally the user's own Slack user ID, so it lands as a DM). Pass an explicit
  channel ID to post somewhere else (e.g. a lab channel).

## Prerequisites (already set up on this machine; only relevant if missing)

- Bot token in `~/.secrets` as `SLACK_PLOT_TOKEN=xoxb-...` (does not expire) — the
  script also accepts `SLACK_PLOT_TOKEN` directly from the environment.
- Default DM target in `~/.config/slack_plot_channel` (the user's Slack user ID).
- To post to a channel instead of a DM: invite `@hpc_agent_plots` to that channel in
  Slack, then pass the channel's ID as the second argument.
- New machine setup: add `SLACK_PLOT_TOKEN` to `~/.secrets`, create
  `~/.config/slack_plot_channel` with the target Slack user/channel ID.

## Notes

- Slack previews PNG/JPG/PDF/HTML inline reasonably well; for plots specifically,
  prefer PNG over PDF if inline preview matters (Slack does not render PDF vector
  previews as nicely) — the `agent-plots` skill's PDF-by-default convention is about
  the browser server, not Slack; re-save as PNG first if the user is going to view it
  primarily through Slack.
- This is a fire-and-forget CLI call — no confirmation prompt needed beyond the
  normal tool-use permission check, since posting a file the user just asked to send
  is the explicit intent, not an inferred action.
