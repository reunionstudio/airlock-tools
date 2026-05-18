# Snowflake CLI for Airlock Drift Checks

Use Snowflake CLI when MCP is not configured yet or when you need a direct
snapshot of installed Airlock documentation. Treat Snowflake CLI as a transport
for stored procedure calls. Do not use it to bypass Airlock procedures.

## Install

Install Snowflake CLI using Snowflake's current installation docs. Confirm:

```bash
snow --version
snow --help
```

## Add a Connection

Interactive setup:

```bash
snow connection add
```

Named setup, when the values are already known:

```bash
snow connection add \
  --connection-name airlock-dev \
  --account "<account>" \
  --user "<user>" \
  --role "<snowflake_role_with_airlock_app_access>" \
  --warehouse "<warehouse>" \
  --database "<airlock_application_name>"
```

Prefer key-pair, SSO, OAuth, or workload identity when account policy requires
them. Avoid committing `config.toml`, private keys, passwords, tokens, or
temporary credentials.

Test and select the connection:

```bash
snow connection test -c airlock-dev
snow connection set-default airlock-dev
snow connection list
```

## Airlock Context Queries

Confirm Snowflake context:

```bash
snow sql -c airlock-dev -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_WAREHOUSE();"
```

Fetch installed Airlock documentation and registry:

```bash
snow sql -c airlock-dev -q "CALL airlock.user.documentation();"
snow sql -c airlock-dev -q "CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');"
snow sql -c airlock-dev -q "CALL airlock.user.documentation(CONTENT_MODE => 'FULL');"
```

Fetch role/spec context:

```bash
snow sql -c airlock-dev -q "CALL airlock.user.list_my_roles();"
snow sql -c airlock-dev -q "CALL airlock.user.list_my_specs('<airlock_role>');"
snow sql -c airlock-dev -q "CALL airlock.user.describe_spec('<spec_name>', '<airlock_role>');"
```

Admin-only registry check:

```bash
snow sql -c airlock-dev -q "CALL airlock.admin.api_info();"
```

Native App install and ownership checks:

```bash
snow sql -c airlock-dev -q "SHOW PRIVILEGES IN APPLICATION AIRLOCK;"
snow sql -c airlock-dev -q "SHOW OBJECTS OWNED BY APPLICATION AIRLOCK;"
```

Grant Airlock's requested storage-database privilege only after the consumer has
reviewed it:

```bash
snow sql -c airlock-dev -q "GRANT CREATE DATABASE ON ACCOUNT TO APPLICATION AIRLOCK;"
```

## Safer Script Files

For repeatable drift checks, put non-secret SQL in a file and run:

```bash
snow sql -c airlock-dev -f airlock_api_snapshot.sql
```

Example `airlock_api_snapshot.sql`:

```sql
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_WAREHOUSE();
CALL airlock.user.documentation();
CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
CALL airlock.user.list_my_roles();
```

Keep snapshots out of public commits if they contain customer spec names,
filenames, user names, or other tenant-specific information.

## What to Compare

Compare Snowflake CLI results against:

- MCP tool names, arguments, and procedure calls in `src/airlock_mcp/server.py`.
- Normalization behavior in `src/airlock_mcp/normalize.py`.
- Airlock CoCo skill guidance in `.cortex/skills/airlock/`.
- Public docs in `README.md` and `docs/`.
- Unit and integration tests.

If the installed registry has a new user-safe procedure that maps to a primary
agent workflow, propose an MCP tool and a skill example. If a signature changes,
treat it as a breaking risk until tested.
