from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock

try:
    from mcp import Client

    from moodmo_mcp.server import get_mood, list_activities, list_moods, mcp, set_client
except ImportError:  # pragma: no cover - optional extra
    Client = None
    get_mood = list_activities = list_moods = mcp = set_client = None


@unittest.skipUnless(Client is not None, "mcp extra is not installed")
class MoodMoMcpServerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.stub = MagicMock()
        self.stub.list_moods.return_value = {
            "count": 1,
            "results": [{"sqid": "moodsqid1", "mood": 1, "activities": ["Walk"]}],
        }
        self.stub.get_mood.return_value = {
            "sqid": "moodsqid1",
            "mood": 1,
            "note_title": "Nice",
            "note": "",
            "activities": ["Walk"],
            "date": "2026-09-10",
            "time": "12:00:00",
            "last_modified": "2026-09-10T18:00:00+00:00",
        }
        self.stub.list_activities.return_value = {
            "count": 1,
            "results": [{"sqid": "actysqid1", "name": "Walk"}],
        }
        set_client(self.stub)

    def tearDown(self):
        set_client(None)

    async def test_tools_via_in_memory_client(self):
        async with Client(mcp) as client:
            moods = await client.call_tool(
                "list_moods",
                {"since": "2026-09-01T00:00:00Z"},
            )
            mood = await client.call_tool("get_mood", {"sqid": "moodsqid1"})
            activities = await client.call_tool("list_activities", {})

        self.stub.list_moods.assert_called_once_with(since="2026-09-01T00:00:00Z")
        self.stub.get_mood.assert_called_once_with("moodsqid1")
        self.stub.list_activities.assert_called_once_with(since=None)

        self.assertEqual(
            json.loads(self._text(moods)),
            self.stub.list_moods.return_value,
        )
        self.assertEqual(
            json.loads(self._text(mood)),
            self.stub.get_mood.return_value,
        )
        self.assertEqual(
            json.loads(self._text(activities)),
            self.stub.list_activities.return_value,
        )

    def test_tool_functions_directly(self):
        self.assertEqual(
            json.loads(list_moods()),
            self.stub.list_moods.return_value,
        )
        self.assertEqual(
            json.loads(get_mood("moodsqid1")),
            self.stub.get_mood.return_value,
        )
        self.assertEqual(
            json.loads(list_activities(since="2026-01-01T00:00:00Z")),
            self.stub.list_activities.return_value,
        )
        self.stub.list_activities.assert_called_with(since="2026-01-01T00:00:00Z")

    @staticmethod
    def _text(result) -> str:
        if hasattr(result, "content") and result.content:
            block = result.content[0]
            return getattr(block, "text", str(block))
        if hasattr(result, "structured_content") and result.structured_content:
            payload = result.structured_content
            if isinstance(payload, dict) and "result" in payload:
                return payload["result"]
            return json.dumps(payload)
        return str(result)


if __name__ == "__main__":
    unittest.main()
