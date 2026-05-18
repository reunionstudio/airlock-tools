# Airlock Marketplace Install and Native App Security

Use this reference when a user asks how to install Airlock, what permissions it
needs, how Snowflake Native App security works, or how to uninstall/reinstall
without losing files and data.

## Sources

- Airlock Marketplace listing:
  `https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock`
- Public Airlock docs:
  `https://reunionstudio.io/airlock/docs/index.html`
- Public Airlock spec library:
  `https://reunionstudio.io/airlock/docs/spec-library.html`
- Snowflake Native App docs are authoritative for platform install, privilege,
  application-role, ownership-transfer, and uninstall behavior.

## Install Walkthrough

1. Open the Airlock Marketplace listing in Snowsight:
   `https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock`
2. Install the app into the consumer account. Choose the application name
   deliberately, commonly `AIRLOCK`.
3. Review requested privileges. Airlock may request `CREATE DATABASE` so the app
   can create its storage database, commonly `AIRLOCK_DATA`, inside the consumer
   account.
4. Grant required privileges to the installed application when prompted by
   Snowsight or with SQL:
   ```sql
   SHOW PRIVILEGES IN APPLICATION AIRLOCK;
   GRANT CREATE DATABASE ON ACCOUNT TO APPLICATION AIRLOCK;
   ```
5. Grant Snowflake application roles to account roles that should administer or
   use Airlock, following the installed app and Snowflake UI guidance. Keep
   Snowflake application roles (`app_admin`, `app_user`) distinct from Airlock
   roles created inside Airlock.
6. Launch Airlock or call installed procedures to confirm the install:
   ```sql
   CALL airlock.user.documentation();
   CALL airlock.user.documentation(CONTENT_MODE => 'PROCEDURES');
   CALL airlock.user.list_my_roles();
   ```

## Why Airlock Uses CREATE DATABASE

Airlock requests `CREATE DATABASE` so the installed Native App can create and own
an `AIRLOCK_DATA` database in the consumer account. Airlock uses this database
to create the Snowflake objects it needs for governed ingestion, including
storage for uploaded files, manifests, tables, views, attachments, and other
operational data.

This permission lets Airlock create its own storage database. It should not be
described as permission to read or modify arbitrary existing customer databases.
Access to existing customer objects still requires Snowflake grants, references,
or documented Airlock procedures.

## Native App Security Model

Airlock is a Snowflake Native App:

- The provider publishes an application package through a listing.
- The consumer installs an application object in their Snowflake account.
- Snowflake runs the app setup script during install/upgrade.
- Data and app-created objects remain in the consumer Snowflake account.
- The consumer reviews and grants requested privileges.
- Snowflake application roles control who can call the installed app's exposed
  procedures and UI.
- Airlock roles then enforce finer business access inside Airlock.

Do not bypass this model by editing Airlock-owned stages, tables, views, or
schemas directly.

## Uninstall Without Losing Airlock Data

Do not casually uninstall Airlock with an option that deletes app-owned objects
if the customer wants to keep uploaded files, manifests, attachments, or data.
In Snowflake Native Apps, dropping an app with `CASCADE` can drop objects owned
by the app. To retain app-owned objects outside the application object, transfer
ownership first.

Before uninstalling:

```sql
SHOW OBJECTS OWNED BY APPLICATION AIRLOCK;
```

If data must be retained, transfer ownership of the relevant app-owned objects
to a customer-controlled role before dropping the app. For example:

```sql
GRANT OWNERSHIP ON DATABASE AIRLOCK_DATA TO ROLE <customer_owner_role>;
```

Follow Snowflake's `GRANT OWNERSHIP` guidance for whether to copy current grants
and for object-specific ownership transfer requirements. In Snowsight, choose
the transfer option rather than the delete option when uninstalling and data
should be preserved.

## Reinstall and AIRLOCK_DATA Name Collision

If `AIRLOCK_DATA` still exists because ownership was transferred before
uninstall, a later Airlock install cannot create and own a database with that
exact same name. Rename the retained database before reinstalling:

```sql
ALTER DATABASE AIRLOCK_DATA RENAME TO AIRLOCK_DATA_ARCHIVE_YYYYMMDD;
```

Then reinstall Airlock so the app can create and own a fresh `AIRLOCK_DATA`
database. Rename only after confirming downstream dependencies, grants, and
retention needs.

## Agent Behavior

When helping with install or uninstall:

- Explain what you attempted and name the exact Snowflake or Airlock procedure
  or command.
- Separate Snowflake platform privileges from Airlock roles and license issues.
- Ask before destructive uninstall/drop actions.
- Warn that deleting app-owned objects may delete Airlock files and data.
- Prefer ownership transfer when the customer wants to preserve data.
- Do not suggest direct edits to Airlock-owned objects as a workaround.
