#!/usr/bin/env bash
set -euo pipefail

# Deploy AI Chatbot frontend (products/ai_chatbot/frontend/dist) to a remote server.
#
# Usage:
#   deploy/scripts/deploy-ai-chatbot-frontend.sh root@8.211.27.199 /var/www/fiido-frontend
#
# Notes:
# - Requires SSH key-based auth (recommended). Avoid password automation in scripts.
# - Will upload dist/ contents into the target directory.

REMOTE="${1:-}"
REMOTE_DIR="${2:-}"

if [[ -z "${REMOTE}" || -z "${REMOTE_DIR}" ]]; then
  echo "Usage: $0 <user@host> <remote_dir>" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="${ROOT_DIR}/products/ai_chatbot/frontend/dist"

if [[ ! -d "${DIST_DIR}" ]]; then
  echo "Missing dist directory: ${DIST_DIR}" >&2
  echo "Run: (cd products/ai_chatbot/frontend && npm run build-only)" >&2
  exit 1
fi

echo "Uploading ${DIST_DIR}/ -> ${REMOTE}:${REMOTE_DIR}/"

ssh -o BatchMode=yes "${REMOTE}" "mkdir -p '${REMOTE_DIR}'"

rsync -az --delete \
  -e "ssh -o BatchMode=yes" \
  "${DIST_DIR}/" \
  "${REMOTE}:${REMOTE_DIR}/"

echo "Done."
