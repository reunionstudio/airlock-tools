# Submit File With Attachment

Use this pattern when a user asks to submit a CSV rowset plus evidence such as a
receipt PDF or image.

## Procedure Path

1. Confirm context:
   ```sql
   SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_WAREHOUSE();
   ```
2. Discover installed procedures and roles:
   ```sql
   CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
   CALL airlock.user.list_my_roles();
   ```
3. Find and describe the spec:
   ```sql
   CALL airlock.user.list_my_specs('<airlock_role>');
   CALL airlock.user.describe_spec('<spec_name>', '<airlock_role>');
   ```
4. Validate the CSV:
   ```sql
   CALL airlock.user.validate_data(
     '<spec_name>',
     NULL,
     '<csv_header_and_rows>',
     '<airlock_role>'
   );
   ```
5. If validation succeeds, base64 encode the attachment only for the procedure
   call and load:
   ```sql
   CALL airlock.user.load_data(
     '<spec_name>',
     NULL,
     '<csv_header_and_rows>',
     '<logical_filename>',
     '<airlock_role>',
     '<path_scope_from_accessible_paths>',
     '<base64_attachment>',
     '<attachment_filename>'
   );
   ```

## Report

Return the structured Airlock result:

- `STATUS`
- `CODE`
- `MESSAGE`
- `ISSUES`
- `SPEC_NAME`
- `PATH`
- `FILENAME`
- `ROW_COUNT`
- attachment identifiers or attachment issue codes

Do not log raw attachment bytes.
