# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# Alises
alias targz="tar -xvfz"
alias conda_envs="conda info --envs"

# User specific environment and startup programs
# User's Stow packages
if [ -d "$HOME/pkg/bin" ]; then
    PATH="$HOME/pkg/bin:$PATH"
fi

PATH=$HOME/bin:$PATH

export PATH
export PS1='\u@\H:\w$'
unset PROMPT_COMMAND

# Attach or start split screen tmux session
if [[ -z "$TMUX" ]] && [ "$SSH_CONNECTION" != "" ]; then
    tmux attach-session -t ssh_tmux || (tmux new-session -s ssh_tmux \; split-window -h)
fi

# activate environment with useful stuff
# conda activate my_ChimpEQTL_env
