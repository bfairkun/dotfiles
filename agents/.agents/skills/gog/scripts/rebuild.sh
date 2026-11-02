#!/usr/bin/env bash
# Build gog from a release tag with gog-policy.yaml baked in.
# Usage: rebuild.sh [vX.Y.Z|latest] [os/arch]
#   no os/arch: install for this machine as ~/.local/bin/gog
#   os/arch (e.g. darwin/arm64, linux/amd64): write ./gog-<os>-<arch> to copy elsewhere
# Needs git, gh (to look up the latest tag), and Go in conda env agent_gobuild.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
out_dir=$PWD
tag=${1:-latest}
[[ $tag == latest ]] && tag=$(gh release view -R openclaw/gogcli --json tagName -q .tagName)
target=${2:-}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

git -c advice.detachedHead=false clone -q --depth 1 --branch "$tag" https://github.com/openclaw/gogcli.git "$work/src"
cp "$here/gog-policy.yaml" "$work/src/policy.yaml"
cd "$work/src"

# Same steps as upstream build-safe.sh, except the policy generator runs for the
# host while only the final build is cross-compiled, and -s -w drops debug info.
# CGO_ENABLED=0: agent_gobuild has no C compiler.
export CGO_ENABLED=0
go() { mamba run -n agent_gobuild go "$@"; }
go run ./cmd/bake-safety-profile policy.yaml internal/cmd/safety_profile_baked_gen.go
pkg=github.com/openclaw/gogcli/internal/cmd
ldflags="-s -w -X $pkg.version=$tag-safe -X $pkg.commit=$(git rev-parse --short=12 HEAD) -X $pkg.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -z $target ]]; then
  go build -tags safety_profile -ldflags "$ldflags" -o "$work/gog" ./cmd/gog
  "$work/gog" --version
  install -m 755 "$work/gog" "$HOME/.local/bin/gog"
  echo "installed $HOME/.local/bin/gog"
else
  out="$out_dir/gog-${target/\//-}"
  GOOS=${target%/*} GOARCH=${target#*/} go build -tags safety_profile -ldflags "$ldflags" -o "$out" ./cmd/gog
  echo "built $out"
fi
