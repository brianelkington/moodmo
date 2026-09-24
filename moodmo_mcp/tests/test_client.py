from __future__ import annotations

import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from moodmo_mcp.client import MoodMoApiClient, MoodMoApiError


class MoodMoApiClientTest(unittest.TestCase):
    def test_requires_base_url(self):
        with self.assertRaises(MoodMoApiError) as ctx:
            MoodMoApiClient(base_url="", token="secret")
        self.assertIn("MOODMO_API_BASE_URL", str(ctx.exception))

    def test_requires_token(self):
        with self.assertRaises(MoodMoApiError) as ctx:
            MoodMoApiClient(base_url="http://127.0.0.1:8000", token="")
        self.assertIn("MOODMO_API_TOKEN", str(ctx.exception))

    def test_reads_env_vars(self):
        with patch.dict(
            "os.environ",
            {
                "MOODMO_API_BASE_URL": "http://example.test/",
                "MOODMO_API_TOKEN": "env-token",
            },
        ):
            client = MoodMoApiClient()

        self.assertEqual(client.base_url, "http://example.test")
        self.assertEqual(client.token, "env-token")

    @patch("moodmo_mcp.client.urlopen")
    def test_list_moods_success_and_auth_header(self, mock_urlopen):
        payload = {
            "count": 1,
            "results": [
                {
                    "sqid": "abc12345",
                    "mood": 1,
                    "note_title": "Good day",
                    "note": "",
                    "activities": ["Running"],
                    "date": "2026-09-10",
                    "time": "13:00:00",
                    "last_modified": "2026-09-10T19:00:00+00:00",
                }
            ],
        }
        response = MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response

        client = MoodMoApiClient(
            base_url="http://127.0.0.1:8000",
            token="test-token",
        )
        result = client.list_moods()

        self.assertEqual(result, payload)
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8000/api/v1/moods/")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(request.get_header("Accept"), "application/json")

    @patch("moodmo_mcp.client.urlopen")
    def test_list_moods_appends_since_query(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = b'{"count": 0, "results": []}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response

        client = MoodMoApiClient(
            base_url="http://127.0.0.1:8000",
            token="test-token",
        )
        client.list_moods(since="2026-09-01T00:00:00Z")

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "http://127.0.0.1:8000/api/v1/moods/?since=2026-09-01T00%3A00%3A00Z",
        )

    @patch("moodmo_mcp.client.urlopen")
    def test_get_mood_404(self, mock_urlopen):
        error = HTTPError(
            url="http://127.0.0.1:8000/api/v1/moods/missing1/",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=io.BytesIO(b'{"error": "Mood not found"}'),
        )
        mock_urlopen.side_effect = error

        client = MoodMoApiClient(
            base_url="http://127.0.0.1:8000",
            token="test-token",
        )
        with self.assertRaises(MoodMoApiError) as ctx:
            client.get_mood("missing1")

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(str(ctx.exception), "Mood not found")

    @patch("moodmo_mcp.client.urlopen")
    def test_list_activities_401(self, mock_urlopen):
        error = HTTPError(
            url="http://127.0.0.1:8000/api/v1/activities/",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error": "Authentication required"}'),
        )
        mock_urlopen.side_effect = error

        client = MoodMoApiClient(
            base_url="http://127.0.0.1:8000",
            token="bad-token",
        )
        with self.assertRaises(MoodMoApiError) as ctx:
            client.list_activities()

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(str(ctx.exception), "Authentication required")


if __name__ == "__main__":
    unittest.main()
