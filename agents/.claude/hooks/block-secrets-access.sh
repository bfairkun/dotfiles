#!/usr/bin/env bash
# PreToolUse/Bash: refuse any shell command whose text references a .secrets
# file, so secret VALUES cannot reach the model's context via cat/grep/source.
# To see which variables are defined, use the `secret-names` helper, which
# prints names only and whose command string does not contain ".secrets".
set -uo pipefail
payload="$(cat 2>/dev/null || true)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
if printf '%s' "$cmd" | grep -qE '\.secrets'; then
  jq -nc '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Blocked: this command references a .secrets file, which holds API keys in plaintext. Reading it would put secret values into the transcript. Run `secret-names` to list the variable names defined there, or ask the user to act on the file themselves."
    }
  }'
  exit 0
fi
exit 0
