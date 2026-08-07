# .zshenv — sourced for every zsh shell before /etc/zprofile.
# Keep this minimal: only things that must precede system profile.d scripts.

# /etc/zprofile sources /etc/profile in ksh emulation. /etc/profile.d/tmout.sh
# does `declare -r VAR; export VAR` — ksh-local readonly vars can't be exported
# in zsh. Override typeset to strip -r before /etc/zprofile runs; unset in .zprofile.
