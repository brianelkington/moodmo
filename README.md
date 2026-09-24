<div align="center">

  # MoodMo - Self-Hosted Mood Tracking App  

MoodMo is a self-hosted mood tracking and journal application built with privacy in mind, while also prioritizing speed and an user-friendly interface.  

![Screenshot of the Home page of MoodMo](https://github.com/dnlzrgz/moodmo/raw/master/static/images/screenshot.png)
</div>

## Motivation

MoodMo it's the result of my personal longing for a mood tracking and journal application that I could use in every device I wanted without worries about the privacy or security of my data, and one that I could deploy and manage easily, whether on a local device such a Raspberry Pi or through a cloud provider like Railway.  

## Features

- Responsive and modern interface powered by [Tailwind CSS](https://tailwindcss.com/).
- Dynamic user interaction with minimal JavaScript usage thanks to `htmx` and `Alpine.js`.
- Easy to deploy thanks to Docker.
- Simple setup process.
- Flexible configuration through `env` variables.
- Robust authentication provided by `django-allauth`.
- Full-text search functionality.
- Support for caching with `Redis` and `memcached`.
- Data export and import in CSV and JSON formats.
- Optional [Model Context Protocol](https://modelcontextprotocol.io/) server for read-only API access from Cursor and other MCP hosts.

## Deployment

<!-- TODO: Update this section -->
## Development
<!-- TODO: Update this section -->

## MCP server

MoodMo ships a read-only stdio MCP wrapper around `/api/v1/` (list moods, get mood, list activities). It talks to a running MoodMo instance over HTTP using a Bearer API token.

### 1. Create an API token

Use the same environment that runs MoodMo (Poetry venv or Docker). Plain system `python` will fail with `No module named 'django'`.

With Poetry (Python 3.12):

```bash
poetry install
poetry run python manage.py create_api_token --email you@example.com --name "MCP"
```

With Docker Compose (dev stack):

```bash
docker compose -f dev.yaml exec django python manage.py create_api_token --email you@example.com --name "MCP"
```

Store the printed token securely; it is shown only once.

### 2. Install the optional MCP extra

```bash
poetry install --extras mcp
```

### 3. Configure Cursor (or another MCP host)

Do not commit a live `mcp.json` with a real token. Add a local MCP server entry like:

```json
{
  "mcpServers": {
    "moodmo": {
      "command": "poetry",
      "args": ["run", "moodmo-mcp"],
      "cwd": "R:/MoodMo",
      "env": {
        "MOODMO_API_BASE_URL": "http://127.0.0.1:8000",
        "MOODMO_API_TOKEN": "<token>"
      }
    }
  }
}
```

Environment variables:

| Variable | Description |
|----------|-------------|
| `MOODMO_API_BASE_URL` | Base URL of the MoodMo instance (no trailing slash required) |
| `MOODMO_API_TOKEN` | Raw API token from `create_api_token` |

You can also run the server with `python -m moodmo_mcp` when those variables are set.

### Tools

| Tool | API call |
|------|----------|
| `list_moods` | `GET /api/v1/moods/` (optional `since`) |
| `get_mood` | `GET /api/v1/moods/{sqid}/` |
| `list_activities` | `GET /api/v1/activities/` (optional `since`) |

Mood values are integers: `-2` very unhappy, `-1` unhappy, `0` neutral, `1` happy, `2` very happy. Mood `activities` are name strings. Each mood includes both `note_title` (quick/short note) and `note` (full body); keep both when presenting or syncing an entry.

## Roadmap

- [ ] Statistics.
- [ ] Search.
- [ ] Dark mode.
- [ ] Weather integration.
- [ ] Location.
- [ ] Journaling.

## Help Not Wanted but Attention Is Appreciated

At the moment I'm not seeking external contributions through pull requests nor I would accept them, but your attention and feedback are highly appreciated. If you encounter any issues, have suggestions for improvements or just want to share your thoughts on MoodMo, feel free to open an issue!
