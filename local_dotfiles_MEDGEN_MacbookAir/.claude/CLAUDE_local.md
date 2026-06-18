# MEDGEN_MacbookAir — Machine-Specific Notes

Work (MEDGEN) MacBook Air (macOS).

## Agent Reference

| Key | Value |
|---|---|
| `MACHINE` | MEDGEN (work) MacBook Air (macOS) |
| `HOSTNAME_VERIFY` | `echo $HOST` → `MED-GEN-ML-04.local` |
| `BRAIN_PATH` | `~/Documents/repos_not_projects/brain` _(verify/clone on machine)_ |
| `my_utils` | `~/Documents/repos_not_projects/my_utils/` |

## Local Clipboard

`pbcopy` daemon runs locally via `~/Library/LaunchAgents/pbcopy.plist` (loaded in `.profile_local`); it receives clipboard text from remote HPC sessions over the autossh reverse tunnel (port 2224).
