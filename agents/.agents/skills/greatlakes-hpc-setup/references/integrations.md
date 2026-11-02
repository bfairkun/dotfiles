## Phase 9: Secrets and MCPs (optional — set up the integrations you'll use)

**Why:** MCPs let agents reach external services (a live Jupyter kernel, Slack, Google
Drive/Gmail/Calendar). Most need a per-machine secret or auth step, so they're **not** carried
by stow — set up only the ones the user wants. Offer each; skip what they don't need.

### 9a. The `~/.secrets` file (API keys and tokens)

**Why:** `.bashrc_local` and `.zshrc_local` both do `[ -f ~/.secrets ] && source ~/.secrets`,
so anything exported there is available to interactive shells and agent shell tools
tool after `source ~/.secrets`). It lives in `$HOME`, never in the repo, so secrets are never
git-tracked. Create it `chmod 600`:

```bash
umask 077
cat > ~/.secrets <<'EOF'
# Exported secrets — sourced by .bashrc_local / .zshrc_local. Never commit this file.
export ALPHAGENOME_API_KEY="..."          # AlphaGenome API (alphagenome_utils)
export SLACK_PLOT_TOKEN="xoxb-..."         # Slack bot token for post_plot_to_slack (9d)
export SLACK_PLOT_CHANNEL="UXXXXXXXX"      # Slack user ID (DM self) or channel ID for plots
# export ANTHROPIC_API_KEY="sk-ant-..."    # only if running Claude with a raw API key
EOF
chmod 600 ~/.secrets
```

The maintainer's file currently exports: `ALPHAGENOME_API_KEY`, `SLACK_PLOT_TOKEN`,
`SLACK_PLOT_CHANNEL`. Add only the keys the user actually has — leave the rest out.

### 9b. Jupyter-kernel MCP (local, already wired up by stow)

The only MCP whose code lives on this machine. The script ships in
`~/bin/jupyter_kernel_mcp.py`; register it as a user-scope stdio server in each client.
See the `jupyter-kernel` skill.

### 9c. Account/plugin MCPs — Google Drive, Gmail, Calendar, Slack (remote, no local code)

**Why:** These are **remote** MCP servers (HTTP endpoints hosted by Google/Slack) — no code is
downloaded here. They differ only in how they're registered, and **each machine must
authenticate once** even though the registration travels:

- **Google Drive / Gmail / Calendar** — account-level **connectors**. Enable them once in the
  Claude desktop app or at claude.ai (Settings → Connectors). They then appear in Claude Code
  anywhere you're signed in with that Anthropic account. Nothing to configure on the cluster.
- **Slack** — registered as the `slack@claude-plugins-official` **plugin**, already enabled in
  the tracked `settings.json`, so it travels with the dotfiles. But the OAuth token is
  per-machine: in Claude Code run `/mcp`, pick `slack`, and complete authentication. (This
  Slack MCP — for reading/searching Slack — is **separate** from the plot-upload script in 9d.)

Verify what's live on the current machine: `claude mcp list`.

### 9d. Slack plot upload — `post_plot_to_slack` (optional, great for Remote Control)

**Why this exists:** plots saved to the agent-plots dir are normally viewed in a browser over
an SSH tunnel. But when driving Claude from **Remote Control on a phone** (e.g. voice-commanding
Claude while walking), there's no tunnel and no browser — you can't see the plots. Pushing a
plot straight into a Slack DM means it shows up on your phone instantly. It's purely about a
nicer remote/mobile experience.

This is a standalone script (`~/bin/post_plot_to_slack`), **not** the Slack MCP. It uses a Slack
**bot token**, independent of the 9c plugin auth:

1. Set `SLACK_PLOT_TOKEN` (`xoxb-...`) and `SLACK_PLOT_CHANNEL` in `~/.secrets` (9a). The token
   is a Slack **bot** token; the bot needs scopes `files:write`, `chat:write`, and `im:write`
   (the last for DMing yourself). Alternatively write the token to `~/.config/slack_plot_token`
   and the target to `~/.config/slack_plot_channel` (both `chmod 600`).
2. `SLACK_PLOT_CHANNEL` can be your own Slack **user ID** (starts `U`, e.g. `UC94MAVLL`) to DM
   yourself, or a **channel ID** (starts `C`) the bot has been invited to (`/invite @yourbot`,
   else `not_in_channel`).
3. Test (remember the Bash tool is non-interactive — source secrets first):
   ```bash
   source ~/.secrets
   post_plot_to_slack /path/to/plot.png          # optional 2nd arg overrides the channel
   ```
   Success prints `posted <file> to Slack channel <id>` and the image appears in that DM/channel.

Verified working on gl-login3 (2026-06): DM to self via user ID resolves through
`conversations.open` to a `D...` DM channel and the upload lands.

---
