# TreasuryOS on Replit

> Owner note to Agent: keep this file aligned with AGENTS.md. Don't remove sections without asking.

## Overview
MCP server (`server.py`) + Streamlit apps for small-business treasury and loan-readiness analysis.
Full agent guide: **AGENTS.md**. Financial guardrails: **CLAUDE.md**.

## Run targets
- **Default Run button:** business-owner app → `streamlit run smb_app.py --server.port 8501 --server.address 0.0.0.0`
- **RM dashboard:** `streamlit run rm_dashboard.py --server.port 8501 --server.address 0.0.0.0`
- **MCP server over HTTP (for remote agents):** `MCP_TRANSPORT=streamable-http PORT=8000 python server.py`
  → endpoint is `https://<your-repl-domain>/mcp`

## Dependencies
Python 3.11. Install with `pip install -r requirements.txt` (uv also works via `pyproject.toml`).
No secrets required.

## Architecture
- `tools/` — pure analysis functions reading CSVs from `TREASURY_DATA_DIR` (default `sample_data/`)
- `server.py` — wraps the tools as MCP tools
- `smb_app.py`, `rm_dashboard.py`, `app.py` — Streamlit front ends on the same engine

## Preferences
- Keep `tools/` side-effect free; give every MCP tool a clear docstring.
- Synthetic data only.
- Streamlit theme lives in `.streamlit/config.toml`; don't override it in code.
