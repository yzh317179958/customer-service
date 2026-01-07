# Chat History Storage - Implementation Plan (Cross-module)

> **Style**: Vibe Coding (docs-first, small steps, verification included)  
> **Dev Order**: infrastructure → services → products  
> **CSV only**: no Excel/XLSX  
> **Search**: PostgreSQL full-text search (strong search)

---

## Phase 0: Final Decisions (Lock Before Coding)

Confirm in code/config:
- Persist only chat messages (`user`, `assistant`, `agent`); no tool/system events for now.
- `created_at` is Unix timestamp seconds (`float`) to match existing DB models.
- Retention is configurable via `CHAT_HISTORY_RETENTION_DAYS` (default `30`).
- Export format is CSV only.
- Search is “strong” via PostgreSQL full-text search (`content_tsv` + GIN).

Verification:
- Team agrees on endpoint paths: `/api/history/*` (no double `/api/api` prefixing).

---

## Phase 1: Infrastructure (database + scheduler)

## Step 1: Add `chat_messages` DB model + migration

Tasks:
- Create `ChatMessageModel` under `infrastructure/database/models/`.
- Export it via `infrastructure/database/models/__init__.py`.
- Add DB migration for the table and indexes:
  - `message_id` unique
  - base indexes: `session_name`, `conversation_id`, `created_at`, `role`
  - composite `(created_at, session_name)`
  - full-text search: `content_tsv` + GIN index

Files:
- Add `infrastructure/database/models/chat_message.py`
- Update `infrastructure/database/models/__init__.py`
- Add Alembic migration under `infrastructure/database/migrations/`

Verification:
- `PYTHONPATH=. python3 -c "from infrastructure.database.models import ChatMessageModel; print('OK')"`
- Run migrations in a dev environment and confirm the table + indexes exist.

Expected result:
- Table is created and indexed; model import works.

---

## Step 2: Add configurable retention cleanup job

Tasks:
- Implement a cleanup task that deletes rows with `created_at < now - retention_days`.
- Read retention from env `CHAT_HISTORY_RETENTION_DAYS` (default `30`).
- Register the job in the existing scheduler initialization path (daily at 03:00).

Files:
- Add/Update task file under `infrastructure/scheduler/tasks/`
- Update the scheduler registration location (where other jobs are registered)

Verification:
- Add a manual test command to run the cleanup function once (dev environment).
- Confirm it deletes only expired rows.

Expected result:
- Cleanup runs and respects configured retention.

---

## Phase 2: Services (`services/session`)

## Step 3: Implement `MessageStoreService` (write + query + search + export)

Tasks:
- Create `services/session/message_store.py`.
- Provide a non-blocking write path:
  - `enqueue_save_message(...)` pushes a write request into an in-process async queue.
  - background worker(s) drain the queue and insert into PostgreSQL using `get_db_session()`.
  - DB writes run in a thread to avoid blocking the event loop.
  - if disabled or queue full: log and drop (best-effort).
- Provide read/search/export APIs used by the workbench:
  - `get_sessions(...)` (paged list with time range)
  - `get_messages_by_session(...)` (paged messages)
  - `search_messages(...)` (FTS query + time range + paging)
  - `get_statistics(...)` (counts + avg response time)
  - `export_messages_csv(...)` (CSV bytes)

Files:
- Add `services/session/message_store.py`
- Update `services/session/__init__.py` to export the new service

Verification:
- Minimal unit-style smoke script (local) that:
  - enqueues a message
  - waits briefly for worker flush
  - queries it back
- Confirm search returns matches for multi-word queries.

Expected result:
- Service works in isolation and does not crash when DB is unavailable.

---

## Phase 3: Product integration - AI chatbot (`products/ai_chatbot`)

## Step 4: Wire `MessageStoreService` into ai_chatbot lifecycle

Tasks:
- Add dependency injection entrypoints in `products/ai_chatbot/dependencies.py` to hold a singleton `MessageStoreService`.
- In `products/ai_chatbot/lifespan.py`, initialize the store and start worker(s).

Verification:
- Start ai_chatbot locally; verify no startup errors and service is initialized.

Expected result:
- Store is available via `get_message_store()` in handlers.

---

## Step 5: Persist user + assistant messages in `handlers/chat.py`

Write points:
- After receiving the user message: enqueue `role=user`.
- After generating the final assistant message: enqueue `role=assistant` with `response_time_ms`.

Conversation id handling:
- Use best available `conversation_id`:
  - request-provided `conversation_id`, else cached value, else NULL.
- If Coze returns a new `conversation_id`, store it on the session state for subsequent messages.

Degrade behavior:
- Storage failures must not affect API responses.

Verification:
- Send a chat message; confirm DB contains two rows (user + assistant).
- Validate that the assistant row has `response_time_ms`.

Expected result:
- AI chat flow persists messages reliably with minimal added latency.

---

## Phase 4: Product integration - Agent workbench (`products/agent_workbench`)

## Step 6: Persist agent messages (manual chat)

Write point:
- In `products/agent_workbench/handlers/sessions.py` (`agent_send_message`), after saving to `SessionState.history`, enqueue `role=agent` with `agent_id/agent_name`.

Verification:
- Take over a session and send an agent message; confirm a DB row with `role=agent` is created.

Expected result:
- Human agent messages are included in stored history.

---

## Step 7: Add authenticated history API in workbench backend

Tasks:
- Create `products/agent_workbench/handlers/history.py` implementing:
  - `GET /history/sessions`
  - `GET /history/sessions/{session_name}`
  - `GET /history/search`
  - `GET /history/statistics`
  - `GET /history/export` (CSV only)
- Protect all endpoints with existing `require_agent`.
- Ensure router mounting results in final paths under `/api/history/*` (no duplicated prefix).

API contract (minimum):
- Session list aggregation is **by `session_name`** (never by `conversation_id`).
- Messages with `conversation_id IS NULL` are still included in session history and counts.
- `/history/search` uses query param `q` (required) and supports multi-word queries (FTS).
- `/history/export` returns UTF-8 CSV and accepts `session_name` (required) + optional time range filters.

Files:
- Add `products/agent_workbench/handlers/history.py`
- Update `products/agent_workbench/routes.py` to include the router
- Update `products/agent_workbench/dependencies.py` to expose the shared `MessageStoreService` instance

Verification:
- Call endpoints with a valid agent token; confirm 200.
- Call endpoints without token; confirm 401.
- Export endpoint returns a downloadable CSV.

Expected result:
- Workbench backend can browse/search/export history securely.

---

## Step 8: Add history UI page in workbench frontend (React)

Tasks:
- Add a page/component under `products/agent_workbench/frontend/components/` (aligned with existing structure).
- Add API client wrapper under `products/agent_workbench/frontend/src/api/`.
- Add a sidebar menu item and a route to the new page.

UI requirements:
- Paged session list with time filter
- Session detail panel
- Keyword search
- CSV export button

Verification:
- Manual UI test: list sessions, open detail, search, export.

Expected result:
- Agents can self-serve historical chat review.

---

## Phase 5: End-to-end Verification

## Step 9: E2E check across both products

Scenarios:
- AI chat persists user + assistant messages.
- Agent message persists during manual mode.
- Workbench history APIs can retrieve the full message stream.
- Search returns relevant hits for multi-word queries.
- Retention cleanup deletes expired data according to config.

Performance checks (sanity):
- Chat response latency should not regress noticeably (writes are queued).
