# Sourced for all zsh sessions (interactive and non-interactive).
# Keep minimal — only exports that must be available unconditionally.

# SLURM binaries — added directly (module load slurm/current doesn't reliably
# modify PATH in non-interactive shells). Hardcode the current-el8 path.
export PATH=/software/slurm-current-el8-x86_64/bin:$PATH
