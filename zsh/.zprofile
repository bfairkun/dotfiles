# .zprofile
# If something is compatible and desired to be configured for all shells, including zsh, please edit ~/.profile
# and source .profile in all shells

# TMOUT is set readonly by zsh internals before /etc/profile.d/tmout.sh runs;
# unset it first so sourcing .profile doesn't throw a read-only error.
unset TMOUT 2>/dev/null
[[ -f ~/.profile ]] && source ~/.profile

# use ~/.zprofile_local if exists
if [ -f ~/.zprofile_local ]; then
    source ~/.zprofile_local
fi
