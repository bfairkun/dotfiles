#!/usr/bin/env sh

######################################################################
# @author      : bjf79 (bjf79@midway2-login1.rcc.local)
# @file        : ExportAllCondaEnvs
# @created     : Monday Apr 19, 2021 13:20:19 CDT
#
# @description : Script to export all conda envs to yaml. Copy pasted from a
# github issues thread: https://github.com/conda/conda/issues/5165
######################################################################


NOW=$(date "+%Y-%m-%d")
CONDA_BASE=$(conda info --base)
CONDA_FUNCTION="etc/profile.d/conda.sh"
CONDA="$CONDA_BASE/$CONDA_FUNCTION"
source $CONDA

mkdir ./condaenvs-$NOW

ENVS=$(conda env list | grep '^\w' | cut -d' ' -f1)
for env in $ENVS; do
    conda activate $env
    conda env export > ./condaenvs-$NOW/$env.yml
    echo "Exporting $env"
done

