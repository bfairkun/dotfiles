# MEDGEN_MacbookAir — Machine-Specific Notes

Work (MEDGEN) MacBook Air (macOS).

## Agent Reference

| Key | Value |
|---|---|
| `MACHINE` | MEDGEN (work) MacBook Air (macOS) |
| `HOSTNAME_VERIFY` | `echo $HOST` → `Benjamins-MacBook-Air.local` (was `MED-GEN-ML-04.local` before the Nov 2026 wipe) |
| `BRAIN_PATH` | `~/Documents/repos_not_projects/brain` |
| `my_utils` | `~/Documents/repos_not_projects/my_utils/` |
| `USERNAME` | `benjaminfair` (was `bjf79` before the wipe) |

## Local Clipboard

`pbcopy` daemon runs locally via `~/Library/LaunchAgents/pbcopy.plist` (loaded in `.profile_local`); it receives clipboard text from remote HPC sessions over the autossh reverse tunnel (port 2224).
