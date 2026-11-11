# Copilot instructions

Follow [AGENTS.md](../AGENTS.md) at the repo root — it covers setup, run commands, the 9 MCP tools,
data format, and coding conventions. Financial and credit guardrails are in [CLAUDE.md](../CLAUDE.md).

Key rules:
- `tools/` functions stay pure and side-effect free.
- Every MCP tool in `server.py` needs a clear docstring; MCP clients show it to models.
- All data is synthetic. Never add real customer data.
