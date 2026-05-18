from __future__ import annotations

import importlib


def test_source_files_list_is_json() -> None:
    server = importlib.import_module("airlock_mcp.server")

    assert server._source_files_arg(["a.csv", "b.csv"]) == '["a.csv", "b.csv"]'


def test_content_source_requires_exactly_one() -> None:
    server = importlib.import_module("airlock_mcp.server")

    result = server._validate_one_content_source("airlock.user.validate_data", None, None)

    assert result is not None
    assert result["code"] == "INVALID_CONTENT_SOURCE"


def test_delete_files_preserves_current_airlock_argument_order(monkeypatch) -> None:
    server = importlib.import_module("airlock_mcp.server")
    calls = []

    def fake_call(procedure, args=None):
        calls.append((procedure, args))
        return {"ok": True}

    monkeypatch.setattr(server, "_call", fake_call)

    result = server.airlock_delete_files(
        "invoices",
        ["a.csv", "b.csv"],
        source_directory="public/full_access",
        in_app_role="automation_user",
    )

    assert result == {"ok": True}
    assert calls == [
        (
            "airlock.user.delete_files",
            [
                "invoices",
                '["a.csv", "b.csv"]',
                "public/full_access",
                "automation_user",
                True,
                True,
            ],
        )
    ]


def test_attachment_tools_pass_role_lens_and_tag(monkeypatch) -> None:
    server = importlib.import_module("airlock_mcp.server")
    calls = []

    def fake_call(procedure, args=None):
        calls.append((procedure, args))
        return {"ok": True}

    monkeypatch.setattr(server, "_call", fake_call)

    server.airlock_add_attachment(
        "invoices",
        "public/full_access",
        "INV-1",
        attachment_content_base64="YWJj",
        attachment_filename="receipt.txt",
        in_app_role="automation_user",
        attachment_tag="receipt",
    )

    assert calls == [
        (
            "airlock.user.add_attachment",
            [
                "invoices",
                "public/full_access",
                "INV-1",
                None,
                "YWJj",
                "receipt.txt",
                "other",
                None,
                "automation_user",
                True,
                "receipt",
                None,
                None,
            ],
        )
    ]


def test_load_data_passes_delegation_context(monkeypatch) -> None:
    server = importlib.import_module("airlock_mcp.server")
    calls = []

    def fake_call(procedure, args=None):
        calls.append((procedure, args))
        return {"ok": True}

    monkeypatch.setattr(server, "_call", fake_call)

    server.airlock_load_data(
        "timesheets",
        file_content="employee,hours\njoe,8",
        filename="joe_timesheet",
        in_app_role="timesheet_agent",
        on_behalf_of_user="joe",
        delegation_id="D123",
    )

    assert calls == [
        (
            "airlock.user.load_data",
            [
                "timesheets",
                None,
                "employee,hours\njoe,8",
                "joe_timesheet",
                "timesheet_agent",
                None,
                None,
                None,
                True,
                "joe",
                "D123",
            ],
        )
    ]


def test_delegation_tools_use_user_procedures(monkeypatch) -> None:
    server = importlib.import_module("airlock_mcp.server")
    calls = []

    def fake_call(procedure, args=None):
        calls.append((procedure, args))
        return {"ok": True}

    monkeypatch.setattr(server, "_call", fake_call)

    create_result = server.airlock_create_delegation(
        {
            "actor_user": "deb",
            "spec_name": "demo_employee_reimbursements",
            "allowed_actions": ["load_data", "add_attachment"],
        }
    )
    list_result = server.airlock_list_my_delegations("received", "demo_employee_reimbursements")

    assert create_result == {"ok": True}
    assert list_result == {"ok": True}
    assert calls == [
        (
            "airlock.user.create_delegation",
            [
                {
                    "actor_user": "deb",
                    "spec_name": "demo_employee_reimbursements",
                    "allowed_actions": ["load_data", "add_attachment"],
                },
                True,
            ],
        ),
        (
            "airlock.user.list_my_delegations",
            ["received", "demo_employee_reimbursements", False],
        ),
    ]


def test_create_delegation_rejects_empty_descriptor() -> None:
    server = importlib.import_module("airlock_mcp.server")

    result = server.airlock_create_delegation({})

    assert result["ok"] is False
    assert result["code"] == "INVALID_DELEGATION_DESCRIPTOR"


def test_expectation_work_tool_uses_user_visible_procedure(monkeypatch) -> None:
    server = importlib.import_module("airlock_mcp.server")
    calls = []

    def fake_call(procedure, args=None):
        calls.append((procedure, args))
        return {"ok": True}

    monkeypatch.setattr(server, "_call", fake_call)

    result = server.airlock_list_expectation_work(
        spec_name="budget_requests",
        in_app_role="finance_reviewer",
        include_managed_roles=False,
    )

    assert result == {"ok": True}
    assert calls == [
        (
            "airlock.user.list_my_expectation_work",
            ["budget_requests", "finance_reviewer", False],
        )
    ]
