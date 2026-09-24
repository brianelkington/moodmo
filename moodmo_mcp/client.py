"""HTTP client for the MoodMo `/api/v1/` endpoints."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class MoodMoApiError(Exception):
    """Raised when the MoodMo API returns an error or cannot be reached."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MoodMoApiClient:
    """Thin Bearer-token client for MoodMo's read-only JSON API."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("MOODMO_API_BASE_URL", "")).rstrip(
            "/"
        )
        self.token = token or os.environ.get("MOODMO_API_TOKEN", "")
        self.timeout = timeout

        if not self.base_url:
            raise MoodMoApiError(
                "MOODMO_API_BASE_URL is required (e.g. http://127.0.0.1:8000)."
            )
        if not self.token:
            raise MoodMoApiError("MOODMO_API_TOKEN is required.")

    def list_moods(self, since: str | None = None) -> dict[str, Any]:
        return self._get("/api/v1/moods/", {"since": since} if since else None)

    def get_mood(self, sqid: str) -> dict[str, Any]:
        return self._get(f"/api/v1/moods/{sqid}/")

    def list_activities(self, since: str | None = None) -> dict[str, Any]:
        return self._get("/api/v1/activities/", {"since": since} if since else None)

    def _get(
        self,
        path: str,
        params: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        if params:
            cleaned = {key: value for key, value in params.items() if value}
            if cleaned:
                url = f"{url}?{urlencode(cleaned)}"

        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            detail = self._error_detail(exc)
            raise MoodMoApiError(detail, status_code=exc.code) from exc
        except URLError as exc:
            raise MoodMoApiError(f"Could not reach MoodMo API: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise MoodMoApiError("MoodMo API returned invalid JSON.") from exc

    @staticmethod
    def _error_detail(exc: HTTPError) -> str:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return f"MoodMo API error ({exc.code})."

        if isinstance(payload, dict) and "error" in payload:
            return str(payload["error"])
        return f"MoodMo API error ({exc.code})."
