## Stow Conflict Resolution

When two packages contribute files under the same directory, GNU Stow unfolds the first
package's directory symlink and merges them normally. `stow -n` may report a false conflict
while simulating this unfold; verify the targets, then run the real `stow` command.

**Never use `stow -R` / `--restow` carelessly.** It first unstows (deletes all symlinks), then restows. If restow fails due to a conflict, you're left with nothing linked.

When `stow -v <package>` fails with `CONFLICT: ... vs. ...`:
1. Move the conflicting real file aside: `mv ~/.foo/bar ~/.foo/bar.bak`
2. Run `stow -v <package>` — it will now create the symlink cleanly
3. Decide: restore the real file over the symlink (`mv bar.bak bar` — keeps it as an unmanaged real file), or update the dotfiles copy to match and keep it managed

**Absolute symlinks conflict too.** Stow only claims *relative* links. A link like
`~/bin/foo -> /home/<user>/dotfiles/bin/bin/foo` points at the right file but still blocks
`stow bin` (seen with `install-codex-tmux-hooks`, 2026-09-25). Fix: `ln -sfn ../dotfiles/bin/bin/foo ~/bin/foo`.
Find them with `find ~ -maxdepth 2 -lname "$HOME/dotfiles/*"`.

Utility: `bin/bin/MoveStowConflicts.cli.py` automates moving all conflicting files to a backup dir in bulk.

## Git Lock Quirks on This Mac

Agent background git checks can briefly hold `.git/index.lock`. Wait for active operations;
remove a lock only after confirming it is stale.

**Stale locks** (left behind when a git process crashes or hangs):
```bash
rm -f ~/dotfiles/.git/index.lock
```

**Root-owned stow package dirs cause git to stall.** If any directory inside the repo is owned by root (e.g. `config/.config/fish/` was owned by root because fish was installed with sudo), `git status` hangs trying to read it, leaving locks that persist. Symptoms: every git command fails with `index.lock exists`.

Fix: either correct ownership (`sudo chown -R $USER <path>`) or remove the path from the repo (`git rm -r <path>`). Check with:
```bash
ls -la config/.config/   # look for root-owned entries
```
