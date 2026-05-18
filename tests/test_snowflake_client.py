from __future__ import annotations

import pytest

from airlock_mcp.snowflake_client import build_call_sql


def test_build_call_sql_with_arguments() -> None:
    assert build_call_sql("airlock.user.describe_spec", 2) == "CALL airlock.user.describe_spec(%s, %s)"


def test_build_call_sql_respects_application_name() -> None:
    assert (
        build_call_sql("airlock.user.describe_spec", 2, "AIRLOCK_LEO")
        == "CALL AIRLOCK_LEO.user.describe_spec(%s, %s)"
    )


def test_build_call_sql_without_arguments() -> None:
    assert build_call_sql("airlock.user.list_my_roles", 0) == "CALL airlock.user.list_my_roles()"


def test_build_call_sql_rejects_unknown_schema() -> None:
    with pytest.raises(ValueError):
        build_call_sql("airlock.core.file_manifest", 0)


def test_build_call_sql_rejects_injection_shape() -> None:
    with pytest.raises(ValueError):
        build_call_sql("airlock.user.list_my_roles; SELECT 1", 0)


def test_build_call_sql_rejects_unsafe_application_name() -> None:
    with pytest.raises(ValueError):
        build_call_sql("airlock.user.list_my_roles", 0, "AIRLOCK; DROP DATABASE AIRLOCK")
