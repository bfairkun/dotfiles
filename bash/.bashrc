# .bashrc


# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# User specific aliases and functions

if [ -f ~/.bashrc_local ]; then
    source ~/.bashrc_local
fi

[ -f ~/.fzf.bash ] && source ~/.fzf.bash
