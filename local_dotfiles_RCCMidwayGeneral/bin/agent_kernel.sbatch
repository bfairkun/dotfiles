#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=4:00:00

ENV=${1:-py_general}
LANG=${2:-python}
CF=$SCRATCH/$USER/agent_kernel.json
[[ "$LANG" == "r" ]] && CF=$SCRATCH/$USER/agent_r_kernel.json

HOST_IP=$(ip route get 8.8.8.8 | awk '{print $7;exit}')
echo "Node: $HOSTNAME  IP: $HOST_IP  Env: $ENV  Lang: $LANG"

source ~/miniconda3/etc/profile.d/conda.sh
conda activate $ENV

echo "Starting kernel..."
if [[ "$LANG" == "r" ]]; then
    # IRkernel reads an existing connection file rather than creating one,
    # so generate it first with jupyter_client then hand it to R
    python -c "
from jupyter_client import write_connection_file
write_connection_file(fname='$CF', ip='$HOST_IP')
"
    R --slave -e "IRkernel::main()" --args $CF
else
    python -m ipykernel_launcher --ip=$HOST_IP -f $CF
fi
