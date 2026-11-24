#!/usr/bin/env bash
# PreToolUse/Bash guard: refuse a mutating `gog` command on a Google Sheet or Doc
# unless a backup for that document exists from the last MAX_AGE_H hours.
# Rationale: gog's Sheets permissions are append-only, but an append CAN overwrite
# (Sheets table detection targeted A1 on a tab whose A1 was empty), and the CLI has
# no permission to repair what it damages.
MAX_AGE_H=6
IN=$(cat)
CMD=$(printf '%s' "$IN" | jq -r '.tool_input.command // ""' 2>/dev/null) || exit 0
[ -z "$CMD" ] && exit 0

# only mutating gog verbs
printf '%s' "$CMD" | grep -qE 'gog[[:space:]]+(sheets[[:space:]]+(append|update|clear)|docs[[:space:]]+(write|edit|insert|sed|find-replace|clear|add-tab|delete-tab|format)|drive[[:space:]]+(update|move|rename|trash|upload))' || exit 0

deny() {
  jq -nc --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}

ID=$(printf '%s' "$CMD" | grep -oE '[A-Za-z0-9_-]{30,}' | head -1)
[ -z "$ID" ] && deny "Backup guard: could not find a document id in this gog command. Run 'gog-backup <id>' first, then retry."

DIR="$HOME/.agent_backups/$ID"
[ -d "$DIR" ] || deny "Backup guard: NO backup exists for $ID. This is a shared document and gog cannot undo its own writes. Run:  gog-backup $ID   then retry."

RECENT=$(find "$DIR" -mindepth 1 -maxdepth 1 -type d -mmin "-$((MAX_AGE_H*60))" 2>/dev/null | head -1)
[ -z "$RECENT" ] && deny "Backup guard: the newest backup of $ID is older than ${MAX_AGE_H}h, so it may not reflect the current content. Run:  gog-backup $ID   then retry."
exit 0
