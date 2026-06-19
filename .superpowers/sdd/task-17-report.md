# Task 17: API 路由 — Report

## Summary

Implemented 3 API route files and 1 test file for the FastAPI-based REST API layer.

## Files Created

| File | Description |
|------|-------------|
| `src/api/chat.py` | 对话路由: POST /chat (sync ainvoke), POST /chat/stream (SSE astream_events), POST /chat/{session_id}/approve |
| `src/api/sessions.py` | 会话管理: POST /sessions, GET /sessions/{id}/history, DELETE /sessions/{id} |
| `src/api/health.py` | 系统路由: GET /health, GET /metrics, GET /skills, POST /skills/reload |
| `tests/unit/test_api.py` | 2 tests: ChatRequest validation (min/max length, required fields), HealthResponse defaults & custom values |

## Updated Files

| File | Change |
|------|--------|
| `src/api/__init__.py` | Exports `chat_router`, `sessions_router`, `health_router` |

## Endpoints (11 total)

1. `POST /api/v1/chat` — Synchronous chat via `graph.ainvoke()`
2. `POST /api/v1/chat/stream` — SSE streaming via `graph.astream_events()`
3. `POST /api/v1/chat/{session_id}/approve` — Human approval callback
4. `POST /api/v1/sessions` — Create session
5. `GET /api/v1/sessions/{session_id}/history` — Get session history from checkpointer
6. `DELETE /api/v1/sessions/{session_id}` — Delete session
7. `GET /api/v1/health` — Health check returning HealthResponse
8. `GET /api/v1/metrics` — Agent runtime metrics
9. `GET /api/v1/skills` — List loaded skills
10. `POST /api/v1/skills/reload` — Reload skills from disk

## Key Design Decisions

- All routes use `req.app.state.graph` / `memory` / `skill_registry` / `mcp` / `settings` for dependency injection via FastAPI app state
- Stream endpoint uses `text/event-stream` media type with `parse_graph_event` from `stream_parser`
- Config passes `thread_id`, `user_id`, `access_token` via LangGraph `configurable` dict
- Metrics tracked via global `get_metrics()` singleton
- Sessions use `uuid4()` for new session IDs when none provided

## Tests

- `tests/unit/test_api.py`: 2 tests, both passing
- Full test suite: 91/91 passing (excluding pre-existing `test_middleware.py` import error)
