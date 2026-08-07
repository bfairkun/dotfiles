# .zshenv — sourced for every zsh shell before /etc/zprofile.
# Keep this minimal: only things that must precede system profile.d scripts.

# /etc/profile.d/tmout.sh tries to set TMOUT but zsh marks it readonly first.
# Unset it here so the system script doesn't throw a read-only error.
unset TMOUT 2>/dev/null
