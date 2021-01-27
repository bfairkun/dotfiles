# .profile
# If something is compatible and desired to be configured for all POSIX shells, including zsh, please edit ~/.profile
# and source .profile in all shells

# nnn config
export NNN_PLUG='p:-_less -iRS $nnn*;w:wall'
export NNN_BMS='d:~/Documents;D:~/Downloads/;m:~/mnt/midway/'


#======================
# Block fixes weird behavior with X11 forwarding while in tmux
#http://alexteichman.com/octo/blog/2014/01/01/x11-forwarding-and-terminal-multiplexers/
# -- Improved X11 forwarding through GNU Screen (or tmux).
# If not in screen or tmux, update the DISPLAY cache.
# If we are, update the value of DISPLAY to be that in the cache.
function update-x11-forwarding
{
    if [ -z "$STY" -a -z "$TMUX" ]; then
        echo $DISPLAY > ~/.display.txt
    else
        export DISPLAY=`cat ~/.display.txt`
    fi
}

# This is run before every command.
preexec() {
    # Don't cause a preexec for PROMPT_COMMAND.
    # Beware!  This fails if PROMPT_COMMAND is a string containing more than one command.
    [ "$BASH_COMMAND" = "$PROMPT_COMMAND" ] && return 

    update-x11-forwarding

    # Debugging.
    #echo DISPLAY = $DISPLAY, display.txt = `cat ~/.display.txt`, STY = $STY, TMUX = $TMUX  
}
trap 'preexec' DEBUG
#===================


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
