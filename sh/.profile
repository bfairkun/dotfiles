# .profile
# If something is compatible and desired to be configured for all POSIX shells, including zsh, please edit ~/.profile
# and source .profile in all shells

echo "Running  ${0}..."

# nnn config
export NNN_PLUG='p:-_less -iRS $nnn*;w:wall'
export NNN_BMS='d:~/Documents;D:~/Downloads/;m:~/mnt/midway/'


# User specific environment and startup programs
# User's Stow packages
if [ -d "$HOME/pkg/bin" ]; then
    export PATH="$HOME/pkg/bin:$PATH"
fi

# User's home bin
if [ -d "$HOME/bin" ]; then
    export PATH="$HOME/bin:$PATH"
fi

if [ -f ~/.profile_local ]; then
    source ~/.profile_local
fi
