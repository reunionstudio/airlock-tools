from __future__ import annotations

import json
import logging
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import AirlockConfig
from .normalize import blocked_result, exception_result, normalize_airlock_result
from .snowflake_client import SnowflakeAirlockClient

LOGGER = logging.getLogger("airlock_mcp")

CONFIG = AirlockConfig.from_env()
CLIENT = SnowflakeAirlockClient(CONFIG)
mcp = FastMCP("Airlock MCP")


def _call(procedure: str, args: list[Any] | None = None) -> dict[str, Any]:
    args = args or []
    started = time.perf_counter()
    try:
        rows = CLIENT.call_procedure(procedure, args)
        duration_ms = int((time.perf_counter() - started) * 1000)
        result = normalize_airlock_result(procedure, rows, duration_ms=duration_ms)
        LOGGER.info(
            "procedure=%s status=%s code=%s duration_ms=%s",
            procedure,
            result["status"],
            result["code"],
            duration_ms,
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result = exception_result(procedure, exc)
        LOGGER.warning("procedure=%s status=error code=%s", procedure, result["code"])
        return result


def _resource_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)


def _validate_one_content_source(procedure: str, path: str | None, file_content: str | None) -> dict[str, Any] | None:
    has_path = bool(path)
    has_content = bool(file_content)
    if has_path == has_content:
        return blocked_result(
            procedure,
            "INVALID_CONTENT_SOURCE",
            "Provide exactly one of path or file_content.",
        )
    return None


def _validate_inline_size(procedure: str, field_name: str, value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    size = len(value.encode("utf-8"))
    if size > CONFIG.max_inline_bytes:
        return blocked_result(
            procedure,
            "INLINE_PAYLOAD_TOO_LARGE",
            f"{field_name} exceeds AIRLOCK_MCP_MAX_INLINE_BYTES.",
            [
                {
                    "code": "INLINE_PAYLOAD_TOO_LARGE",
                    "message": f"{field_name} is {size} bytes; limit is {CONFIG.max_inline_bytes} bytes.",
                    "severity": "error",
                }
            ],
        )
    return None


def _source_files_arg(source_files: str | list[str]) -> str:
    if isinstance(source_files, list):
        return json.dumps(source_files)
    return source_files


@mcp.tool()
def airlock_get_connection_context() -> dict[str, Any]:
    """Return Snowflake session context and Airlock MCP configuration facts."""
    procedure = "snowflake.session_context"
    try:
        return {
            "ok": True,
            "procedure": procedure,
            "status": "ok",
            "code": None,
            "message": "Resolved Snowflake session context.",
            "payload": CLIENT.session_context(),
            "issues": [],
            "rows": [],
        }
    except Exception as exc:  # noqa: BLE001
        return exception_result(procedure, exc)


@mcp.tool()
def airlock_get_api_info(admin: bool = False) -> dict[str, Any]:
    """Discover installed Airlock procedure availability.

    In user mode this calls the structured documentation procedure registry.
    Admin `api_info` is only called when AIRLOCK_MCP_ADMIN_TOOLS=1 and
    admin=true.
    """
    if admin:
        if not CONFIG.admin_tools_enabled:
            return blocked_result(
                "airlock.admin.api_info",
                "ADMIN_TOOLS_DISABLED",
                "Admin tools are disabled.",
            )
        return _call("airlock.admin.api_info")
    return _call("airlock.user.documentation", ["markdown", "api_v1", "PROCEDURES", None])


@mcp.tool()
def airlock_get_documentation(
    content_mode: str = "TOC",
    section_ids: str | None = None,
    output_format: str = "markdown",
    doc_key: str = "api_v1",
) -> dict[str, Any]:
    """Fetch installed Airlock documentation as structured procedure output."""
    return _call("airlock.user.documentation", [output_format, doc_key, content_mode, section_ids])


@mcp.tool()
def airlock_list_my_roles() -> dict[str, Any]:
    """List Airlock business roles for the current Snowflake user."""
    return _call("airlock.user.list_my_roles")


@mcp.tool()
def airlock_check_license(claim: bool = False) -> dict[str, Any]:
    """Read the caller's Airlock license seat, or claim one when claim=true."""
    if claim:
        return _call("airlock.user.claim_license_seat")
    return _call("airlock.user.get_my_license_seat")


@mcp.tool()
def airlock_list_specs(
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """List specs under an Airlock role lens; include managed child roles by default."""
    return _call("airlock.user.list_my_specs", [in_app_role, include_managed_roles])


@mcp.tool()
def airlock_describe_spec(
    spec_name: str,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """Describe a spec through an Airlock role lens, including fields, rules, paths, and attachments."""
    return _call("airlock.user.describe_spec", [spec_name, in_app_role, include_managed_roles])


@mcp.tool()
def airlock_select_reference_data(
    spec_name: str,
    object_key: str,
    row_limit: int = 500,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
    row_offset: int = 0,
    record_reference_read_event: bool = True,
) -> dict[str, Any]:
    """Read governed rows from a reference spec through Airlock authorization."""
    return _call(
        "airlock.user.select_reference_data",
        [
            spec_name,
            object_key,
            row_limit,
            in_app_role,
            include_managed_roles,
            row_offset,
            record_reference_read_event,
        ],
    )


@mcp.tool()
def airlock_validate_data(
    spec_name: str,
    path: str | None = None,
    file_content: str | None = None,
    in_app_role: str | None = None,
    path_scope: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """Validate candidate data through Airlock without writing a file."""
    procedure = "airlock.user.validate_data"
    blocked = _validate_one_content_source(procedure, path, file_content)
    if blocked:
        return blocked
    blocked = _validate_inline_size(procedure, "file_content", file_content)
    if blocked:
        return blocked
    return _call(
        procedure,
        [spec_name, path, file_content, in_app_role, path_scope, include_managed_roles],
    )


@mcp.tool()
def airlock_load_data(
    spec_name: str,
    path: str | None = None,
    file_content: str | None = None,
    filename: str | None = None,
    in_app_role: str | None = None,
    path_scope: str | None = None,
    attachment_content_base64: str | None = None,
    attachment_filename: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """Load data through Airlock, optionally registering one attachment in the same call."""
    procedure = "airlock.user.load_data"
    blocked = _validate_one_content_source(procedure, path, file_content)
    if blocked:
        return blocked
    for field_name, value in (
        ("file_content", file_content),
        ("attachment_content_base64", attachment_content_base64),
    ):
        blocked = _validate_inline_size(procedure, field_name, value)
        if blocked:
            return blocked
    return _call(
        procedure,
        [
            spec_name,
            path,
            file_content,
            filename,
            in_app_role,
            path_scope,
            attachment_content_base64,
            attachment_filename,
            include_managed_roles,
        ],
    )


@mcp.tool()
def airlock_list_files(
    spec_name: str,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """List files in a spec that the caller may see."""
    return _call("airlock.user.list_my_files", [spec_name, in_app_role, include_managed_roles])


@mcp.tool()
def airlock_select_files(
    spec_name: str,
    search_string: str | None = None,
    regex_pattern: str | None = None,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """Read accessible file data through Airlock checks."""
    return _call(
        "airlock.user.select_my_files",
        [spec_name, search_string, regex_pattern, in_app_role, include_managed_roles],
    )


@mcp.tool()
def airlock_delete_files(
    spec_name: str,
    source_files: str | list[str],
    source_directory: str | None = None,
    in_app_role: str | None = None,
    dry_run: bool = True,
    include_managed_roles: bool = True,
    confirm: bool = False,
) -> dict[str, Any]:
    """Preview or delete files through Airlock.

    The default is non-mutating. Set dry_run=false and confirm=true to perform
    deletion.
    """
    procedure = "airlock.user.delete_files"
    if not dry_run and not confirm:
        return blocked_result(
            procedure,
            "CONFIRMATION_REQUIRED",
            "Set confirm=true when dry_run=false.",
        )
    return _call(
        procedure,
        [
            spec_name,
            _source_files_arg(source_files),
            source_directory,
            in_app_role,
            dry_run,
            include_managed_roles,
        ],
    )


@mcp.tool()
def airlock_list_work_items(
    spec_name: str | None = None,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """List workflow work items visible to the caller."""
    return _call("airlock.user.list_my_work_items", [spec_name, in_app_role, include_managed_roles])


@mcp.tool()
def airlock_list_expectation_work(
    spec_name: str | None = None,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """List expectation status and required follow-up visible to the caller."""
    return _call(
        "airlock.user.list_my_expectation_work",
        [spec_name, in_app_role, include_managed_roles],
    )


@mcp.tool()
def airlock_edit_file_workflow(
    spec_name: str,
    path: str,
    filename: str,
    action: str,
    comment: str | None = None,
    validate_only: bool = True,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
) -> dict[str, Any]:
    """Validate or apply a workflow transition for a file.

    Defaults to validate_only=true. Set validate_only=false to move the file.
    """
    return _call(
        "airlock.user.edit_file_workflow",
        [
            spec_name,
            path,
            filename,
            action,
            comment,
            validate_only,
            in_app_role,
            include_managed_roles,
        ],
    )


@mcp.tool()
def airlock_add_attachment(
    spec_name: str,
    file_path: str,
    file_filename: str,
    attachment_stage_path: str | None = None,
    attachment_content_base64: str | None = None,
    attachment_filename: str | None = None,
    attachment_type: str = "other",
    description: str | None = None,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
    attachment_tag: str | None = None,
) -> dict[str, Any]:
    """Add an attachment to an existing file through Airlock checks."""
    procedure = "airlock.user.add_attachment"
    if bool(attachment_stage_path) == bool(attachment_content_base64):
        return blocked_result(
            procedure,
            "INVALID_ATTACHMENT_SOURCE",
            "Provide exactly one of attachment_stage_path or attachment_content_base64.",
        )
    blocked = _validate_inline_size(procedure, "attachment_content_base64", attachment_content_base64)
    if blocked:
        return blocked
    return _call(
        procedure,
        [
            spec_name,
            file_path,
            file_filename,
            attachment_stage_path,
            attachment_content_base64,
            attachment_filename,
            attachment_type,
            description,
            in_app_role,
            include_managed_roles,
            attachment_tag,
        ],
    )


@mcp.tool()
def airlock_replace_attachment(
    spec_name: str,
    file_path: str,
    file_filename: str,
    attachment_id: str,
    attachment_stage_path: str | None = None,
    attachment_content_base64: str | None = None,
    attachment_filename: str | None = None,
    attachment_type: str = "other",
    description: str | None = None,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
    attachment_tag: str | None = None,
) -> dict[str, Any]:
    """Replace an existing attachment. This is permanent unless Airlock adds restore support."""
    procedure = "airlock.user.replace_attachment"
    if bool(attachment_stage_path) == bool(attachment_content_base64):
        return blocked_result(
            procedure,
            "INVALID_ATTACHMENT_SOURCE",
            "Provide exactly one of attachment_stage_path or attachment_content_base64.",
        )
    blocked = _validate_inline_size(procedure, "attachment_content_base64", attachment_content_base64)
    if blocked:
        return blocked
    return _call(
        procedure,
        [
            spec_name,
            file_path,
            file_filename,
            attachment_id,
            attachment_stage_path,
            attachment_content_base64,
            attachment_filename,
            attachment_type,
            description,
            in_app_role,
            include_managed_roles,
            attachment_tag,
        ],
    )


@mcp.tool()
def airlock_delete_attachment(
    spec_name: str,
    file_path: str,
    file_filename: str,
    attachment_id: str,
    in_app_role: str | None = None,
    include_managed_roles: bool = True,
    confirm: bool = False,
) -> dict[str, Any]:
    """Delete an attachment. Requires confirm=true because attachment delete is permanent."""
    procedure = "airlock.user.delete_attachment"
    if not confirm:
        return blocked_result(
            procedure,
            "CONFIRMATION_REQUIRED",
            "Set confirm=true to delete the attachment.",
        )
    return _call(
        procedure,
        [spec_name, file_path, file_filename, attachment_id, in_app_role, include_managed_roles],
    )


@mcp.resource("airlock://documentation/toc")
def documentation_toc() -> str:
    """Installed Airlock documentation table of contents."""
    return _resource_json(_call("airlock.user.documentation", ["markdown", "api_v1", "TOC", None]))


@mcp.resource("airlock://documentation/procedures")
def documentation_procedures() -> str:
    """Installed Airlock structured procedure registry."""
    return _resource_json(_call("airlock.user.documentation", ["markdown", "api_v1", "PROCEDURES", None]))


@mcp.resource("airlock://specs/{spec_name}/descriptor")
def spec_descriptor(spec_name: str) -> str:
    """Descriptor for an accessible Airlock spec."""
    return _resource_json(_call("airlock.user.describe_spec", [spec_name, CONFIG.default_airlock_role]))


@mcp.resource("airlock://specs/{spec_name}/files")
def spec_files(spec_name: str) -> str:
    """Files visible for an accessible Airlock spec."""
    return _resource_json(_call("airlock.user.list_my_files", [spec_name, CONFIG.default_airlock_role]))


@mcp.prompt(title="Submit file to Airlock")
def submit_file_to_airlock(spec_name: str, in_app_role: str | None = None) -> str:
    """Guide an agent through a validate-then-load Airlock submission."""
    role_text = in_app_role or "the caller's appropriate Airlock role"
    return (
        f"Submit data to Airlock spec {spec_name!r} using {role_text}. "
        "Use installed documentation as source of truth for procedure contracts. "
        "Use the public Airlock docs site only for product context and examples. First call "
        "airlock_describe_spec to inspect fields, accessible paths, workflow, "
        "and attachment policy. Then call airlock_validate_data with the exact "
        "CSV content or staged path. Only call airlock_load_data after validation "
        "succeeds. If attachment_required is true, include attachment_content_base64 "
        "and attachment_filename in the load call. Return the structured Airlock "
        "status, code, issues, path, filename, row count, and attachment result."
    )


@mcp.prompt(title="Triage Airlock expectation work")
def triage_expectation_work(spec_name: str | None = None, in_app_role: str | None = None) -> str:
    """Guide an agent through expectation work triage."""
    scope = f"spec {spec_name!r}" if spec_name else "all visible specs"
    role_text = in_app_role or "the caller's appropriate Airlock role"
    return (
        f"Triage Airlock expectation work for {scope} using {role_text}. "
        "Use installed documentation as source of truth for procedure contracts. "
        "Use public Airlock docs only for product context and examples. List visible work items "
        "and expectation work, inspect late or blocked rows, and recommend only "
        "documented Airlock procedure calls. Keep Snowflake roles and Airlock "
        "roles distinct in the explanation."
    )


@mcp.prompt(title="Explain Airlock architecture")
def explain_airlock_architecture(audience: str = "technical user") -> str:
    """Guide an agent in explaining Airlock's architecture context."""
    return (
        f"Explain Airlock to a {audience}. Present Airlock as the governance layer "
        "between flexible cognition and durable Snowflake records. Use the three-layer "
        "model: cognition layer (humans, agents, bespoke apps), governance layer "
        "(Airlock specs, validation, permissions, workflow, attachments, controlled "
        "procedures), and system-of-record layer (Snowflake). Emphasize that specs "
        "are durable business contracts defining what valid work looks like, while "
        "apps and agents can be task-specific or ephemeral. Explain why this reduces "
        "private agent-local state, supports multi-agent handoffs, preserves audit "
        "history, and lets Snowflake become a direct governed system of record rather "
        "than merely a downstream analytics warehouse. Keep "
        "implementation claims grounded: installed Airlock procedure documentation is "
        "the source of truth for exact capabilities."
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    mcp.run()


if __name__ == "__main__":
    main()
