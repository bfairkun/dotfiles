---
name: dotfiles
description: Edit or add dotfiles following the repo's stow-based organization conventions. Invoke when the user asks to add, modify, or reorganize dotfiles.
---

# Dotfiles Organization

Repo: `~/dotfiles`; remote: `git@github.com:bfairkun/dotfiles.git`.
Each top-level directory is a Stow package mirroring paths under `$HOME`:
`bash/.bashrc` → `~/.bashrc`, `bin/bin/tool` → `~/bin/tool`.

## Editing

- Edit package sources, never the `$HOME` symlink.
- Keep one `local_dotfiles_<MachineName>` package per physical machine. RCC uses the shared
  `local_dotfiles_RCCMidwayGeneral` plus node-specific `local_dotfiles_RCCMidway2`/`3`.
- General packages contain portable settings. Machine-specific shell overrides belong in
  `.zshrc_local`, `.bashrc_local`, or `.profile_local`, sourced by the general files.
- Machine feature markers belong at the root of the machine package; placing them under
  `.config` can conflict with that directory's folded link to the general `config` package.
- Store machine facts in that package's `.agents/AGENTS.local.md`, using the Great Lakes
  key/value table format. Keep repository `AGENTS.md` consistent with this skill.
- Do not edit submodule contents here: `vim/.vim`, `ohmyzsh/.oh-my-zsh`, `fzf/.fzf`, and
  `zsh/.zsh_custom/plugins/zsh-syntax-highlighting`.
- From `~/dotfiles`, use `stow -n <package>` to inspect links, then `stow -v <package>`.
  Never casually use `--restow`/`-R`: it unlinks first and can leave everything unlinked on
  conflict. For conflicts or git locks, read [troubleshooting](references/troubleshooting.md).
- Review and commit only task-related changes; preserve existing work.

## Symlinks and files applications rewrite

A symlink inside a package resolves from its **repo location**, not its eventual `$HOME`
location. Prefer links to tracked files within the package. For a target outside the repo,
calculate the path from the actual link location and verify it resolves.

Example: `agents/.claude-enterprise/projects` needs `../../../.claude/projects` to reach
`~/.claude/projects`; `../.claude/projects` points to a nonexistent directory inside the repo.

Applications may atomically replace settings files, destroying file symlinks. Give mutable
files such as Claude's `settings.json` separate copies; share directories only when shared
runtime state is intended. Read-only instruction files can be symlinked.

## Prevent runtime files from entering the repo

Stow can fold a whole directory into one symlink. For application directories that acquire
caches or state, use `--no-folding` so only tracked leaf files are linked:

```bash
stow -n --no-folding Library
stow --no-folding Library
```

Read-only packages (skills, vim, tmux, oh-my-zsh) can remain folded. To repair an already folded
application directory, follow [unfolding](references/unfolding.md).

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
| `local_dotfiles_RCCMidway3/` | Midway3 node only — per-machine feature markers (e.g. `.brain-notes-reminder`) |
| `local_dotfiles_GreatLakesUMich/` | UMich Great Lakes HPC — shell locals, `.condarc`, extra `bin/`, and `.agents/AGENTS.local.md` |
| `local_dotfiles_MyMacbookAir/` | Personal MacBook Air — shell locals, SSH config, LaunchAgents, and `.agents/AGENTS.local.md` |
| `local_dotfiles_MEDGEN_MacbookAir/` | MEDGEN (work) MacBook Air — same shape as MyMacbookAir |
| `local_dotfiles_HPStream/` | HP Stream laptop (Linux, i3wm) |

One package per physical machine. `RCCMidway3` holds only genuinely Midway3-only files; everything shared by both nodes stays in `RCCMidwayGeneral`. Per-machine agent facts go in each package's `.agents/AGENTS.local.md`; the RCC Midway file in `RCCMidwayGeneral` serves both login nodes.

## Supporting files

- `README.md`: installation instructions.
- `.xstow.ini`: ignored names (`~`, `CVS`, `core`, `README*`, `RCS`, `.git*`).
- `bin/bin/MoveStowConflicts.cli.py`: back up conflicting files before linking.
