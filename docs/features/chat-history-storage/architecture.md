# Chat History Storage - Architecture

> **Feature**: Chat History Storage & Retrieval  
> **Created**: 2026-01-07  
> **Last Updated**: 2026-01-07  
> **Norms**: `CLAUDE.md` 3-layer architecture + Vibe Coding docs-first workflow

---

## 1. Layered Architecture (Products → Services → Infrastructure)

```
products/ai_chatbot ───────────────┐
                                   │  (imports)
products/agent_workbench ──────────┼──────▶ services/session/message_store.py
                                   │              │
                                   │              │ (imports)
                                   │              ▼
                                   └──────▶ infrastructure/database/models/chat_message.py
                                                  │
                                                  ▼
                                            PostgreSQL chat_messages

infrastructure/scheduler/tasks/cleanup_chat_history.py ───────────────▶ PostgreSQL chat_messages
```

Rules:
- Products do not import each other.
- Both products depend on the shared service (`services/session`).
- The service layer is the only place that touches DB models.

---

## 2. Main Components

### 2.1 `infrastructure/database`

- Add a new SQLAlchemy model: `ChatMessageModel`
- Add migrations and indexes (including full-text search index)

Implemented files (Step 1):
- `infrastructure/database/models/chat_message.py`
  - Purpose: ORM model for `chat_messages` (user/assistant/agent messages)
  - Notable fields: `message_id` (idempotency), `created_at` (float unix seconds), `content_tsv` (FTS)
- `infrastructure/database/migrations/versions/3b6c9e2f4a7d_add_chat_messages_table.py`
  - Purpose: create `chat_messages` + indexes + trigger-maintained `content_tsv` + GIN index

Testing note:
- In this sandbox environment, starting PostgreSQL and connecting via unix sockets required elevated permissions; Step 1 was verified by running Alembic against a local user-space Postgres instance and inspecting the created table/indexes/triggers via `psql`.

### 2.2 `services/session`

`MessageStoreService` provides:
- Write: `enqueue_save_message(...)` (best-effort, non-blocking)
- Read: session listing + message retrieval
- Search: PostgreSQL full-text search
- Export: CSV only

Implemented files (Step 3):
- `services/session/message_store.py`
  - Purpose: shared persistence/query/search/export service for chat history
  - Notes: in-process async queue + worker(s); DB ops run in a thread; FTS via `content_tsv`

Write pipeline design:
- Each running process (ai_chatbot, agent_workbench) maintains an in-process queue + worker(s).
- Worker uses `get_db_session()` and performs inserts in a thread to avoid blocking the event loop.
- When storage is disabled or unhealthy, writes are skipped (best-effort).

### 2.3 `products/ai_chatbot`

Write points:
- User message received (save `role=user`)
- Assistant final reply produced (save `role=assistant` + `response_time_ms`)

Notes:
- `conversation_id` may be unknown for the first message; store NULL if not available.
- Storage failures must not break the chat endpoint.

Implemented files (Step 4):
- `products/ai_chatbot/dependencies.py`
  - Purpose: store and expose `MessageStoreService` instance via DI getter
- `products/ai_chatbot/lifespan.py`
  - Purpose: initialize `MessageStoreService` and start/stop workers with the product lifecycle

Implemented files (Step 5):
- `products/ai_chatbot/handlers/chat.py`
  - Purpose: enqueue persistence of `user` message (pre-Coze) and `assistant` final reply (post-Coze) for both sync and stream endpoints

### 2.4 `products/agent_workbench`

Write points:
- Agent sends a message (`agent_send_message`): save `role=agent` with `agent_id/agent_name`.

Read points:
- Provide authenticated `/api/history/*` endpoints using `MessageStoreService`.
- Provide a React UI page for history browsing, search, and CSV export.

Implemented files (Step 6):
- `products/agent_workbench/dependencies.py`
  - Purpose: store and expose `MessageStoreService` instance via DI getter
- `products/agent_workbench/lifespan.py`
  - Purpose: initialize `MessageStoreService` and start/stop workers with the product lifecycle
- `products/agent_workbench/handlers/sessions.py`
  - Purpose: enqueue persistence of `agent` messages in `agent_send_message`

Implemented files (Step 7):
- `products/agent_workbench/handlers/history.py`
  - Purpose: authenticated history APIs (list/detail/search/stats/export) backed by `MessageStoreService`
- `products/agent_workbench/routes.py`
  - Purpose: register history router

Implemented files (Step 8):
- `products/agent_workbench/frontend/src/api/history.ts`
  - Purpose: frontend API wrapper for `/api/history/*` (sessions/detail/search/stats/export)
- `products/agent_workbench/frontend/components/ChatHistoryView.tsx`
  - Purpose: history UI page (session list + detail + search + CSV export)
- `products/agent_workbench/frontend/components/Sidebar.tsx`
  - Purpose: adds a navigation entry to `/history`
- `products/agent_workbench/frontend/App.tsx`
  - Purpose: registers the `/history` route

### 2.5 `infrastructure/scheduler`

- Daily cleanup job deletes messages older than `CHAT_HISTORY_RETENTION_DAYS`.

Implemented files (Step 2):
- `infrastructure/scheduler/tasks/cleanup_chat_history.py`
  - Purpose: delete `chat_messages` rows older than `CHAT_HISTORY_RETENTION_DAYS`
- `infrastructure/bootstrap/scheduler.py`
  - Purpose: register a daily cron job (`cleanup_chat_history`, 03:00) that runs `cleanup_old_chat_messages()`

---

## 3. Data Flow

### 3.1 Persisting Messages

```
User message ──▶ ai_chatbot ──▶ MessageStoreService.enqueue_save_message ──▶ DB insert
AI reply     ──▶ ai_chatbot ──▶ MessageStoreService.enqueue_save_message ──▶ DB insert
Agent msg    ──▶ agent_workbench ─▶ MessageStoreService.enqueue_save_message ─▶ DB insert
```

### 3.2 Querying History

```
Workbench UI ──▶ agent_workbench /api/history/* ──▶ MessageStoreService (queries) ──▶ PostgreSQL
```

---

## 4. Key Data Modeling Decisions

- `created_at`: Unix timestamp seconds (`float`) for consistency with existing models.
- `message_id`: UUID string for idempotency (safe retries).
- Strong search: PostgreSQL full-text search via `content_tsv` + GIN index.
- Export: CSV only (no extra dependencies).
- Session list aggregation: **group by `session_name`** (workbench session identity). `conversation_id` is only for optional segmentation/filtering within a session.

---

## 5. Configuration

- `CHAT_HISTORY_ENABLED` (default `true`)
- `CHAT_HISTORY_QUEUE_MAXSIZE` (default `2000`)
- `CHAT_HISTORY_WORKERS` (default `1`)
- `CHAT_HISTORY_RETENTION_DAYS` (default `30`)

---

## 6. Security & Access Control

- History endpoints are protected by existing agent JWT auth (`require_agent`).
- Message storage should avoid collecting sensitive fields; persist only message content + minimal identifiers.
