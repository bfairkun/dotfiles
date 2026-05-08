#!/bin/bash
# list-sessions.sh — List Claude sessions for a project directory
#
# USAGE:
#   list-sessions.sh [dir-or-pattern]
#
# EXAMPLES:
#   list-sessions.sh                          # list sessions for current directory
#   list-sessions.sh /home/bjf79             # list sessions for a specific path
#   list-sessions.sh diversesm               # fuzzy match against project dir names
#   list-sessions.sh --all                   # list all sessions across all projects

CLAUDE_PROJECTS="${HOME}/.claude/projects"

# Convert an absolute path to a claude project dir key
# e.g. /project/yangili1/bjf79/20260310_diversesm_dr -> -project-yangili1-bjf79-20260310-diversesm-dr
path_to_key() {
    echo "$1" | sed 's|/|-|g; s|_|-|g'
}

list_sessions() {
    local project_dir="$1"
    local jsonl_files=("$project_dir"/*.jsonl)
    local output=""

    [ ! -e "${jsonl_files[0]}" ] && return

    for f in "${jsonl_files[@]}"; do
        [ -f "$f" ] || continue
        id=$(basename "$f" .jsonl)

        # Try customTitle first; fall back to last assistant message snippet
        label=$(python3 - "$f" << 'PYEOF'
import sys, json

fpath = sys.argv[1]
custom_title = ""
last_assistant = ""

try:
    with open(fpath) as fh:
        first_line = fh.readline()
        try:
            d = json.loads(first_line)
            custom_title = d.get("customTitle") or ""
        except Exception:
            pass

    if not custom_title:
        with open(fpath) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    msg = d.get("message", {})
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            text = content
                        elif isinstance(content, list):
                            text = " ".join(
                                c.get("text", "") for c in content if isinstance(c, dict)
                            )
                        else:
                            text = ""
                        text = text.strip()
                        if text:
                            last_assistant = text
                except Exception:
                    pass

    label = custom_title if custom_title else last_assistant
    # Collapse whitespace and truncate
    label = " ".join(label.split())[:120]
    print(label)
except Exception:
    print("")
PYEOF
)
        [ -z "$label" ] && label="(no content)"
        mtime=$(stat -c '%y' "$f" | cut -d'.' -f1)
        output+="  $mtime  $id  $label"$'\n'
    done

    [ -z "$output" ] && return
    echo "$output" | sort -r
}

ARG="${1:-$(pwd)}"

if [ "$ARG" = "--all" ]; then
    for project_dir in "$CLAUDE_PROJECTS"/*/; do
        key=$(basename "$project_dir")
        result=$(list_sessions "$project_dir")
        [ -z "$result" ] && continue
        echo "=== $key ==="
        echo "$result"
        echo
    done
    exit 0
fi

# If arg looks like an absolute path, convert it to a key
if [[ "$ARG" == /* ]]; then
    key=$(path_to_key "$ARG")
    project_dir="${CLAUDE_PROJECTS}/${key}"
    if [ ! -d "$project_dir" ]; then
        echo "No project dir found for: $ARG"
        echo "Tried: $project_dir"
        exit 1
    fi
    echo "=== $key ==="
    list_sessions "$project_dir"
else
    # Fuzzy match against project dir names
    matches=$(ls "$CLAUDE_PROJECTS" | grep -i "$ARG")
    if [ -z "$matches" ]; then
        echo "No project dirs matching: $ARG"
        exit 1
    fi
    while IFS= read -r key; do
        result=$(list_sessions "${CLAUDE_PROJECTS}/${key}")
        [ -z "$result" ] && continue
        echo "=== $key ==="
        echo "$result"
        echo
    done <<< "$matches"
fi
