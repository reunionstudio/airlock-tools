# Airlock Tools Recurring Tasks

## Start here

For future `@improve` runs:

1. Treat `/Users/ao/proj/reunionstudio/airlock` as the upstream source of truth.
2. Check upstream shared docs for inbound drift:
   - `docs/airlock-tools.md`
   - `docs/agent_delegation.md`
   - `docs/airlock_mcp_server_guide.md`
   - `docs/airlock_cortex_code_skill_guide.md`
   - `docs/mcp_and_stored_procedures.md`
3. Verify exact procedure names and signatures against upstream procedure
   wrappers or installed documentation before changing MCP tool behavior.
4. Run focused checks when quick:
   ```bash
   uv run --extra dev ruff check .
   uv run --extra dev pytest
   git diff --check
   ```
5. Update `cleanup.md` with completed sync results and concrete follow-ups.

## Tracked variables

- `last_improve_dependency_sync_at`: `2026-05-18`
- `last_improve_cleanup_pass_at`: `null`
- `last_improve_coverage_pass_at`: `null`

## Checklist

- Inbound Airlock dependency sync
- MCP tool/procedure drift
- CoCo skill and examples drift
- Docs and release notes drift
- Focused tests
