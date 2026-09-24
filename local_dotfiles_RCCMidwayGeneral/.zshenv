# Sourced for all zsh sessions (interactive and non-interactive).
# Keep minimal — only exports that must be available unconditionally.

# SLURM binaries — added directly (module load slurm/current doesn't reliably
# modify PATH in non-interactive shells). Hardcode the current-el8 path.
export PATH=/software/slurm-current-el8-x86_64/bin:$PATH

##=====================================================================
## CODEX_TMUX_HANG workaround -- DELETE THIS WHOLE BLOCK WHEN FIXED UPSTREAM
##
## Bug (diagnosed 2026-09-14 against codex 0.154.0; still present in 0.156.1
## on 2026-09-23): at TUI startup codex
## probes the terminal for extended-key support by running
##     tmux display-message -p '#{extended-keys-format}'
## It spawns that helper with a hardcoded PATH of /usr/local/bin:/bin:/usr/bin,
## so it always resolves /usr/bin/tmux (2.7 on Midway) even though our PATH
## puts /software/tmux-3.2a-el8-x86_64/bin (3.2a) first. A tmux 2.7 client
## talking to our 3.2a server blocks forever in poll(), and codex sets no
## timeout on the probe -- so `codex` hangs on a blank screen, forever.
##
## Workaround: CODEX_TUI_DISABLE_KEYBOARD_ENHANCEMENT=1 skips the probe.
## Costs nothing here -- tmux 3.2a has no extended-keys option at all, so the
## probe would have reported "unsupported" anyway. Gated on $TMUX so keyboard
## enhancement (Shift+Enter for newline, etc.) still works outside tmux, where
## codex never runs the probe and the bug cannot trigger.
##
## Lives in .zshenv rather than .zshrc_local because it must also apply to
## `zsh -c` invocations -- that is how tmux / tmux-agent-bridge / the
## dispatcher launch codex, and those never source .zshrc.
##
## Version-pinned on purpose: on any other codex version this prints a loud
## notice instead of silently carrying a stale workaround forever.
##=====================================================================
CODEX_TMUX_HANG_PINNED_VERSION=0.156.1
_codex_link=$HOME/.codex/packages/standalone/current

if [ -L "$_codex_link" ]; then
    _codex_ver=${${_codex_link:A:t}%%-*}

    if [ "$_codex_ver" = "$CODEX_TMUX_HANG_PINNED_VERSION" ]; then
        # Known-affected version -- apply the workaround, inside tmux only.
        [ -n "$TMUX" ] && export CODEX_TUI_DISABLE_KEYBOARD_ENHANCEMENT=1
    else
        print -u2 ""
        print -u2 "################################################################################"
        print -u2 "## AGENT-ACTIONABLE: codex version changed -- recheck the tmux startup-hang bug"
        print -u2 "##"
        print -u2 "##   installed codex : $_codex_ver"
        print -u2 "##   workaround pin  : $CODEX_TMUX_HANG_PINNED_VERSION"
        print -u2 "##   CODEX_TUI_DISABLE_KEYBOARD_ENHANCEMENT is currently NOT being set."
        print -u2 "##"
        print -u2 "## Re-test whether upstream fixed it (run from inside tmux):"
        print -u2 "##   tmux new-session -d -s cxtest -x 200 -y 50 'codex; read x'"
        print -u2 "##   sleep 20; tmux capture-pane -p -t cxtest; tmux kill-session -t cxtest"
        print -u2 "##     FIXED  => the codex TUI banner paints within ~20s."
        print -u2 "##     BROKEN => blank pane, plus a stuck child process:"
        print -u2 "##               /usr/bin/tmux display-message -p #{extended-keys-format}"
        print -u2 "##"
        print -u2 "## If FIXED : delete this whole CODEX_TMUX_HANG block from"
        print -u2 "##            ~/dotfiles/local_dotfiles_RCCMidwayGeneral/.zshenv"
        print -u2 "##            The env var is then dead weight -- remove it, do not keep it."
        print -u2 "## If BROKEN: bump the pin to CODEX_TMUX_HANG_PINNED_VERSION=$_codex_ver"
        print -u2 "##            in that same file, and leave this block in place."
        print -u2 "################################################################################"
        print -u2 ""
    fi
    unset _codex_ver
elif [ -d "$HOME/.codex" ]; then
    print -u2 ""
    print -u2 "## AGENT-ACTIONABLE: ~/.codex exists but the standalone 'current' symlink is"
    print -u2 "## missing, so the CODEX_TMUX_HANG version check in ~/.zshenv cannot run."
    print -u2 "## codex may have been installed a different way (npm?). Re-check whether the"
    print -u2 "## tmux startup-hang bug applies, then fix or delete that block."
    print -u2 ""
fi
unset _codex_link
