# API Drift Review

Use this example when asked whether an Airlock app upgrade means this repo must
change.

## Inputs

- Snowflake connection name.
- Airlock application/database name.
- Airlock API `content_hash` or `etag`, if already known.
- Installed documentation rows or permission to query them.

## Steps

1. Capture installed context:
   ```bash
   snow sql -c <connection> -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_WAREHOUSE();"
   snow sql -c <connection> -q "CALL airlock.user.documentation();"
   snow sql -c <connection> -q "CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');"
   ```
2. Compare the installed procedure registry to MCP calls in
   `src/airlock_mcp/server.py`.
3. Check whether any changed procedure affects:
   - discovery
   - role/license checks
   - spec listing/description
   - validate/load
   - list/select/delete files
   - workflow
   - attachments
   - references
   - expectations
   - admin mode
4. Check docs and skill guidance for stale procedure names, arguments, safety
   wording, or examples.
5. Run:
   ```bash
   uv run --extra dev pytest
   uv run --extra dev ruff check .
   ```

## Report Format

```text
Findings
P1: airlock.user.load_data added required argument "x"; update server.py and tests.
P2: documentation now recommends new path_scope wording; update CoCo skill example.

Reviewed
- Airlock documentation etag: <etag>
- Snowflake role: <role>
- Airlock roles observed: <roles>
- Tests: <results>
```
