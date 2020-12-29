#!/usr/bin/env bash

######################################################################
# @author      : benfair (benfair@$HOSTNAME)
# @file        : install_dotfiles
# @created     : Friday Dec 25, 2020 16:00:19 EST
#
# @description : My dotfile installer. Just git submodules and then symlink to
# $HOME with stow
######################################################################

# For readme:
# git clone --recursive
# install/MoveStowConflicts.cli.py MoveStowConflictFilesToDir -n -v --NewDir ~/PreStowConflictFiles/ --SubtreeDirs *

#Install submodule repositories
# zsh plugins, vimrc, local rc files
if ! [ -x "$(command -v git)" ]; then
  echo 'Error: git is not installed.' >&2
  exit 1
fi
git submodule update --init --recursive

# Stow to create symlinks in $HOME
# if xstow
if [-x "$(command -v xstow)"]; then
    xstow -v -f -n bash/ bin/ git/ local_dotfiles/ other/ sh/ tmux/
    #exit 0
elif [-x "$(command -v stow)"] && $(stow -V>x) then;
    stow -v -f -n 
else
    echo 'stow (Version > X) and xstow not available. Please install and retry, or manually symlink or copy the dotfiles into $HOME as needed.' >&2
    exit 1
fi
