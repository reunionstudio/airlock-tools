from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .config import AirlockConfig

PROCEDURE_RE = re.compile(r"^airlock\.(user|admin)\.[a-z][a-z0-9_]*$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def build_call_sql(
    procedure: str,
    argument_count: int,
    application_name: str | None = None,
) -> str:
    match = PROCEDURE_RE.fullmatch(procedure)
    if not match:
        raise ValueError(f"Unsupported procedure name: {procedure}")
    if argument_count < 0:
        raise ValueError("argument_count must be non-negative")
    schema_name = match.group(1)
    procedure_name = procedure.rsplit(".", 1)[1]
    database_name = application_name or "airlock"
    if not IDENTIFIER_RE.fullmatch(database_name):
        raise ValueError(f"Unsupported Airlock application name: {database_name}")
    procedure_target = f"{database_name}.{schema_name}.{procedure_name}"
    placeholders = ", ".join(["%s"] * argument_count)
    return f"CALL {procedure_target}({placeholders})"


class SnowflakeAirlockClient:
    def __init__(self, config: AirlockConfig):
        self.config = config

    def call_procedure(self, procedure: str, args: Sequence[Any] = ()) -> list[Mapping[str, Any]]:
        snowflake = _snowflake_connector()
        sql = build_call_sql(procedure, len(args), self.config.application_name)
        conn = snowflake.connect(**self.config.connection_parameters())
        try:
            cursor = conn.cursor(snowflake.DictCursor)
            try:
                cursor.execute(sql, list(args))
                return list(cursor.fetchall())
            finally:
                cursor.close()
        finally:
            conn.close()

    def session_context(self) -> dict[str, Any]:
        snowflake = _snowflake_connector()
        conn = snowflake.connect(**self.config.connection_parameters())
        try:
            cursor = conn.cursor(snowflake.DictCursor)
            try:
                cursor.execute(
                    "SELECT CURRENT_USER() AS CURRENT_USER, "
                    "CURRENT_ROLE() AS ACTIVE_SNOWFLAKE_ROLE, "
                    "CURRENT_DATABASE() AS CURRENT_DATABASE, "
                    "CURRENT_WAREHOUSE() AS CURRENT_WAREHOUSE"
                )
                row = cursor.fetchone() or {}
            finally:
                cursor.close()
        finally:
            conn.close()

        return {
            "current_user": row.get("CURRENT_USER"),
            "active_snowflake_role": row.get("ACTIVE_SNOWFLAKE_ROLE"),
            "current_database": row.get("CURRENT_DATABASE"),
            "current_warehouse": row.get("CURRENT_WAREHOUSE"),
            "application_name": self.config.application_name,
            "admin_tools_enabled": self.config.admin_tools_enabled,
            "default_airlock_role": self.config.default_airlock_role,
        }


def _snowflake_connector() -> Any:
    try:
        import snowflake.connector
    except ImportError as exc:  # pragma: no cover - exercised only without dependency installed
        raise RuntimeError(
            "snowflake-connector-python is required. Install with `pip install airlock-mcp`."
        ) from exc
    return snowflake.connector
