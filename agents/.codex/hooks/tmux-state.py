#!/usr/bin/env python3
"""Translate Codex hooks into tmux markers; never emit hook output or log payloads."""
import json
import os
from pathlib import Path
import subprocess
import sys


def action_for(event):
    name = event.get('hook_event_name')
    if name == 'PermissionRequest':
        return 'attn'
    if name == 'PreToolUse':
        tool = event.get('tool_name', '').split('.')[-1]
        return 'attn' if tool in ('request_user_input', 'request_user_input_async') else 'clear'
    if name == 'Stop':
        return 'done'
    if name in ('SessionStart', 'SessionEnd', 'UserPromptSubmit', 'PostToolUse', 'Interrupt'):
        return 'clear'
    return None


def main():
    if not os.environ.get('TMUX_PANE'):
        return
    try:
        event = json.load(sys.stdin)
        action = action_for(event) if isinstance(event, dict) else None
        if action:
            subprocess.run([str(Path.home() / 'bin/tmux-agent-state'), action],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=3, check=False)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        pass


if __name__ == '__main__':
    main()
