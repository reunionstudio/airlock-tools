# Draft Spec From Template

Use this pattern when a user asks to draft a new spec from an assigned or public
Airlock template.

## Preferred User Path

1. Discover installed procedures and Airlock roles:
   ```sql
   CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
   CALL airlock.user.list_my_roles();
   ```
2. Inspect available templates using installed documentation for the current API.
   If user-facing template-list procedures are not installed, explain that an
   app admin may need to inspect template assignments.
3. Prepare override values from the user's request. Keep overrides narrow.
   Use stable typed columns for durable business facts. When the user needs
   future flexibility for evolving context, add or request a `variant` column
   with explicit `variant_shape` validation instead of creating many speculative
   columns.
4. Create from an assigned template:
   ```sql
   CALL airlock.user.create_spec_from_template(
     '<template_name>',
     '<new_spec_name>',
     '<spec_alias>',
     PARSE_JSON('<spec_config_overrides_json>')
   );
   ```

## Admin Path

For admin creation or alteration:

1. Call the relevant create/alter procedure with `validate_only => TRUE` when
   available.
2. Show the planned spec name, owner Airlock role, publication state, fields,
   workflow, attachment policy, guest access, and validation issues.
3. Ask for approval before the mutating call.
4. Preserve returned `STATUS`, `CODE`, `MESSAGE`, `ISSUES`, and `VALIDATION`.

Never write directly to `core.specs`, stages, generated views, or generated
tables.

## Flexible Context Pattern

Use a `variant` column for contextual payloads that may change over time, such
as `processing_context`, `evidence`, or `agent_context`. Keep join keys,
required identifiers, dates, amounts, and workflow-driving fields as first-class
typed columns.

When the installed Airlock API supports it, pair the variant column with a
`variant_shape` rule. Admins can later alter the spec config to permit and
validate new nested keys without changing the physical table shape.
