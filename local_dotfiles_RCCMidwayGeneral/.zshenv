# Sourced for all zsh sessions (interactive and non-interactive).
# Keep minimal — only exports that must be available unconditionally.

# SLURM binaries — added directly (module load slurm/current doesn't reliably
# modify PATH in non-interactive shells). Hardcode the current-el8 path.
export PATH=/software/slurm-current-el8-x86_64/bin:$PATH

# Shared snakemake conda envs. Covers runs that use a project's own
# code/snakemake_profiles/ (no conda-prefix there), which otherwise build
# duplicate envs in .snakemake/conda and blow the yangili1 file quota.
case "$HOST" in
    midway3*|beagle3*) export SNAKEMAKE_CONDA_PREFIX=/project/yangili1/bjf79/snakemake_conda_envs ;;
    midway2*) export SNAKEMAKE_CONDA_PREFIX=/project2/yangili1/bjf79/snakemake_conda_envs ;;
esac
