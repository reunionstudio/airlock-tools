from __future__ import annotations

import datetime as dt
import decimal
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

ERROR_STATUSES = {"error", "failed", "failure", "blocked", "denied", "not_found"}
SECRET_PATTERNS = [
    (re.compile(r"(AIRLOCK_PRIVATE_KEY_PATH=)[^\s]+", re.IGNORECASE), r"\1<redacted>"),
    (re.compile(r"(AIRLOCK_PRIVATE_KEY_PASSPHRASE=)[^\s]+", re.IGNORECASE), r"\1<redacted>"),
    (re.compile(r"(password=)[^\s,;]+", re.IGNORECASE), r"\1<redacted>"),
    (re.compile(r"(passphrase=)[^\s,;]+", re.IGNORECASE), r"\1<redacted>"),
    (re.compile(r"(['\"])[^'\"]*\.(?:p8|pem|key)\1", re.IGNORECASE), r"\1<redacted-private-key-path>\1"),
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "<redacted-private-key>",
    ),
]


def json_compatible(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, decimal.Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, dt.datetime | dt.date | dt.time):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): json_compatible(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [json_compatible(v) for v in value]
    if isinstance(value, bytes | bytearray):
        return f"<{len(value)} bytes>"
    return str(value)


def normalize_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append({str(key).upper(): json_compatible(value) for key, value in row.items()})
    return normalized


def normalize_airlock_result(
    procedure: str,
    rows: Sequence[Mapping[str, Any]],
    duration_ms: int | None = None,
) -> dict[str, Any]:
    normalized_rows = normalize_rows(rows)
    first = normalized_rows[0] if normalized_rows else {}

    status = _first_scalar(normalized_rows, "STATUS")
    status_text = str(status).lower() if status is not None else "ok"
    code = _first_scalar(normalized_rows, "CODE")
    message = _first_scalar(normalized_rows, "MESSAGE")
    issues = _collect_issues(normalized_rows)

    has_error_issue = any(str(issue.get("severity", "")).lower() == "error" for issue in issues)
    ok = status_text not in ERROR_STATUSES and not has_error_issue

    if code is None and not ok:
        code = _first_issue_code(issues) or status_text.upper()

    payload: dict[str, Any] | Any = {}
    if len(normalized_rows) == 1 and set(first) == {"PAYLOAD"}:
        payload = first["PAYLOAD"]
    elif "PAYLOAD" in first:
        payload = first["PAYLOAD"]

    result: dict[str, Any] = {
        "ok": ok,
        "procedure": procedure,
        "status": status_text,
        "code": code,
        "message": message or _default_message(procedure, ok, len(normalized_rows)),
        "payload": payload,
        "issues": issues,
        "rows": normalized_rows,
    }
    if duration_ms is not None:
        result["duration_ms"] = duration_ms
    return result


def blocked_result(
    procedure: str,
    code: str,
    message: str,
    issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "procedure": procedure,
        "status": "blocked",
        "code": code,
        "message": message,
        "payload": {},
        "issues": issues
        or [{"code": code, "message": message, "severity": "error"}],
        "rows": [],
    }


def exception_result(procedure: str, error: BaseException) -> dict[str, Any]:
    message = sanitize_error_message(str(error))
    if not message:
        message = "Snowflake procedure call failed."
    return {
        "ok": False,
        "procedure": procedure,
        "status": "error",
        "code": "SNOWFLAKE_PROCEDURE_ERROR",
        "message": f"Snowflake call failed for {procedure}.",
        "payload": {
            "error_type": error.__class__.__name__,
            "safe_detail": message,
        },
        "issues": [
            {
                "code": "SNOWFLAKE_PROCEDURE_ERROR",
                "message": message,
                "severity": "error",
            }
        ],
        "rows": [],
    }


def sanitize_error_message(message: str) -> str:
    text = " ".join(message.split())
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text[:1000]


def _first_scalar(rows: list[dict[str, Any]], key: str) -> Any:
    for row in rows:
        value = row.get(key)
        if value is not None:
            return value
    return None


def _collect_issues(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for row in rows:
        collected.extend(_coerce_issues(row.get("ISSUES")))
        validation = _parse_json_variant(row.get("VALIDATION"))
        if isinstance(validation, Mapping):
            collected.extend(_coerce_issues(validation.get("issues")))
    return collected


def _coerce_issues(value: Any) -> list[dict[str, Any]]:
    value = _parse_json_variant(value)
    if value is None or value == "":
        return []
    if isinstance(value, Mapping):
        if "issues" in value:
            return _coerce_issues(value["issues"])
        return [json_compatible(value)]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        issues: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                issues.append(json_compatible(item))
            else:
                issues.append({"code": "ISSUE", "message": str(item), "severity": "error"})
        return issues
    return [{"code": "ISSUE", "message": str(value), "severity": "error"}]


def _parse_json_variant(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{":
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def _first_issue_code(issues: list[dict[str, Any]]) -> str | None:
    for issue in issues:
        code = issue.get("code")
        if code:
            return str(code)
    return None


def _default_message(procedure: str, ok: bool, row_count: int) -> str:
    if ok:
        return f"{procedure} returned {row_count} row(s)."
    return f"{procedure} returned an error."
