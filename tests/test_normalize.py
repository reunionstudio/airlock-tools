from __future__ import annotations

from airlock_mcp.normalize import (
    blocked_result,
    exception_result,
    normalize_airlock_result,
    sanitize_error_message,
)


def test_normalize_success_preserves_rows_and_payload() -> None:
    result = normalize_airlock_result(
        "airlock.user.load_data",
        [
            {
                "SPEC_NAME": "invoices",
                "STATUS": "ok",
                "MESSAGE": "Loaded file.",
                "ISSUES": [],
                "ROW_COUNT": 2,
            }
        ],
        duration_ms=12,
    )

    assert result["ok"] is True
    assert result["status"] == "ok"
    assert result["message"] == "Loaded file."
    assert result["issues"] == []
    assert result["rows"][0]["SPEC_NAME"] == "invoices"
    assert result["duration_ms"] == 12


def test_normalize_error_extracts_code_from_issues() -> None:
    result = normalize_airlock_result(
        "airlock.user.load_data",
        [
            {
                "STATUS": "error",
                "MESSAGE": "Attachment required for spec \"invoices\".",
                "ISSUES": [
                    {
                        "code": "ATTACHMENT_REQUIRED",
                        "message": "Add one receipt attachment.",
                        "severity": "error",
                    }
                ],
            }
        ],
    )

    assert result["ok"] is False
    assert result["code"] == "ATTACHMENT_REQUIRED"
    assert result["issues"][0]["code"] == "ATTACHMENT_REQUIRED"


def test_normalize_parses_variant_issue_json_strings() -> None:
    result = normalize_airlock_result(
        "airlock.user.validate_data",
        [
            {
                "STATUS": "ok",
                "ISSUES": "[]",
                "VALIDATION": '{"issues": []}',
            }
        ],
    )

    assert result["ok"] is True
    assert result["issues"] == []


def test_blocked_result_is_structured() -> None:
    result = blocked_result("airlock.user.delete_files", "CONFIRMATION_REQUIRED", "Set confirm=true.")

    assert result == {
        "ok": False,
        "procedure": "airlock.user.delete_files",
        "status": "blocked",
        "code": "CONFIRMATION_REQUIRED",
        "message": "Set confirm=true.",
        "payload": {},
        "issues": [
            {
                "code": "CONFIRMATION_REQUIRED",
                "message": "Set confirm=true.",
                "severity": "error",
            }
        ],
        "rows": [],
    }


def test_exception_result_sanitizes_secret_like_values() -> None:
    result = exception_result(
        "airlock.user.list_my_roles",
        RuntimeError("connection failed password=example-secret\nstack line"),
    )

    assert result["ok"] is False
    assert result["code"] == "SNOWFLAKE_PROCEDURE_ERROR"
    assert "example-secret" not in result["payload"]["safe_detail"]
    assert "stack line" in result["payload"]["safe_detail"]


def test_exception_result_sanitizes_private_key_paths() -> None:
    result = exception_result(
        "airlock.user.list_my_roles",
        FileNotFoundError("[Errno 2] No such file or directory: '/Users/alice/.keys/airlock_agent.p8'"),
    )

    assert "airlock_agent.p8" not in result["payload"]["safe_detail"]
    assert "<redacted-private-key-path>" in result["payload"]["safe_detail"]


def test_sanitize_truncates() -> None:
    assert len(sanitize_error_message("x" * 2000)) == 1000
