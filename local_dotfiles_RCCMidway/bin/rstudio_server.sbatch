#!/bin/bash
#SBATCH --time=8:00:00
#SBATCH --signal=USR2
#SBATCH --partition=broadwl
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --output=~/.rstudio-server.job
# customize --output path as appropriate (to a directory readable only by the user!)

# See also https://www.rocker-project.org/use/singularity/

# Main parameters for the script with default values
IP=$(/sbin/ip route get 8.8.8.8 | awk '{print $NF;exit}')
readonly PORT=$(python -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
echo "Open RStudio Server at http://${IP}:${PORT}"

USER=$(whoami)
USER_psw="biology"
#USER_psw=$(openssl rand -base64 15)
CONDA_PREFIX="/project2/gilad/bjf79_project1/envs/r_4_2"
TMPDIR=${TMPDIR:-tmp}
MIDWAYHOST=$(hostname | grep -o -P "midway[23]")

# singularity pull docker://rocker/rstudio_latest
dir_repo="/project2/yangili1/bjf79/rstudio-server-conda_share"
# CONTAINER="${dir_repo}/singularity/rstudio_latest.sif"
CONTAINER="/project2/yangili1/bjf79/singularity_sifs/tidyverse_4.2.sif"


# Set-up temporary paths
# RSTUDIO_TMP="${TMPDIR}/$(echo -n $CONDA_PREFIX | md5sum | awk '{print $1}')"
RSTUDIO_TMP="/project2/yangili1/bjf79/rstudioserver/$(echo -n $CONDA_PREFIX | md5sum | awk '{print $1}')"
mkdir -p $RSTUDIO_TMP/{run,var-lib-rstudio-server,local-share-rstudio,tmp}
echo "Made ${RSTUDIO_TMP}"

R_BIN=$CONDA_PREFIX/bin/R
PY_BIN=$CONDA_PREFIX/bin/python

if [ ! -f $CONTAINER ]; then
    singularity build --fakeroot $CONTAINER Singularity
fi

if [ -z "$CONDA_PREFIX" ]; then
  echo "Activate a conda env or specify \$CONDA_PREFIX"
  exit 1
fi

# conda activate $CONDA_PREFIX

cat > ${RSTUDIO_TMP}/rsession.sh <<END
#!/bin/sh
export OMP_NUM_THREADS=1
#export R_LIBS_USER=${CONDA_PREFIX}/lib
exec rsession "\${@}"
END

chmod +x ${RSTUDIO_TMP}/rsession.sh

export SINGULARITYENV_RSTUDIO_SESSION_TIMEOUT=1

export SINGULARITYENV_USER=${USER}
export SINGULARITYENV_PASSWORD=${USER_psw}
export SINGULARITYENV_RSTUDIO_WHICH_R=${R_BIN}
export SINGULARITYENV_CONDA_PREFIX=${CONDA_PREFIX}
export SINGULARITY_CACHEDIR=/scratch/${MIDWAYHOST}/${USER}/.singularity
export SINGULARITY_PATH=/scratch/${MIDWAYHOST}/${USER}/.singularity

cat 1>&2 <<END
1. SSH tunnel from your workstation using the following command:

   ssh -N -L 8787:${HOSTNAME}:${PORT} ${SINGULARITYENV_USER}@${MIDWAYHOST}.rcc.uchicago.edu

   and point your web browser to http://localhost:8787

2. log in to RStudio Server using the following credentials:

   user: ${SINGULARITYENV_USER}
   password: ${SINGULARITYENV_PASSWORD}

When done using RStudio Server, terminate the job by:

1. Exit the RStudio Session ("power" button in the top right corner of the RStudio window)
2. Issue the following command on the login node:

      scancel -f ${SLURM_JOB_ID}
END

/software/singularity-3.4.0-el7-x86_64/bin/singularity exec \
    --bind $RSTUDIO_TMP/run:/run \
    --bind $RSTUDIO_TMP/var-lib-rstudio-server:/var/lib/rstudio-server \
    --bind $RSTUDIO_TMP/tmp:/tmp \
    --bind $RSTUDIO_TMP/rsession.sh:/etc/rstudio/rsession.sh \
    --bind /sys/fs/cgroup/:/sys/fs/cgroup/:ro \
    --bind ${dir_repo}/singularity/database.conf:/etc/rstudio/database.conf \
    --bind ${dir_repo}/singularity/rsession.conf:/etc/rstudio/rsession.conf \
    --bind ${dir_repo}/singularity/rserver.conf:/etc/rstudio/rserver.conf \
    --bind $RSTUDIO_TMP/local-share-rstudio:/home/rstudio/.local/share/rstudio \
    --bind ${CONDA_PREFIX}:${CONDA_PREFIX} \
    --bind $HOME/.config/rstudio:/home/rstudio/.config/rstudio \
    --bind /project2:/project2 \
    --bind /scratch/${MIDWAYHOST}/${USER}:/scratch/${MIDWAYHOST}/${USER} \
    ${CONTAINER} rserver  \
    --www-address=${IP} \
    --www-port=${PORT} \
    --rsession-which-r=${R_BIN} \
    --server-user ${USER} \
    --auth-none=0 \
    --auth-pam-helper-path=pam-helper \
    --auth-timeout-minutes=0 \
    --auth-stay-signed-in-days=3

printf 'rserver exited' 1>&2


# /software/singularity-3.4.0-el7-x86_64/bin/singularity exec \
#     --bind $RSTUDIO_TMP/run:/run \
#     --bind $RSTUDIO_TMP/var-lib-rstudio-server:/var/lib/rstudio-server \
#     --bind $RSTUDIO_TMP/tmp:/tmp \
#     --bind $RSTUDIO_TMP/rsession.sh:/etc/rstudio/rsession.sh \
#     --bind /sys/fs/cgroup/:/sys/fs/cgroup/:ro \
#     --bind ${dir_repo}/singularity/database.conf:/etc/rstudio/database.conf \
#     --bind ${dir_repo}/singularity/rsession.conf:/etc/rstudio/rsession.conf \
#     --bind ${dir_repo}/singularity/rserver.conf:/etc/rstudio/rserver.conf \
#     --bind $RSTUDIO_TMP/local-share-rstudio:/home/rstudio/.local/share/rstudio \
#     --bind ${CONDA_PREFIX}:${CONDA_PREFIX} \
#     --bind $HOME/.config/rstudio:/home/rstudio/.config/rstudio \
#     --bind /project2:/project2 \
#     --bind /scratch/midway2/${USER}:/scratch/midway2/${USER} \
#     ${CONTAINER} R
