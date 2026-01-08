import json
import os
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from products.ai_chatbot import dependencies as deps
from products.ai_chatbot.handlers import chat as chat_module
from products.ai_chatbot.handlers.chat import router as chat_router
from products.ai_chatbot.handlers.manual import router as manual_router
from services.session.regulator import Regulator
from services.session.state import SessionState, SessionStatus


class _DummyTokenManager:
    def get_access_token(self, session_name: str):
        return "dummy-token"

    def invalidate_token(self, session_name: str):
        return None


class _FakeResponse:
    def __init__(self, status_code: int = 200, lines=None):
        self.status_code = status_code
        self._lines = list(lines or [])

    async def aread(self):
        return b""

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _FakeStreamCtx:
    def __init__(self, response: _FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def stream(self, method, url, json=None, headers=None):
        # Minimal SSE-like lines that the handlers parse.
        lines = [
            "event: conversation.message.delta",
            'data: {"conversation_id":"conv_test_1","role":"assistant","content":"Hello"}',
        ]
        return _FakeStreamCtx(_FakeResponse(status_code=200, lines=lines))


class _TestSessionStore:
    def __init__(self):
        self._store: dict[str, SessionState] = {}

    async def get(self, session_name: str):
        return self._store.get(session_name)

    async def save(self, state: SessionState):
        self._store[state.session_name] = state
        return True

    async def get_or_create(self, session_name: str, conversation_id: str | None = None):
        state = await self.get(session_name)
        if state is None:
            state = SessionState(session_name=session_name, conversation_id=conversation_id)
            await self.save(state)
        return state


class ContactOnlyIntegrationTest(unittest.TestCase):
    def setUp(self):
        os.environ.pop("ENABLE_MANUAL_HANDOFF", None)

        self._orig_async_client = chat_module.httpx.AsyncClient
        chat_module.httpx.AsyncClient = _FakeAsyncClient

        store = _TestSessionStore()
        deps.set_session_store(store)
        deps.set_token_manager(_DummyTokenManager())
        deps.set_regulator(Regulator())
        deps.set_config("wf_dummy", "app_dummy")
        deps.set_message_store(None)

        app = FastAPI()
        app.include_router(chat_router, prefix="/api")
        app.include_router(manual_router, prefix="/api")
        self._app = app
        self._client = TestClient(app)
        self._store = store

    def tearDown(self):
        chat_module.httpx.AsyncClient = self._orig_async_client

    def _read_sse_events(self, resp):
        events = []
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            if not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            events.append(payload)
        return events

    def test_manual_escalate_is_contact_only(self):
        resp = self._client.post("/api/manual/escalate", json={"session_name": "s1", "reason": "manual"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["handoff_enabled"], False)
        self.assertIn("You can reach our support team", body["contact_message"])
        self.assertNotIn(body["data"]["status"], [SessionStatus.PENDING_MANUAL, SessionStatus.MANUAL_LIVE])

    def test_chat_appends_contact_message_on_keyword(self):
        resp = self._client.post("/api/chat", json={"message": "我要转人工", "user_id": "s2"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertIn("Hello", body["message"])
        self.assertIn("You can reach our support team", body["message"])

    def test_chat_does_not_409_when_session_in_pending_manual(self):
        # Create a state and force it into pending_manual to ensure contact-only ignores it.
        import asyncio

        async def _prep():
            s = await self._store.get_or_create("s3")
            s.status = SessionStatus.PENDING_MANUAL
            await self._store.save(s)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_prep())
        finally:
            loop.close()
            asyncio.set_event_loop(None)

        resp = self._client.post("/api/chat", json={"message": "hi", "user_id": "s3"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])

    def test_chat_stream_appends_contact_message_on_keyword(self):
        with self._client.stream("POST", "/api/chat/stream", json={"message": "转人工", "user_id": "s4"}) as resp:
            self.assertEqual(resp.status_code, 200)
            events = self._read_sse_events(resp)

        types = [e.get("type") for e in events]
        self.assertIn("message", types)
        self.assertIn("done", types)
        joined = "".join(e.get("content", "") for e in events if e.get("type") == "message")
        self.assertIn("Hello", joined)
        self.assertIn("You can reach our support team", joined)


if __name__ == "__main__":
    unittest.main()
