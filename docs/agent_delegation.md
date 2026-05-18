# Agent Delegation Design

This document defines the proposed Airlock contract for user-to-agent
delegation. It is a design document, not a shipped API reference. Do not treat
the procedure names or parameters here as available until the installed Airlock
documentation exposes them.

## Summary

Agent delegation lets a human or business user explicitly authorize an agent
account to perform limited Airlock actions on that user's behalf.

Delegation is not impersonation. Airlock must keep both identities visible:

- `actor_user`: the Snowflake user or service account that called the procedure.
- `principal_user`: the user on whose behalf the action was performed.
- `delegation_id`: the explicit active grant used for the action.

Good audit wording:

```text
Deb submitted joe_timesheet_2026_05_17.csv on behalf of Joe.
```

Avoid:

```text
Joe submitted joe_timesheet_2026_05_17.csv.
```

The second sentence hides the actor and turns delegation into impersonation.

## Product Defaults

The conservative default is:

- Delegation is disabled unless a spec explicitly enables it.
- Delegation starts with submit-style actions, not governance actions.
- Actor and principal are both evaluated by the PDP.
- Delegated files use the principal user's path scope when the spec has
  per-user isolated directories.
- The actor is visible in `created_by`, `uploaded_by`, events, and procedure
  result context.
- The principal is visible in delegated result context and events.
- Ambiguous delegation grants fail instead of guessing.

## Initial Action Set

Recommended phase-one delegated actions:

| Action | Include first? | Reason |
| --- | --- | --- |
| `validate_data` | Yes | Read/validation planning, no mutation. |
| `load_data` | Yes | Primary use case: agent submits a user's file. |
| `add_attachment` | Yes | Needed for evidence such as reimbursements or timesheets. |
| `replace_attachment` | Later | Permanent in Airlock and needs clearer policy. |
| `delete_files` | No | Destructive and not needed for first submission workflows. |
| `delete_attachment` | No | Destructive and not needed for first submission workflows. |
| workflow submit transition | Later | Useful, but should be action-scoped by workflow policy. |
| workflow approval/rejection | No | Governance decision, not a simple delegated submission. |
| spec/admin operations | No | Too broad for user-to-agent delegation. |

Example split: an agent can be delegated to validate, load, and add evidence for
a user's reimbursement, but submit/review/approval workflow transitions remain
outside the grant until product policy explicitly allows them.

## Spec Configuration

Delegation belongs in spec access/workflow policy, not column validation.

Proposed config shape:

```json
{
  "delegation_policy": {
    "enabled": false,
    "allowed_actions": ["validate_data", "load_data", "add_attachment"],
    "allowed_actor_roles": ["timesheet_agent", "automation_user"],
    "principal_scope": "assigned_users",
    "workflow_step_actions": [
      {
        "step_name": "Draft",
        "step_order": 1,
        "allowed_actions": ["validate_data", "load_data", "add_attachment"]
      },
      {
        "step_name": "Submitted",
        "step_order": 2,
        "allowed_actions": []
      }
    ],
    "requires_user_approval": true,
    "max_duration_days": 365
  }
}
```

Field meanings:

- `enabled`: explicit opt-in for the spec. Default is `false`.
- `allowed_actions`: delegable Airlock actions for this spec.
- `allowed_actor_roles`: Airlock roles that may act as delegates.
- `principal_scope`: which users may be principals. Initial value should be
  `assigned_users`.
- `workflow_step_actions`: optional per-step narrowing of delegable actions. If
  present, global `allowed_actions` is only the outer allowlist; the step must
  also allow the requested action.
- `requires_user_approval`: whether a user must personally approve the
  delegation, as opposed to admin-created delegation only.
- `max_duration_days`: upper bound on delegation validity.

Use this for submit-style workflows: a spec admin can allow an agent to prepare
files and attachments while the file is in `Draft`, but keep `Draft ->
Submitted` or later approval transitions non-delegatable.

## Delegation Record

Candidate table:

```sql
core.agent_delegations (
  pk VARCHAR PRIMARY KEY,
  hk BINARY(32) NOT NULL,
  created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
  created_by VARCHAR NOT NULL,
  modified_at TIMESTAMP_LTZ,
  modified_by VARCHAR,
  principal_user VARCHAR NOT NULL,
  principal_user_norm VARCHAR NOT NULL,
  actor_user VARCHAR NOT NULL,
  actor_user_norm VARCHAR NOT NULL,
  actor_airlock_role VARCHAR,
  spec_name VARCHAR NOT NULL,
  allowed_actions VARIANT NOT NULL,
  path_scope VARCHAR,
  effective_from TIMESTAMP_LTZ,
  effective_to TIMESTAMP_LTZ,
  revoked_at TIMESTAMP_LTZ,
  revoked_by VARCHAR,
  revoke_reason VARCHAR,
  comment VARCHAR,
  is_locked BOOLEAN DEFAULT FALSE
)
```

Normalize user names for lookup, but keep original display values for audit.

Useful lookup fields:

- `actor_user_norm`
- `principal_user_norm`
- `spec_name`
- `actor_airlock_role`
- active-window fields if Snowflake supports the desired hybrid-table index
  shape

## Procedure Contract

### Delegation Management

Possible admin/spec-admin procedures:

```sql
CALL airlock.admin.create_delegation(delegation_descriptor, validate_only);
CALL airlock.admin.list_delegations(in_app_role, spec_name, principal_user, actor_user);
CALL airlock.admin.revoke_delegation(delegation_id);
```

Optional self-service procedures, if product policy allows:

```sql
CALL airlock.user.create_delegation(delegation_descriptor, validate_only);
CALL airlock.user.list_my_delegations();
CALL airlock.user.list_delegations_to_me();
CALL airlock.user.revoke_delegation(delegation_id);
```

A conservative first implementation can be admin/spec-admin-created only, with
user-facing read/list so principals can see what exists.

### Delegated User Actions

Delegated action procedures should add two optional trailing parameters:

```text
on_behalf_of_user VARCHAR DEFAULT NULL,
delegation_id VARCHAR DEFAULT NULL
```

Example:

```sql
CALL airlock.user.load_data(
  spec_name => 'timesheets',
  path => NULL,
  file_content => :csv,
  filename => 'joe_timesheet_2026_05_17',
  in_app_role => 'timesheet_agent',
  path_scope => NULL,
  attachment_content_base64 => NULL,
  attachment_filename => NULL,
  include_managed_roles => TRUE,
  on_behalf_of_user => 'joe',
  delegation_id => 'D123'
);
```

`delegation_id` can be optional only when exactly one active grant matches the
actor, principal, spec, role lens, and action. If more than one active grant
matches, return `AMBIGUOUS_DELEGATION`.

## PDP Contract

The PDP should evaluate delegated calls in this order:

1. Normalize `actor_user` from `CURRENT_USER()`.
2. Normalize `principal_user` from `on_behalf_of_user`.
3. If no `on_behalf_of_user`, use existing non-delegated behavior.
4. Load the spec and verify `delegation_policy.enabled`.
5. Verify the requested action is allowed by spec policy.
6. Verify actor's Airlock role is allowed by spec policy.
7. Resolve an active delegation record.
8. Evaluate principal access to the spec/path/action.
9. Evaluate actor delegate access to the spec/path/action.
10. Apply normal workflow, attachment, reference, and validation checks.

PDP response should include:

```json
{
  "delegation": {
    "delegated": true,
    "delegation_id": "D123",
    "actor_user": "DEB_AGENT",
    "principal_user": "JOE",
    "action": "load_data"
  }
}
```

## Path Scope Rule

When a spec uses isolated per-user paths, delegated uploads should default to the
principal user's path key, not the actor's path key.

Example:

```text
Deb submits for Joe
Spec has isolated user directories
Airlock writes under Joe's path scope
Audit says actor=Deb, principal=Joe
```

This preserves the business meaning of "Joe's timesheet" while still showing who
actually submitted it.

## Event and Manifest Contract

For the first implementation:

- Keep `created_by`, `uploaded_by`, and procedure `username` values as actor.
- Add explicit delegation context to event payloads/results.
- Consider adding `principal_user` or `on_behalf_of_user` columns only when UI,
  audit queries, or external consumers need direct filtering.

Do not silently store the principal in existing actor columns. That would make
delegation indistinguishable from impersonation.

## Licensing Contract

For the first implementation:

- The actor user must satisfy the same named-license requirement as any other
  caller of `airlock.user.*`.
- Delegated actions must not automatically claim or bill a seat for the
  principal user.
- The principal user must still be a valid Airlock identity for the spec/path
  policy being evaluated.

This avoids surprise billing when one approved agent submits for many users. If
a future pricing model charges delegated principals separately, that must be an
explicit product and Marketplace billing change, not a side effect of
delegation.

## Result Contract

Every delegated mutation should return the normal Airlock result plus:

```json
{
  "DELEGATED": true,
  "ACTOR_USER": "DEB_AGENT",
  "PRINCIPAL_USER": "JOE",
  "DELEGATION_ID": "D123"
}
```

Denials should use stable codes:

- `DELEGATION_DISABLED`
- `DELEGATION_ACTION_NOT_ALLOWED`
- `DELEGATION_ACTOR_ROLE_NOT_ALLOWED`
- `DELEGATION_NOT_FOUND`
- `DELEGATION_EXPIRED`
- `DELEGATION_REVOKED`
- `AMBIGUOUS_DELEGATION`
- `DELEGATION_PRINCIPAL_ACCESS_DENIED`
- `DELEGATION_ACTOR_ACCESS_DENIED`

## UI Contract

UI should say:

```text
Submitting as Deb for Joe
```

Avoid:

```text
Logged in as Joe
```

Spec admins should configure delegation near access/workflow controls. User
settings should list active delegations both directions:

- agents who can act for me
- users I can act for

## MCP and CoCo Contract

MCP tools should add `on_behalf_of_user` and `delegation_id` only to tools that
support delegation in the installed Airlock API. Tool descriptions must say the
call remains audited as the actor acting for the principal.

The Cortex Code skill should instruct agents:

- never log in as the principal
- use Airlock delegation parameters only when installed documentation exposes
  them
- report delegated results as "Submitted as Deb for Joe"
- preserve delegation denial codes
- preserve actor, principal, and delegation id in structured output

## Testing Contract

Required tests before shipping:

- non-delegated calls still behave exactly as before
- delegation disabled by default
- spec delegation disabled denies delegated call
- actor role not allowed denies call
- missing/expired/revoked delegation denies call
- principal access denied denies call
- actor delegate access denied denies call
- valid delegation writes to principal path scope for isolated user specs
- result and event include actor, principal, and delegation id
- ambiguous active delegation fails without `delegation_id`

## Implementation Rule

No delegated action should run unless Airlock can answer:

```text
Who acted?
For whom?
Under which delegation?
For which spec, path, and action?
Was that grant valid at execution time?
```
