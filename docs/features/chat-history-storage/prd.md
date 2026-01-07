# Chat History Storage - Cross-module PRD

> **Doc Type**: Cross-module feature PRD  
> **Created**: 2026-01-07  
> **Last Updated**: 2026-01-07  
> **Modules**: `products/ai_chatbot`, `products/agent_workbench`, `services/session`, `infrastructure/database`, `infrastructure/scheduler`

---

## 1. Overview

### 1.1 Feature Name

Chat History Storage & Retrieval

### 1.2 Background

- Current chat messages are mainly kept in Redis with TTL; data expires and is not queryable long-term.
- `SessionState.history` keeps only a limited number of messages; long conversations get truncated.
- Quality monitoring and optimization require reliable history: search, sampling, export, and basic stats.

### 1.3 Goals (P0)

1. Persist all chat messages (user / AI assistant / human agent) to PostgreSQL in near real-time.
2. Provide an authenticated history query API in the agent workbench:
   - session list
   - session detail (full message flow)
   - keyword search (strong search)
   - basic statistics
   - CSV export
3. Automatic retention cleanup with configurable retention days.

### 1.4 Non-goals (for now)

- Storing tool-call traces / system events (only chat messages: user, assistant, agent).
- Excel/XLSX export.

---

## 2. Module Responsibilities

| Layer | Module | Responsibility |
|------|--------|----------------|
| products | `products/ai_chatbot` | Save user + assistant messages (and assistant response time) |
| products | `products/agent_workbench` | Save agent messages; provide history query/export API + UI |
| services | `services/session` | Provide `MessageStoreService` for write/query/search/export |
| infrastructure | `infrastructure/database` | Define `chat_messages` model + migrations |
| infrastructure | `infrastructure/scheduler` | Daily cleanup job based on retention config |

---

## 3. Data Requirements

### 3.1 Messages to Persist

- `role=user`: end-user message content
- `role=assistant`: AI assistant reply content + `response_time_ms`
- `role=agent`: human agent message content + agent identity

### 3.2 Key Identifiers

- `session_name`: stable session identifier (user_id / session_id)
- `conversation_id`: Coze conversation id (nullable; may be unknown for the first user message if Coze fails early)

### 3.3 Terminology and Aggregation Rules (Strong Constraint)

Definitions:
- **Session (Workbench “Conversation”)**: a customer interaction thread identified by `session_name`.
- **Conversation Segment**: a Coze-level thread identified by `conversation_id` (may be NULL for early/failed messages).

Strong constraints:
1. **Session list MUST be aggregated by `session_name`**, not by `conversation_id`.
2. `conversation_id` is treated as an attribute for filtering/segmenting within a session, not the primary grouping key.
3. Messages with `conversation_id IS NULL` MUST still appear in the session (they are part of the session history).

### 3.3 Retention Policy

- Configurable retention, default 30 days.
- Cleanup is performed by scheduled task.

Configuration:
- `CHAT_HISTORY_RETENTION_DAYS` (int, default `30`)

---

## 4. Cross-module Interaction

### 4.1 Write Flow

1. **AI chatbot**
   - User message received → persist `role=user`
   - Coze reply received → persist `role=assistant` + response time
2. **Agent workbench**
   - Agent sends message → persist `role=agent` + agent identity

Write requirements:
- Best-effort persistence: failures must not break chat or agent messaging.
- Storage should not noticeably slow the request path.

### 4.2 Read Flow (Workbench)

Workbench calls history APIs to:
- List sessions/conversations with time range filters
- Fetch a full message stream
- Search across messages with keyword query (strong search)
- Export to CSV

---

## 5. APIs (Workbench)

All endpoints are served by `products/agent_workbench` and must be protected by existing agent JWT auth.

Base prefix rules:
- Agent workbench app router already mounts under `config.api_prefix` (usually `/api`).
- History routes should be mounted once under the same prefix.

Endpoints (final paths):

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/history/sessions` | List sessions (paged) |
| GET | `/api/history/sessions/{session_name}` | Session detail (messages) |
| GET | `/api/history/search` | Strong keyword search |
| GET | `/api/history/statistics` | Basic stats |
| GET | `/api/history/export` | Export CSV |

### 5.1 Query Parameters (Definition)

- `GET /api/history/sessions`
  - `page` (default 1), `page_size` (default 20)
  - `start_time` (unix seconds, optional), `end_time` (unix seconds, optional)
  - Returns: session summaries grouped by `session_name`, ordered by `last_message_at` desc
  - Summary fields (minimum):
    - `session_name`
    - `message_count` (all roles)
    - `first_message_at` (min `created_at`)
    - `last_message_at` (max `created_at`)
    - `conversation_count` (distinct non-NULL `conversation_id`, optional)
- `GET /api/history/sessions/{session_name}`
  - `limit` (default 100), `offset` (default 0)
  - Returns: messages ordered by `created_at` asc
- `GET /api/history/search`
  - `q` (keyword query, required; supports multi-word)
  - `start_time`, `end_time` (optional)
  - `page`, `page_size`
  - Optional filters: `role` (user/assistant/agent), `session_name` (exact match)
  - Returns: matches ordered by relevance and time
- `GET /api/history/statistics`
  - `start_time`, `end_time` (optional)
  - Returns: counts by role + avg assistant response time
- `GET /api/history/export`
  - `session_name` (required)
  - `start_time`, `end_time` (optional)
  - Returns: CSV file (UTF-8)

---

## 6. User Stories

1. As a quality manager, I can review all conversations within the retention window.
2. As an agent, I can search prior conversations by keyword to find similar cases.
3. As an analyst, I can export a conversation to CSV for offline analysis.
4. As a compliance owner, I can ensure chat data expires according to configured retention.

---

## 7. Success Criteria

### 7.1 Functional

- All user/assistant/agent messages are persisted to PostgreSQL.
- Workbench can list sessions and display full message flows.
- Search supports multi-word queries and returns relevant matches.
- CSV export downloads correctly.
- Scheduled cleanup deletes expired data according to `CHAT_HISTORY_RETENTION_DAYS`.

### 7.2 Non-functional

- Storage failures do not block chat responses or agent messaging (degraded but functional).
- Query endpoints are paginated and index-backed.
- Access control: history endpoints require agent auth.
