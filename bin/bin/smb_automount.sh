#!/bin/bash
# Generic SMB automount helper. Mount one share when the server is reachable.
# Usage: smb_automount.sh <keychain_label> <keychain_account> <smb_user> <server> <share> <mountpoint>
#
# Create the required Keychain entry once with:
#   security add-internet-password -s "<keychain_label>" -a "<keychain_account>" -w

KEYCHAIN_LABEL="$1"
KEYCHAIN_ACCOUNT="$2"
SMB_USER="$3"
SERVER="$4"
SHARE="$5"
MOUNTPOINT="$6"

if [[ -z "$SERVER" || -z "$SHARE" || -z "$MOUNTPOINT" ]]; then
  echo "Usage: $0 <keychain_label> <keychain_account> <smb_user> <server> <share> <mountpoint>" >&2
  exit 1
fi

# Skip if already mounted
if mount | grep -q "$SERVER"; then
  exit 0
fi

# Only proceed if server is reachable (VPN check)
if ! /usr/bin/nc -z -w2 "$SERVER" 445 2>/dev/null; then
  exit 0
fi

# Get password from Keychain
PASS=$(security find-internet-password -s "$KEYCHAIN_LABEL" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null)
if [[ -z "$PASS" ]]; then
  echo "$(date): No Keychain entry found for $KEYCHAIN_LABEL / $KEYCHAIN_ACCOUNT" >&2
  exit 1
fi

# URL-encode password to handle special characters
ENCODED_PASS=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$PASS")

mkdir -p "$MOUNTPOINT"
mount_smbfs "//${SMB_USER}:${ENCODED_PASS}@${SERVER}/${SHARE}" "$MOUNTPOINT" \
  && echo "$(date): Mounted ${SERVER}/${SHARE} at ${MOUNTPOINT}" \
  || echo "$(date): Failed to mount ${SERVER}/${SHARE}" >&2
