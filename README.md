# Google My Business Manager

A Streamlit platform to monitor Google Business Profile (GBP) performance, analyze reviews, publish posts, and export reports.

Built for:
- Marketing agencies
- Local business owners
- Customer support and sales teams

## What you can do

- Track profile views and actions
- Analyze search keywords and trends
- Review customer feedback and generate AI reply suggestions (optional)
- Publish posts directly to GBP
- Upload image from your computer via Google Drive and attach it to the post
- Run profile health checks
- Export PDF reports

## Quick Start (5 minutes)

1. Open the app at `http://localhost:8501`.
2. Click **Login with Google**.
3. Authorize access to your Google Business Profile.
4. In the sidebar, choose a business in **Select Business**.
5. Choose a date range.
6. Click **Fetch Data**.
7. Use tabs: **Overview**, **Reviews**, **Posts**, **Health**, **Create Post**.

## Create Post with image from your computer

1. Open **Create Post**.
2. Set post details (type, language code, text, optional CTA).
3. In **Image Source**, choose **Upload from computer (Drive)**.
4. Select the image file.
5. Browse Drive folders and select where the file will be saved.
6. Click **Upload image to Drive**.
7. After URL is ready, click **Publish Now**.

## Security basics

- Never share `client_secret.json`.
- Never expose API keys in chat, email, or screenshots.
- Keep Drive/GBP access limited to required users.

## Technical Setup (Support)

### Requirements

- Python 3.10+
- Google OAuth credentials

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Credentials

Use `.env` as the default and recommended setup (based on `.env.example`):

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_AUTH_URI`
- `GOOGLE_TOKEN_URI`

Legacy/optional support is still available for:
- `client_secret.json` in project root
- `.streamlit/secrets.toml` with OAuth `web` object

Required scopes:
- `https://www.googleapis.com/auth/business.manage`
- `https://www.googleapis.com/auth/drive.file`
- `https://www.googleapis.com/auth/drive.metadata.readonly`

Optional AI key:

```bash
export GEMINI_API_KEY="your_key_here"
```

### Run

```bash
streamlit run app.py
```

Open: `http://localhost:8501`

## MCP server (Google Business Profile)

A thin MCP server exposes the same Google clients used by the Streamlit app (`data_fetcher.py`, `drive_helper.py`) as JSON tools. It does not import Streamlit, return DataFrames, or generate PDFs/Plotly charts.

Auth is user OAuth only (no service account). The Streamlit `auth.py` session/secrets flow is not used.

### Install and run

```bash
pip install -r requirements.txt
```

stdio (default — Cursor, Claude Desktop, Claude Code):

```bash
python mcp_server.py
# or: python -m src.gmb_mcp
```

Streamable HTTP:

```bash
python mcp_server.py --http --host 127.0.0.1 --port 8765
```

Endpoint: `http://127.0.0.1:8765/mcp`

### Connect from Cursor

Add to MCP settings (project or user). Do not put tokens in git.

```json
{
  "mcpServers": {
    "google-business-profile": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/absolute/path/to/this/repo",
      "env": {
        "GOOGLE_ACCESS_TOKEN": "<your-oauth-access-token>"
      }
    }
  }
}
```

For HTTP instead of stdio:

```json
{
  "mcpServers": {
    "google-business-profile": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

### Auth options (never commit these)

1. Pass `access_token` on any tool call.
2. Set `GOOGLE_ACCESS_TOKEN` (optional `GOOGLE_REFRESH_TOKEN` + `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` for refresh).
3. Local helper — opens a browser and writes a gitignored token file (default `.gmb-mcp-token.json`):

```bash
python mcp_server.py --oauth
```

Or use MCP tools `start_oauth` then `complete_oauth` with the `code` from the redirect URL. Token files and client secrets must stay out of git (`GMB_MCP_TOKEN_PATH` overrides the file path).

Redirect URI for the helper defaults to `http://localhost:8753/` unless `GOOGLE_REDIRECT_URI` is set. Add that URI in Google Cloud OAuth clients.

### Tools

Read: `list_accounts`, `list_locations`, `get_daily_metrics`, `get_search_keywords`, `list_reviews`, `list_posts`, `list_media`, `list_questions`, `profile_health_check`

Write: `create_local_post`, `upload_image_to_drive`, `reply_to_review`

Auth helpers: `start_oauth`, `complete_oauth`

Location IDs accept `accounts/{accountId}/locations/{locationId}`, `locations/{locationId}`, or a bare id. v4 calls reuse `resolve_location_parent`. Dates are `YYYY-MM-DD`. Drive uploads take base64 image bytes (`file_base64`) and return a public URL.

## Development

Install dev tools:

```bash
pip install -r requirements-dev.txt
```

Run checks:

```bash
ruff check src tests app.py auth.py mcp_server.py
pytest
python -m py_compile app.py auth.py data_fetcher.py drive_helper.py mcp_server.py
```

Utility/debug scripts are in `tools/`.

## Portuguese Documentation

See [README-ptbr.md](README-ptbr.md).

## License

MIT (see `LICENSE`).
