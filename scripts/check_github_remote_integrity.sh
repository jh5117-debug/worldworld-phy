#!/usr/bin/env bash
set -euo pipefail

EXPECTED_REMOTE="ssh://git@ssh.github.com:443/jh5117-debug/worldworld-phy.git"
OLD_BAD_REMOTE="world_model_phys.git"

echo "== git remote -v =="
git remote -v

origin_url="$(git remote get-url origin)"
if [[ "${origin_url}" != "${EXPECTED_REMOTE}" ]]; then
  echo "ERROR: origin is not the expected GitHub repository." >&2
  echo "Expected: ${EXPECTED_REMOTE}" >&2
  echo "Actual:   ${origin_url}" >&2
  exit 1
fi

if git remote -v | grep -q "${OLD_BAD_REMOTE}"; then
  echo "ERROR: stale remote still references ${OLD_BAD_REMOTE}" >&2
  exit 1
fi

echo "== git ls-remote --heads origin =="
git ls-remote --heads origin

echo "Remote integrity check passed: origin points to ${EXPECTED_REMOTE}"
