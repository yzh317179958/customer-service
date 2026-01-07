#!/usr/bin/env bash
set -euo pipefail

# Deploy to Fiido AI server (agent_workbench + ai_chatbot).
#
# This script intentionally does NOT embed passwords.
# Prefer SSH key auth. If you only have password auth, run this script manually in a terminal.
#
# Usage:
#   bash deploy/scripts/deploy-to-ai-server.sh
#   DEPLOY_HOST=8.211.27.199 DEPLOY_USER=root bash deploy/scripts/deploy-to-ai-server.sh
#   SKIP_FRONTEND_BUILD=1 bash deploy/scripts/deploy-to-ai-server.sh
#
# Requires (local):
#   - rsync, ssh
#   - node/npm (unless SKIP_FRONTEND_BUILD=1)
#
# Requires (server):
#   - systemd services: fiido-ai-chatbot, fiido-agent-workbench
#   - nginx static dirs:
#       /var/www/fiido-frontend/   (ai_chatbot)
#       /var/www/fiido-workbench/  (agent_workbench)
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_HOST="${DEPLOY_HOST:-8.211.27.199}"
DEPLOY_USER="${DEPLOY_USER:-root}"
SERVER_ROOT="${SERVER_ROOT:-/opt/fiido-ai-service}"
SERVER_AI_FE_DIR="${SERVER_AI_FE_DIR:-/var/www/fiido-frontend}"
SERVER_WB_FE_DIR="${SERVER_WB_FE_DIR:-/var/www/fiido-workbench}"

SKIP_FRONTEND_BUILD="${SKIP_FRONTEND_BUILD:-0}"
SKIP_SERVICE_RESTART="${SKIP_SERVICE_RESTART:-0}"
SKIP_PREFLIGHT="${SKIP_PREFLIGHT:-0}"
SYNC_ENV="${SYNC_ENV:-0}"
SYNC_KEYS="${SYNC_KEYS:-0}"

echo "[deploy] repo: ${ROOT_DIR}"
echo "[deploy] server: ${DEPLOY_USER}@${DEPLOY_HOST}"
echo "[deploy] server_root: ${SERVER_ROOT}"

cd "${ROOT_DIR}"

if [[ "${SKIP_PREFLIGHT}" != "1" ]]; then
  echo "[deploy] preflight: checking SSH key auth (BatchMode)..."
  if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${DEPLOY_USER}@${DEPLOY_HOST}" "echo ok" >/dev/null 2>&1; then
    cat <<'EOF'
[deploy] ERROR: SSH key auth not available (BatchMode check failed).
 - If you want password login, rerun this script manually in an interactive terminal (not via automation).
 - Recommended: set up an SSH key:
     ssh-copy-id root@8.211.27.199
   then rerun:
     bash deploy/scripts/deploy-to-ai-server.sh
EOF
    exit 2
  fi
  echo "[deploy] preflight ok"
fi

if [[ "${SKIP_FRONTEND_BUILD}" != "1" ]]; then
  echo "[deploy] building frontends locally..."

  echo "[deploy] ai_chatbot frontend build"
  (cd products/ai_chatbot/frontend && npm -s run build)

  echo "[deploy] agent_workbench frontend build"
  (cd products/agent_workbench/frontend && npm -s run build)
else
  echo "[deploy] SKIP_FRONTEND_BUILD=1; skipping local frontend builds"
fi

echo "[deploy] syncing python code (split rsync; see CLAUDE.md 3.6/3.7)"
rsync -avz --exclude '__pycache__' --exclude 'node_modules' --exclude '.git' \
  --exclude '.local_*' \
  products/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/products/"
rsync -avz --exclude '__pycache__' --exclude 'node_modules' --exclude '.git' \
  --exclude '.local_*' \
  services/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/services/"
rsync -avz --exclude '__pycache__' --exclude 'node_modules' --exclude '.git' \
  --exclude '.local_*' \
  infrastructure/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/infrastructure/"
rsync -avz assets/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/assets/"
if [[ "${SYNC_KEYS}" == "1" ]]; then
  rsync -avz config/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/config/"
else
  rsync -avz --exclude 'private_key*.pem' config/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/config/"
  echo "[deploy] NOTE: skipped syncing config/private_key*.pem (set SYNC_KEYS=1 to include)"
fi

rsync -avz requirements.txt "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/"
if [[ "${SYNC_ENV}" == "1" ]]; then
  rsync -avz .env "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_ROOT}/"
else
  echo "[deploy] NOTE: skipped syncing .env (set SYNC_ENV=1 to include)"
fi

echo "[deploy] syncing built frontends to nginx static dirs"
rsync -avz --delete products/ai_chatbot/frontend/dist/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_AI_FE_DIR}/"
rsync -avz --delete products/agent_workbench/frontend/dist/ "${DEPLOY_USER}@${DEPLOY_HOST}:${SERVER_WB_FE_DIR}/"

if [[ "${SKIP_SERVICE_RESTART}" != "1" ]]; then
  echo "[deploy] restarting services"
  ssh "${DEPLOY_USER}@${DEPLOY_HOST}" "systemctl restart fiido-ai-chatbot fiido-agent-workbench"
  echo "[deploy] status"
  ssh "${DEPLOY_USER}@${DEPLOY_HOST}" "systemctl --no-pager --full status fiido-ai-chatbot fiido-agent-workbench | sed -n '1,60p'"
else
  echo "[deploy] SKIP_SERVICE_RESTART=1; skipping service restarts"
fi

echo "[deploy] done"
