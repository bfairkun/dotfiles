# Agent instructions

## What this is

Stow-based dotfiles. Each top-level directory is a stow package; running `stow <pkg>` from `~/dotfiles` symlinks its contents into `$HOME`, mirroring the package's internal path (`bash/.bashrc` → `~/.bashrc`; nested `bin/bin/` → `~/bin/`).

The detailed reference lives in the `dotfiles` skill (`agents/.agents/skills/dotfiles/SKILL.md`). Keep it and this file in sync without duplicating detail here.

## Conventions that must hold

- **One package per machine.** A given physical machine gets exactly one `local_dotfiles_<MachineName>/` package — never split across two (e.g. don't keep `.condarc` in one package and that same machine's VSCode settings in another).
- **Naming:** machine packages are `local_dotfiles_<MachineName>`. The RCC Midway family is `local_dotfiles_RCCMidwayGeneral` (both login nodes) plus `local_dotfiles_RCCMidway2` / `local_dotfiles_RCCMidway3` (per-node). Keep the shared prefix so the family sorts together.
- **General vs. local:** never put machine-specific settings in a general package. They belong in that machine's `local_dotfiles_*` package via the override pattern — `.zshrc`/`.bashrc`/`.profile` each source a `*_local` counterpart supplied by the machine package.

## Per-machine facts for agents

Each machine package carries `local_dotfiles_<Machine>/.agents/AGENTS.local.md`, stowed to `~/.agents/AGENTS.local.md` and imported by the global `AGENTS.md`. Machine-unique values (filesystem paths, SLURM account, default conda envs, the `brain` repo path) go there as a key/value table. Canonical format: `local_dotfiles_GreatLakesUMich/.agents/AGENTS.local.md`.

## Editing

- Edit files inside `~/dotfiles/<package>/`, never the `$HOME` symlink.
- Submodules (`vim/.vim`, `ohmyzsh/.oh-my-zsh`, `fzf/.fzf`, `zsh/.zsh_custom/plugins/zsh-syntax-highlighting`) — don't edit their contents from here.
- Never `stow -R`/`--restow` carelessly: it unstows (deletes symlinks) then restows, so a conflict mid-restow leaves nothing linked.
