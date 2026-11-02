# Account tracking and switching

Window tags `@claude_session_id` and `@claude_account` are the source of truth. Never infer
identity from transcript modification times: multiple windows can share a project directory.
Read tags with `show-window-options`; `show-options -t <idx> -wv` can fall back to the active
window's value when the target has no value:

```bash
tmux show-window-options -t <IDX> -v @claude_session_id
tmux show-window-options -t <IDX> -v @claude_account
```

The default-account file controls new sessions only; see [launch](../SKILL.md#step-f--launch-claude-or-codex-in-the-bottom-pane).
Change it only on the user's request, never by IP detection (VPN makes location ambiguous).

```bash
~/.claude/switch-account.sh <personal|enterprise> [window-name ...]
```

- With window names, switches those tagged windows. Without names, switches all managed
  windows on the opposite account. Untagged windows are skipped with a warning.
- Gracefully terminates Claude, resumes the exact tagged session under the target config
  directory, and updates the account tag. Do not use `--fork-session`.
- Personal and enterprise share the transcript tree through the `projects` symlink;
  credentials/settings remain separate.
- Scope is managed two-pane windows with Claude in the bottom pane and both tags set.
  Other processes and untagged windows are untouched.

For manual shell use, `claude-ent` in `local_dotfiles_RCCMidwayGeneral/.zshrc_local` wraps
`CLAUDE_CONFIG_DIR=~/.claude-enterprise command claude "$@"`.
