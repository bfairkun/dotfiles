# .bash_profile
# If something is compatible and desired to be configured for all shells, including zsh, please edit ~/.profile
# Only keep bash specific configuration here, and source .profile everwhere

# # Get the aliases and functions
# if [ -f ~/.bashrc ]; then
# 	. ~/.bashrc
# fi

[[ -f ~/.profile ]] && source ~/.profile

export PS1='\u@\H:\w$'
# unset PROMPT_COMMAND

#Activate autocompletion for git
if [ -f ~/.git-completion.bash ]; then
  . ~/.git-completion.bash
fi


# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

