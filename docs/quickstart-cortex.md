# Cortex Code Skill Quickstart

Use this path when the agent is Snowflake Cortex Code and can call Snowflake SQL
tools directly. The Airlock skill teaches Cortex Code how to use Airlock stored
procedures safely.

## Prerequisites

- Cortex Code CLI is installed and connected to Snowflake.
- Airlock is installed from the
  [Snowflake Marketplace listing](https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock).
- The active Snowflake role can use the installed Airlock app and required
  application role.
- The caller has the needed Airlock role assignment and license seat.

## Add the Skill

From a local clone of this repo:

```bash
cortex skill add .cortex/skills
cortex skill list
```

After this repo is published, Cortex Code can also add skills from Git. Use the
released tag or branch your team has approved:

```bash
cortex skill add https://github.com/reunionstudio/airlock-tools.git
cortex skill list
```

If your Cortex Code version expects a direct skill directory, clone the repo and
add `.cortex/skills` locally.

## First Prompt

Start Cortex Code in a workspace with the skill available:

```bash
cortex
```

Then ask:

```text
$airlock Discover my Airlock roles and list the specs I can use.
```

For a file submission:

```text
$airlock Submit @budget.csv to the FY26 budget spec as role finance_agent.
```

The skill should make Cortex Code:

1. Query installed Airlock documentation.
2. List the caller's Airlock roles.
3. List and describe accessible specs.
4. Validate candidate data.
5. Load only after validation succeeds.
6. Preserve structured Airlock status, codes, issues, path, filename, and
   workflow context.

## Share Through Snowflake

For customer teams that want Snowflake-role-controlled distribution, publish the
skill directory to a Snowflake stage:

```bash
cortex skill publish .cortex/skills --to-stage @MY_DB.MY_SCHEMA.MY_STAGE/airlock-skills/
cortex skill add @MY_DB.MY_SCHEMA.MY_STAGE/airlock-skills/
```

Grant `READ` on the stage to users who should load the skill. Grant `WRITE`
only to trusted publishers.

## With MCP

If the Airlock Tools MCP server is also available, the skill should prefer typed
Airlock tools such as:

- `airlock_describe_spec`
- `airlock_validate_data`
- `airlock_load_data`
- `airlock_add_attachment`
- `airlock_list_expectation_work`

Without MCP, the skill should call installed Airlock procedures through
Snowflake SQL tools.
