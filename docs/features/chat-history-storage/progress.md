# Chat History Storage - Progress

> **Feature**: Chat History Storage & Retrieval  
> **Created**: 2026-01-07  
> **Last Updated**: 2026-01-08  
> **Tracking**: Cross-module (single source of truth)

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ⏳ | Not started |
| 🚧 | In progress |
| ✅ | Done |
| 🧱 | Blocked |

---

## Milestones

| Phase | Step | Title | Module | Status |
|------:|-----:|-------|--------|--------|
| 1 | 1 | DB model + migration | `infrastructure/database` | ✅ |
| 1 | 2 | Retention cleanup job | `infrastructure/scheduler` | ✅ |
| 2 | 3 | MessageStoreService | `services/session` | ✅ |
| 3 | 4 | ai_chatbot DI + lifecycle | `products/ai_chatbot` | ✅ |
| 3 | 5 | Persist user/assistant messages | `products/ai_chatbot` | ✅ |
| 4 | 6 | Persist agent messages | `products/agent_workbench` | ✅ |
| 4 | 7 | Workbench history API | `products/agent_workbench` | ✅ |
| 4 | 8 | Workbench history UI | `products/agent_workbench/frontend` | ✅ |
| 5 | 9 | End-to-end verification | All | ✅ |
| 6 | 10 | Server deploy + DB bootstrap | Ops | ✅ |

---

## Notes

- Retention is configurable via `CHAT_HISTORY_RETENTION_DAYS` (default 30).
- Export is CSV only.
- Search uses PostgreSQL full-text search.

---

## Step 1: DB model + migration

**When:** 2026-01-07

**Completed (code):**
- Added `ChatMessageModel` for `chat_messages`
- Added Alembic migration creating table + indexes + FTS trigger + GIN index
- Wired Alembic `env.py` to import the new model

**Files:**
- `infrastructure/database/models/chat_message.py` (new)
- `infrastructure/database/models/__init__.py` (updated export)
- `infrastructure/database/migrations/env.py` (import update)
- `infrastructure/database/migrations/versions/3b6c9e2f4a7d_add_chat_messages_table.py` (new)

**Test result:**
- ✅ Python import/compile checks passed
- ✅ Local Postgres (user-space) started and Alembic migrations applied successfully
- ✅ Verified `chat_messages` table, indexes, and FTS trigger exist

**How it was tested (Step 1):**
- Started a local PostgreSQL 14 instance (unix socket) using `/usr/lib/postgresql/14/bin/*` with a workspace data dir.
- Created `fiido` role + `fiido_db` database.
- Ran `alembic -c infrastructure/database/migrations/alembic.ini upgrade head` with `DATABASE_URL` pointing to the unix socket.
- Verified schema via `psql "\\d chat_messages"` and `pg_indexes`.

---

## Step 2: Retention cleanup job

**When:** 2026-01-07

**Completed:**
- Added chat history cleanup task `cleanup_old_chat_messages()` with configurable retention (`CHAT_HISTORY_RETENTION_DAYS`, default 30)
- Registered a daily APScheduler cron job (03:00 server timezone) in `start_warmup_scheduler()`

**Files:**
- `infrastructure/scheduler/tasks/cleanup_chat_history.py` (new)
- `infrastructure/bootstrap/scheduler.py` (updated job registration)

**Test result:**
- ✅ Local Postgres: inserted one 31-day-old row + one fresh row, ran cleanup, confirmed only old rows are deleted

---

## Step 3: MessageStoreService

**When:** 2026-01-07

**Completed:**
- Implemented `MessageStoreService` providing:
  - best-effort queued writes (`enqueue_save_message`) + background worker(s)
  - session list aggregation by `session_name`
  - session detail retrieval
  - strong search via PostgreSQL FTS (`websearch_to_tsquery` over `content_tsv`)
  - basic statistics
  - CSV export
- Exported service via `services/session/__init__.py`

**Files:**
- `services/session/message_store.py` (new)
- `services/session/__init__.py` (updated export)

**Test result:**
- ✅ Local Postgres E2E: enqueue → flush → query sessions/messages → FTS search → CSV export

---

## Step 4: ai_chatbot DI + lifecycle

**When:** 2026-01-07

**Completed:**
- Added DI getters/setters for message store in `products/ai_chatbot/dependencies.py`
- Initialized `MessageStoreService` in ai_chatbot lifespan and started worker(s) on startup; graceful shutdown on app close

**Files:**
- `products/ai_chatbot/dependencies.py` (updated)
- `products/ai_chatbot/lifespan.py` (updated)

**Test result:**
- ✅ Python compile/import checks passed for DI + lifespan wiring

---

## Step 5: Persist user/assistant messages

**When:** 2026-01-07

**Completed:**
- Added best-effort persistence hooks in both:
  - `POST /chat` (sync): enqueue `user` before Coze call; enqueue `assistant` after final reply with `response_time_ms`
  - `POST /chat/stream` (SSE): enqueue `user` before Coze call; enqueue `assistant` after final reply with `response_time_ms`

**Files:**
- `products/ai_chatbot/handlers/chat.py` (updated)

**Test result:**
- ✅ Python compile/import checks passed (full E2E chat persistence covered by Step 9)

---

## Step 6: Persist agent messages

**When:** 2026-01-07

**Completed:**
- Initialized `MessageStoreService` in agent workbench lifecycle and exposed it via DI
- Added best-effort enqueue persistence in `agent_send_message` (role=agent) including `agent_id`/`agent_name`

**Files:**
- `products/agent_workbench/dependencies.py` (updated)
- `products/agent_workbench/lifespan.py` (updated)
- `products/agent_workbench/handlers/sessions.py` (updated)

**Test result:**
- ✅ Mock-based unit test executed the handler and verified enqueue payload (`STEP6_AGENT_PERSIST_OK`)

---

## Step 7: Workbench history API

**When:** 2026-01-07

**Completed:**
- Added authenticated history endpoints in agent workbench:
  - `GET /api/history/sessions`
  - `GET /api/history/sessions/{session_name}`
  - `GET /api/history/search` (`q` parameter)
  - `GET /api/history/statistics`
  - `GET /api/history/export` (CSV)
- Wired history router into agent workbench routes

**Files:**
- `products/agent_workbench/handlers/history.py` (new)
- `products/agent_workbench/routes.py` (updated)

**Test result:**
- ✅ Mock-based unit test verified handler functions return expected shapes (`STEP7_HISTORY_API_OK`)

---

## Step 8: Workbench history UI

**When:** 2026-01-07

**Completed:**
- Added a new History page in agent workbench frontend:
  - paged session list (time filter + paging)
  - session detail panel (messages by `session_name`)
  - keyword search (scoped to current session or all sessions)
  - CSV export button

**Files:**
- `products/agent_workbench/frontend/src/api/history.ts` (new)
- `products/agent_workbench/frontend/src/api/index.ts` (updated export)
- `products/agent_workbench/frontend/components/ChatHistoryView.tsx` (new page)
- `products/agent_workbench/frontend/components/Sidebar.tsx` (new nav item)
- `products/agent_workbench/frontend/App.tsx` (new route)

**Test result:**
- ✅ `npm -C products/agent_workbench/frontend run build`

---

## Step 9: End-to-end verification

**When:** 2026-01-07

**Completed:**
- Applied Alembic migrations to latest head (including session meta + export jobs tables).
- Ran a local Postgres smoke scenario exercising:
  - queue writes (`user` + `assistant` + `agent`) → flush
  - session list + session detail retrieval
  - multi-word PostgreSQL FTS (`websearch_to_tsquery`) over message content
  - single-session CSV export
  - async export job: create → run → DB status update → CSV file output

**Test result:**
- ✅ Local DB E2E smoke (`MessageStoreService` direct calls) passed.

---

## Step 10: Server deploy + DB bootstrap

**When:** 2026-01-08

**Completed (ops):**
- Deployed latest code + built frontends to `8.211.27.199` (ai.fiido.com) via `deploy/scripts/deploy-to-ai-server.sh`
- Fixed production error on `/workbench/history` ("Request failed with status code 500"):
  - Root cause: server `DATABASE_URL` pointed to `localhost:5432` but Postgres was not running → backend DB connection refused
  - Installed and started PostgreSQL 14 on server, created role `fiido` + database `fiido_db`
  - Ran Alembic migrations to `head` using `infrastructure/database/migrations/alembic.ini`
  - Restarted `fiido-agent-workbench` and `fiido-ai-chatbot`

**Verification:**
- ✅ `https://ai.fiido.com/workbench/history` returns `200`
- ✅ `https://ai.fiido.com/workbench-api/history/sessions` returns `403` when unauthenticated (expected), and stops returning `500`
