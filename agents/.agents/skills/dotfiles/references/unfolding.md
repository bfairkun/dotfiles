# Unfold an application directory

A folded application directory can accumulate runtime files inside this repo. This occurred
with `Library/Application Support/Code` (1.1 GB of state); `config/.config/nnn/sessions/` and
`config/.config/gh/hosts.yml` have also required ignore rules.

1. Quit the application and inspect tracked changes and untracked files. Preserve any source
   edits before restoring tracked files.
2. Run `stow -D <package>` to remove the home symlink.
3. Move the real application directory from the repo to its intended `$HOME` location.
4. Restore the package's tracked files from git, retaining any saved source edits.
5. Compare the home copies with the tracked files and resolve conflicts without discarding
   runtime data. Follow the repo's bulk-deletion approval rule if removing duplicates.
6. Dry-run and apply `stow --no-folding <package>`.

Unstowing leaves the package unlinked until the final step succeeds.
