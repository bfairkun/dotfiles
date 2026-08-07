# .zprofile
# If something is compatible and desired to be configured for all shells, including zsh, please edit ~/.profile
# and source .profile in all shells

[[ -f ~/.profile ]] && source ~/.profile

# use ~/.zprofile_local if exists
if [ -f ~/.zprofile_local ]; then
    source ~/.zprofile_local
fi
