#!/usr/bin/env bash
# Claude Code status line script
# Reads JSON from stdin and outputs a colored status line

input=$(cat)

# Extract fields from JSON
cwd=$(echo "$input" | jq -r '.cwd // .workspace.current_dir // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
five_hour_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
seven_day_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
output_style=$(echo "$input" | jq -r '.output_style.name // ""')

# Shorten cwd: replace $HOME with ~, then truncate middle if too long
home_dir="$HOME"
short_cwd="${cwd/#$home_dir/~}"
# If path is longer than 40 chars, keep first 2 and last 2 components
if [ ${#short_cwd} -gt 40 ]; then
  short_cwd=$(echo "$short_cwd" | awk -F'/' '{
    n=NF;
    if (n > 4) printf "%s/%s/.../%s/%s", $1, $2, $(n-1), $n;
    else print $0
  }')
fi

# Git branch (skip optional lock to avoid blocking)
git_branch=""
if git -C "$cwd" rev-parse --git-dir > /dev/null 2>&1; then
  git_branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null \
    || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

# ANSI color codes (will appear dimmed in Claude Code)
RESET='\033[0m'
CYAN='\033[36m'
YELLOW='\033[33m'
BLUE='\033[34m'
GREEN='\033[32m'
RED='\033[31m'
DIM='\033[2m'

# Build status line parts
parts=""

# cwd
parts="${parts}${CYAN}${short_cwd}${RESET}"

# git branch
if [ -n "$git_branch" ]; then
  parts="${parts}  ${YELLOW}${git_branch}${RESET}"
fi

# model
if [ -n "$model" ]; then
  parts="${parts}  ${BLUE}${model}${RESET}"
fi

# context usage
if [ -n "$used_pct" ] && [ -n "$remaining_pct" ]; then
  used_int=${used_pct%.*}
  # Color: green when low, yellow when moderate, red when high
  if [ "$used_int" -ge 80 ] 2>/dev/null; then
    ctx_color="$RED"
  elif [ "$used_int" -ge 50 ] 2>/dev/null; then
    ctx_color="$YELLOW"
  else
    ctx_color="$GREEN"
  fi
  # Round percentages for display
  used_display=$(printf "%.0f" "$used_pct" 2>/dev/null || echo "$used_int")
  rem_display=$(printf "%.0f" "$remaining_pct" 2>/dev/null || echo "${remaining_pct%.*}")
  parts="${parts}  ${DIM}ctx:${RESET} ${ctx_color}${used_display}% used${RESET} ${DIM}|${RESET} ${ctx_color}${rem_display}% left${RESET}"
fi

# session rate limits (5-hour and/or 7-day)
rate_parts=""
if [ -n "$five_hour_pct" ]; then
  fh_int=$(printf "%.0f" "$five_hour_pct" 2>/dev/null || echo "${five_hour_pct%.*}")
  fh_rem=$((100 - fh_int))
  if [ "$fh_int" -ge 80 ] 2>/dev/null; then
    fh_color="$RED"
  elif [ "$fh_int" -ge 50 ] 2>/dev/null; then
    fh_color="$YELLOW"
  else
    fh_color="$GREEN"
  fi
  rate_parts="${rate_parts}${DIM}5h:${RESET} ${fh_color}${fh_rem}% left${RESET}"
fi
if [ -n "$seven_day_pct" ]; then
  wd_int=$(printf "%.0f" "$seven_day_pct" 2>/dev/null || echo "${seven_day_pct%.*}")
  wd_rem=$((100 - wd_int))
  if [ "$wd_int" -ge 80 ] 2>/dev/null; then
    wd_color="$RED"
  elif [ "$wd_int" -ge 50 ] 2>/dev/null; then
    wd_color="$YELLOW"
  else
    wd_color="$GREEN"
  fi
  [ -n "$rate_parts" ] && rate_parts="${rate_parts} ${DIM}|${RESET} "
  rate_parts="${rate_parts}${DIM}7d:${RESET} ${wd_color}${wd_rem}% left${RESET}"
fi
if [ -n "$rate_parts" ]; then
  parts="${parts}  ${rate_parts}"
fi

# effort level — no direct field exists in the statusline JSON schema;
# output_style.name is the best available proxy (e.g. "default", "Explanatory", "Learning")
if [ -n "$output_style" ]; then
  parts="${parts}  ${DIM}style:${RESET} ${BLUE}${output_style}${RESET}"
fi

printf "%b\n" "$parts"
