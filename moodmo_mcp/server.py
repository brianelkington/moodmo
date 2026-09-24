"""stdio MCP server exposing MoodMo's read-only API as tools."""

from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from moodmo_mcp.client import MoodMoApiClient, MoodMoApiError

INSTRUCTIONS = """\
Read-only access to a MoodMo instance via /api/v1/.

Mood scale: -2 very unhappy, -1 unhappy, 0 neutral, 1 happy, 2 very happy.
Mood activities are name strings (not nested objects with sqids).
Each mood has both `note_title` (short/quick note) and `note` (full body).
When logging or summarizing a mood, include both when present — do not drop the title.
Use optional `since` (ISO 8601) on list tools for incremental sync.
"""

mcp = MCPServer("MoodMo", instructions=INSTRUCTIONS)

_client: MoodMoApiClient | None = None


def get_client() -> MoodMoApiClient:
    global _client
    if _client is None:
        _client = MoodMoApiClient()
    return _client


def set_client(client: MoodMoApiClient | None) -> None:
    """Override the shared API client (used by tests)."""
    global _client
    _client = client


def _as_json(payload: Any) -> str:
    return json.dumps(payload, indent=2)


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True),
)
def list_moods(since: str | None = None) -> str:
    """List the authenticated user's moods, newest first.

    Mood values are integers: -2 very unhappy, -1 unhappy, 0 neutral,
    1 happy, 2 very happy. Each mood's `activities` field is a list of
    activity name strings. Each mood includes `note_title` and `note`;
    consumers must keep both when present.

    Args:
        since: Optional ISO 8601 datetime; only moods with
            last_modified >= since are returned.
    """
    try:
        return _as_json(get_client().list_moods(since=since))
    except MoodMoApiError as exc:
        return f"Error: {exc}"


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True),
)
def get_mood(sqid: str) -> str:
    """Fetch a single mood by its sqid.

    Mood values are integers: -2 very unhappy, -1 unhappy, 0 neutral,
    1 happy, 2 very happy. `activities` are name strings. Response includes
    both `note_title` and `note`; include both when presenting the entry.

    Args:
        sqid: Mood public id (Sqids slug, min length 8).
    """
    try:
        return _as_json(get_client().get_mood(sqid))
    except MoodMoApiError as exc:
        return f"Error: {exc}"


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True),
)
def list_activities(since: str | None = None) -> str:
    """List the authenticated user's activities.

    Args:
        since: Optional ISO 8601 datetime; only activities with
            last_modified >= since are returned.
    """
    try:
        return _as_json(get_client().list_activities(since=since))
    except MoodMoApiError as exc:
        return f"Error: {exc}"


def main() -> None:
    try:
        get_client()
    except MoodMoApiError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    mcp.run()


if __name__ == "__main__":
    main()
