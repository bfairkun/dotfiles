#!/bin/bash
# Auto-mount Midway SMB shares when UChicago VPN is connected.
# Requires a Keychain entry created once with:
#   security add-internet-password -s "midway-smb" -a "ADLOCAL\bjf79" -w

KEYCHAIN_SERVER="midway-smb"
KEYCHAIN_ACCOUNT="ADLOCAL\\bjf79"
SMB_USER="ADLOCAL;bjf79"

mount_smb_share() {
  local server="$1"
  local share="$2"
  local mountpoint="$3"

  # Skip if already mounted
  if mount | grep -q "$server"; then
    return 0
  fi

  # Only proceed if server is reachable (VPN check)
  if ! /usr/bin/nc -z -w2 "$server" 445 2>/dev/null; then
    return 0
  fi

  # Get password from Keychain
  local pass
  pass=$(security find-internet-password -s "$KEYCHAIN_SERVER" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null)
  if [[ -z "$pass" ]]; then
    echo "$(date): No Keychain entry found for $KEYCHAIN_SERVER / $KEYCHAIN_ACCOUNT" >&2
    return 1
  fi

  # URL-encode password to handle special characters
  local encoded_pass
  encoded_pass=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$pass")

  mkdir -p "$mountpoint"
  mount_smbfs "//${SMB_USER}:${encoded_pass}@${server}/${share}" "$mountpoint" \
    && echo "$(date): Mounted ${server}/${share} at ${mountpoint}" \
    || echo "$(date): Failed to mount ${server}/${share}" >&2
}

mount_smb_share "midway3smb1.rcc.uchicago.edu" "project"  "$HOME/mnt/project"
mount_smb_share "midwaysmb.rcc.uchicago.edu"   "project2" "$HOME/mnt/project2"
