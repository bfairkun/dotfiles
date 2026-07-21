---
name: dotfiles
description: Edit or add dotfiles following the repo's stow-based organization conventions. Invoke when the user asks to add, modify, or reorganize dotfiles.
argument-hint: "[what to add or change]"
---

# Dotfiles Repo Organization

Repo location: `~/dotfiles` (also the working directory for all edits)
Remote: `git@github.com:bfairkun/dotfiles.git`

## Core Pattern: GNU Stow

Each top-level directory is a **stow package**. Running `stow <package>` from `~/dotfiles` creates symlinks in `$HOME` mirroring the package's internal directory tree.

```
~/dotfiles/bash/.bashrc  →  (stow bash)  →  ~/.bashrc
```

- Always mirror the path from `$HOME` inside the package directory
- Nested dirs like `bin/bin/` are intentional: stow symlinks the inner `bin/` to `~/bin/`
- XDG-style configs live in `config/.config/<tool>/` → symlinked to `~/.config/<tool>/`

## Package Inventory

**General packages** (cross-machine):
| Package | Contents |
|---------|----------|
| `bash/` | `.bashrc`, `.bash_profile`, `.bash_logout` |
| `zsh/` | `.zshrc`, `.zprofile`, `.zsh_custom/plugins/` |
| `sh/` | `.profile` — shared POSIX settings sourced by both bash and zsh |
| `git/` | `.gitconfig`, `.gitignore_global`, `.git-completion.bash` |
| `tmux/` | `.tmux.conf`, version-specific configs in `.tmux/{1.8,2.2,3.1a,3.1b,3.1c,3.2a}/` |
| `vim/` | `.vim/` submodule (personal vim repo) |
| `fzf/` | `.fzf/` submodule (v0.38.0) |
| `ohmyzsh/` | `.oh-my-zsh/` submodule |
| `bin/` | `bin/bin/` — portable scripts (ack, custom Python/shell scripts) |
| `config/` | `.config/` — XDG configs: fish, gh, navi, nnn, rstudio, snakemake, pulse |
| `other/` | `.ctags`, `.multiqc_config.yaml`, `.ncbi/`, `.rmarkdown/templates/`, `conda_minimal_yamls/` |
| `Library/` | macOS only — `.config/Code/User/` VSCode settings, keybindings, snippets |
| `agents/` | Shared `.agents/` instructions/skills plus client-specific `.claude/`, `.codex/`, and `.gemini/` configuration |

**Machine-specific packages** (`local_dotfiles_<MachineName>`):
| Package | Machine |
|---------|---------|
| `local_dotfiles_RCCMidwayGeneral/` | RCC Midway HPC (**both** login nodes) — shell/config overrides, extra `bin/`, and `.agents/AGENTS.local.md` |
| `local_dotfiles_RCCMidway2/` | Midway2 node only — VSCode remote-server settings |
| `local_dotfiles_GreatLakesUMich/` | UMich Great Lakes HPC — shell locals, `.condarc`, extra `bin/`, and `.agents/AGENTS.local.md` |
| `local_dotfiles_MyMacbookAir/` | Personal MacBook Air — shell locals, SSH config, LaunchAgents, and `.agents/AGENTS.local.md` |
| `local_dotfiles_MEDGEN_MacbookAir/` | MEDGEN (work) MacBook Air — same shape as MyMacbookAir |
| `local_dotfiles_HPStream/` | HP Stream laptop (Linux, i3wm) |

One package per physical machine. There is intentionally no `RCCMidway3`-specific package. Create one only for genuinely Midway3-only files. Per-machine agent facts go in each package's `.agents/AGENTS.local.md`; the RCC Midway file in `RCCMidwayGeneral` serves both login nodes.

## Local Override Pattern

Shell configs source machine-specific files if they exist:
- `~/.zshrc` → sources `~/.zshrc_local`
- `~/.bashrc` → sources `~/.bashrc_local`
- `~/.profile` → sources `~/.profile_local`

Machine-specific stow packages supply those `*_local` files. **Never put machine-specific settings in the general packages** — put them in the appropriate `local_dotfiles_*` package instead.

## Git Submodules

- `vim/.vim` — personal .vim repo
- `ohmyzsh/.oh-my-zsh` — oh-my-zsh framework
- `zsh/.zsh_custom/plugins/zsh-syntax-highlighting`
- `fzf/.fzf`

When adding new files near submodules, be careful not to accidentally edit the submodule.

## Where to Add New Things

| What | Where |
|------|-------|
| New portable tool config (XDG) | `config/.config/<tool>/` |
| New portable script | `bin/bin/` |
| RCC Midway shell/env settings (both nodes) | `local_dotfiles_RCCMidwayGeneral/` |
| Midway2-only settings | `local_dotfiles_RCCMidway2/` |
| Midway3-only settings | create `local_dotfiles_RCCMidway3/` (none exist yet) |
| Per-machine agent facts (paths, hostname verify) | that machine's `.agents/AGENTS.local.md` |
| macOS settings | `local_dotfiles_MyMacbookAir/` or `local_dotfiles_MEDGEN_MacbookAir/` |
| Shared agent instructions/skills and client config | `agents/` |
| Misc dotfiles with no better home | `other/` |
| Snakemake cluster profiles | `config/.config/snakemake/<profile-name>/` |

## Key Utilities

- `bin/bin/MoveStowConflicts.cli.py` — resolves stow conflicts by moving existing files to a backup dir
- `README.md` — full installation instructions
- `.xstow.ini` — xstow ignore config (ignores `~`, `core`, `CVS`, `README*`, `.git*`)

## Workflow When Editing

1. Edit the file inside `~/dotfiles/<package>/...` (not the symlink in `$HOME`)
2. If adding a new file, place it in the right package following the path-mirroring rule
3. If adding a new package, run `stow -v <package>` to create symlinks
4. Commit changes with `git add` + `git commit` from `~/dotfiles`

## Stow Conflict Resolution

When two packages contribute files under the same directory, GNU Stow unfolds the first
package's directory symlink and merges them normally. `stow -n` may report a false conflict
while simulating this unfold; verify the targets, then run the real `stow` command.

**Never use `stow -R` / `--restow` carelessly.** It first unstows (deletes all symlinks), then restows. If restow fails due to a conflict, you're left with nothing linked.

When `stow -v <package>` fails with `CONFLICT: ... vs. ...`:
1. Move the conflicting real file aside: `mv ~/.foo/bar ~/.foo/bar.bak`
2. Run `stow -v <package>` — it will now create the symlink cleanly
3. Decide: restore the real file over the symlink (`mv bar.bak bar` — keeps it as an unmanaged real file), or update the dotfiles copy to match and keep it managed

Utility: `bin/bin/MoveStowConflicts.cli.py` automates moving all conflicting files to a backup dir in bulk.

## Git Lock Quirks on This Mac

**Normal background locks:** Claude Code runs `git status` in the working directory every ~1.6 seconds to populate its UI context. This creates brief (~350ms) index locks at `.git/index.lock`. These are harmless and self-resolving — don't delete them unless they're stale.

**Stale locks** (left behind when a git process crashes or hangs):
```bash
rm -f ~/dotfiles/.git/index.lock
```

**Root-owned stow package dirs cause git to stall.** If any directory inside the repo is owned by root (e.g. `config/.config/fish/` was owned by root because fish was installed with sudo), `git status` hangs trying to read it, leaving locks that persist. Symptoms: every git command fails with `index.lock exists`.

Fix: either correct ownership (`sudo chown -R $USER <path>`) or remove the path from the repo (`git rm -r <path>`). Check with:
```bash
ls -la config/.config/   # look for root-owned entries
```
