# My dotfiles

This repostory helps me keep the dotfile settings I like across different computers. The way I organize and install these is inspired by [this blog post by Alex Pearce](https://alexpearce.me/2016/02/managing-dotfiles-with-stow/) about using git and GNU stow to easily version track and install dotfiles. This repo essentially acts as a stow directory, making it easy to create symlinks in `$HOME` that point to the dotfiles in this repositroy (assuming this repo is in your `$HOME` directory).

I also picked up some tips from [this post](https://www.anishathalye.com/2014/08/03/managing-your-dotfiles/) about dotfile organization and tips.

## Contents

```
.
├── bash
├── bin
│   └── bin
├── git
├── local_dotfiles_MyMacbookAir
├── local_dotfiles_RCCMidway
├── ohmyzsh
├── other
├── sh
├── tmux
├── vim
└── zsh

12 directories
```

- `bash` : my bash specific settings (eg: my `.bashrc` and `.bash_profile`)
- `bin/bin` : Portable and distrutable executables that should be able to work on linux or mac without compiling. For example, a couple custom scripts which are generally useful to me. Also, the perl script [ack](https://beyondgrep.com/why-ack/) is here (Artistic License 2.0), The nested structure is so that stow will create a symlink in `$HOME` to the child `bin/bin` instead of `bin`
- `git` : git settings
- `local_dotfiles_*` : settings with computer-specific dotfiles that will be sourced in the general dotfiles. See installation step3.
- `ohmyzsh` : git-submodule of [oh-my-zsh](https://github.com/ohmyzsh/ohmyzsh). This includes some zsh themes and plugins sourced in my `.zshrc`. So there is no need to install oh-my-zsh independently; it is included in these dotfiles.
- `other` : other random dotfiles
- `sh` : shell settings that I like in both zsh and bash. Both my `.zprofile` and `.bash_profile` source `sh/.profile`
- `tmux` : tmux settings. Note the `tmux/.tmux/*` files for version specific tmux settings
- `vim` : My vim settings. A git submodule of [my .vim repo](https://github.com/bfairkun/.vim) which contains its own README to help with installation of plugins
- `zsh` : zsh specific settings. In addition to `.zshrc`, this also includes non oh-my-zsh plugins as a git submodule

## Installation

#### Step1: clone this repo

First, clone this repo to your home directory, using git commands that will also clone the git submodules nested in this repo:

```
cd ~
git clone --recurse-submodules --remote-submodules https://github.com/bfairkun/dotfiles.git
```

#### Step2: Putting desired dotfiles (or symlinks to dotfiles) in `$HOME``

Now you can just copy or create symlinks from the relevant dotfile to your home directory:

```bash
cd ~/dotfiles

# Create a single symlink
ln -s ~/.bashrc bash/.bashrc 
```

To do this for many dotfiles easily, you can use [GNU stow](https://www.gnu.org/software/stow/). But I have found recent versions of GNU Stow to be a pain to install where I don't have root privelages because recent versions require recent PERL version which itself was difficult to install without root privelages. An easier to install alternative for systems without root privelages and without up-to-date PERL versions (RCC Midway) is [Xstow](http://xstow.sourceforge.net) or an older version of GNU stow (version 1.3.2). Once installed, use like the following example:

```bash
cd ~/dotfiles

# Use stow to create symlinks for everything in bash Use the dry-run -n flag
# first. Remove -n when you feel comfortable you won't mess anything up
stow -v -n bash

# Or use xstow
xstow -v -n bash
```

Stow can also create create symlinks for all the files in multuple folders, like this example that uses a glob pattern with stow. The `local_dotfiles_*` should obviously only be for the desired computer.

```zsh
#Use extended globbing to expand stow argument to all files in the directory
#but ignore the local dotfiles and README. This glob probably only works in zsh,
#but bash has a similar extended globbing option with slightly different syntax

#Start a temprary zsh shell session if you aren't already ising zsh, and allow
#for special glob patterns
zsh
setopt extended_glob

#Print the glob pattern
print ^(local|README)*

#Use it in stow command
stow -v -n ^(local|README)*
```

Stow will not overwrite existing files in `$HOME`. So if you want stow to creat a `$HOME/.vim` symlink to `$HOME/dotfiles/vim/.vim` but you already have a `$HOME/.vim` folder, you need to get rid of it (or move it somewhere else) or else stow will not write a symlink and it will complain of conflicts. I have created a helper script `bin/bin/MoveStowConflicts.cli.py` to systematically put all of the stow conflicts in `$HOME` into a new folder, which you might want to call `MyOldDotfilesThatCreateConflicts/`:

```bash
bin/bin/MoveStowConflicts.cli.py MoveStowConflictFilesToDir -n -v --NewDir ~/MyOldDotfilesThatCreateConflicts/ --SubtreeDirs ^(local|README)*
```

The script contains a dry-run (`-n`) parameter so you can preview what will happen before actually doing it. Use the `-h` help flag on that script for more.

Once you have gotten rid of your stow conflicts, you can consider revisiting the stow commands to create symlinks for all the dotfiles

#### Step3: Add local_dotfiles to override my general settings as needed.

When I need computer specific settings, just create an additional local dotfile that gets sourced in main dotfile. For example, a snippet at the end of my `.bashrc`:

```bash
if [ -f ~/.bashrc_local ]; then
    source ~/.bashrc_local
fi
```

Then you can create a `~/.bashrc_local` to contain computer specific settings. I have included the local dotfiles I use on a few computers in `local_dotfiles_*` which can be stowed like this example:

```bash
cd ~/dotfiles
stow -n -v local_dotfiles_RCCMidway
```

#### Step4: All done!

But some extra notes to keep in mind:
- my vim settings may need some plugins installed, which you can do with `:PlugInstall` once you open vim. The readme in my [.vim repo](https://github.com/bfairkun/.vim) has a little more instructions if needed.
- Also, as I change things in my .vim repo (a nested submodule in this repo), pulling in changes can be kind of tricky if you don't know about git submodules. I read [this primer on git submodules](https://www.vogella.com/tutorials/GitSubmodules/article.html).
- `chsh -s $(which zsh)` to switch to zsh.
- There are a couple things in my vim or zsh settings that require external things to be installed in order to make use of them. For example, I recommend installing or setting up the following:
	- I have the pbcopy script in `bin/bin/pbcopy` and in my tmux and vim config I have remaps that reference this script. The usefulness of this script is mostly for working over ssh, so that you can copy the remote tmux clipboard or the remote vim clipboard to the local clipboard for copy/paste. But in order to make this work, you might need to follow the instructions from this [blogpost by Sean Coates](https://seancoates.com/blogs/remote-pbcopy) on how to set up ssh connection and a listener on your local machine. 
	- Some of my local bashrc/zshrc have the lines for configuring conda. Obviously these will require [conda package manager](https://docs.conda.io/en/latest/miniconda.html) to be installed, and probably best to let `conda init` handle these lines.
	- [fzf](https://github.com/junegunn/fzf) is something I find pretty useful and might be referenced in some of my dotfiles. and it's required for some vim plugins that I use. If you want to install this in a place without root privelages (eg RCC Midway), the git installation instructions should work. (But it won't be necessary to modify bashrc/zshrc when it prompts you during installation, since my bashrc and zshrc already have the fzf line)
	- Other unnecessary things to optionally install that I might have references to in my dotfiles collection include [gitmux](https://github.com/arl/gitmux), [nnn](https://github.com/jarun/nnn), [i3-gaps window manager for linux](https://github.com/Airblader/i3)
