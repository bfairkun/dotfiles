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

