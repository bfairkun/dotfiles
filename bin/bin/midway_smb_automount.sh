#!/bin/bash
# Auto-mount Midway SMB shares when UChicago VPN is connected.
# Requires a Keychain entry created once with:
#   security add-internet-password -s "midway-smb" -a "ADLOCAL\bjf79" -w

DIR="$(dirname "$0")"
"$DIR/smb_automount.sh" midway-smb "ADLOCAL\\bjf79" "ADLOCAL;bjf79" \
  "midway3smb1.rcc.uchicago.edu" "project" "$HOME/mnt/project"
"$DIR/smb_automount.sh" midway-smb "ADLOCAL\\bjf79" "ADLOCAL;bjf79" \
  "midwaysmb.rcc.uchicago.edu" "project2" "$HOME/mnt/project2"
