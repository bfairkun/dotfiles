# gog setup and re-authentication

Installed 2026-10-13: gogcli v0.44.0 (`openclaw/gogcli`, MIT; release checksum verified, source scanned for telemetry and non-Google hosts — none beyond opt-in features and the manual `gog update`).

## Layout (Midway3)

| Item | Location |
|---|---|
| Binary | `~/.local/bin/gog`, upstream source with the policy compiled in by [../scripts/rebuild.sh](../scripts/rebuild.sh). Self-contained: needs no conda or Go to run. Never install the stock release tarball over it. |
| Config | `~/.config/gogcli/config.json` (`keyring_backend: file`) |
| OAuth client JSON (backup) | `~/.config/gogcli/client_secret_gog.json` |
| Encrypted tokens | `~/.local/share/gogcli/` |
| Keyring password | `GOG_KEYRING_PASSWORD` in `~/.secrets` (untracked, chmod 600) |

Midway has no system keychain, hence the file keyring. Never put the client JSON or password in a git-tracked directory (including `brain/raw/inbox/`).

## Google Cloud project

Project `gog-cli` (number 1037523866337), owned by bfair.kun@gmail.com; one Desktop-app OAuth client named `gog` serves every account and machine.

- Enabled APIs: Gmail, Drive, Docs, Sheets, Calendar. A "<X> API is not enabled for this OAuth project" error means enabling it at `https://console.cloud.google.com/apis/library/<x>.googleapis.com?project=1037523866337`; no re-login needed if the account already granted that service.
- Publishing status is **In production** (unverified). Testing status would expire refresh tokens every 7 days. Publishing required a home page and privacy-policy URL on the Branding page.
- Leave "Use this client for an AI-powered agent" unchecked; it targets Google's hosted MCP tools, which gog does not use.

## Add or re-authorize an account

Remote two-step flow (no browser on the server):

```bash
gog auth add <email> --services gmail,drive,docs,sheets,calendar --gmail-scope readonly --remote --step 1
# user opens auth_url on their laptop, clicks Advanced → Go to gog-cli (unsafe),
# lands on a dead http://127.0.0.1:<port>/oauth2/callback?... page, pastes that URL back
gog auth add <email> --services gmail,drive,docs,sheets,calendar --gmail-scope readonly --remote --step 2 --auth-url '<pasted URL>'
gog auth alias set <alias> <email>
```

Finish within ~5 minutes of step 1. Pass the same `--services`/`--gmail-scope` in both steps. Re-adding with fewer services drops the missing ones. `pbcopy_to_local` can put the step-1 URL on the user's Mac clipboard.

`gog auth list --plain` shows accounts and services; `gog auth doctor --check` diagnoses keyring problems.

## Build or upgrade

Building needs only the conda env `agent_gobuild` (create with `mamba create -n agent_gobuild -c conda-forge go`; Go 1.27.2 works). Run from any directory:

```bash
scripts/rebuild.sh [vX.Y.Z|latest]               # build and install ~/.local/bin/gog here
scripts/rebuild.sh v0.44.0 darwin/arm64          # write ./gog-darwin-arm64 to copy to another machine
```

Upgrading is the same command with a newer tag; re-test a blocked command (`gog sheets update x A1 a` must fail) afterwards.

## Another machine

1. Binary: Linux x86-64 machines (Great Lakes, Midway2) can take a copy of the Midway3 binary; for the Mac, build `darwin/arm64` (Apple Silicon) or `darwin/amd64` (Intel) here and `scp` it to `~/.local/bin/gog`. The Mac build is untested; if macOS refuses to run it, `xattr -d com.apple.quarantine` it.
2. Copy the client JSON there, outside git.
3. The policy blocks `gog auth keyring` and `gog auth credentials set`, so run those once with a stock release binary in a temporary path: `gog auth credentials set <json>`, plus `gog auth keyring file` where there is no system keychain (Linux), with `GOG_KEYRING_PASSWORD` added to that machine's `~/.secrets`. The Mac uses its keychain and needs no password.
4. Log in each account as above (logins are per machine).
