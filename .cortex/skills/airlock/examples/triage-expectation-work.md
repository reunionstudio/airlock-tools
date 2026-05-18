# Triage Expectation Work

Use this pattern when a user asks about late, missing, due, or blocked Airlock
work.

## Procedure Path

1. Discover the installed expectation procedure surface:
   ```sql
   CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
   ```
2. List the caller's Airlock roles:
   ```sql
   CALL airlock.user.list_my_roles();
   ```
3. For user-visible expectation status:
   ```sql
   CALL airlock.user.list_my_expectation_work('<spec_name>', '<airlock_role>', TRUE);
   ```
   With the Airlock MCP server, prefer:
   ```text
   airlock_list_expectation_work(
     spec_name='<spec_name>',
     in_app_role='<airlock_role>',
     include_managed_roles=true
   )
   ```
4. If the user asks to move files through workflow, list work items before
   editing:
   ```sql
   CALL airlock.user.list_my_work_items('<spec_name>', '<airlock_role>', TRUE);
   CALL airlock.user.edit_file_workflow(
     '<spec_name>',
     '<path>',
     '<filename>',
     '<action>',
     '<comment>',
     TRUE,
     '<airlock_role>'
   );
   ```
5. Only call `edit_file_workflow` with `validate_only => FALSE` after the user
   approves the transition.

## Report

Explain expectation status as business activity status, not data-shape
validation. Include expectation name, spec name, milestone, enforcement mode,
status, due time, matching file count, exception count, available actions, and
Airlock reason codes.

Use plain operational language:

- `met`: expected work has matching files or activity.
- `pending`: not late yet; no action may be needed.
- `late` or `missing`: identify the expected milestone and next safe procedure.
- `blocked`: name the sequence, interval, workflow, or exception condition that
  Airlock returned.
- `exception_applied`: explain that an approved exception is affecting the
  expected action or enforcement result.
