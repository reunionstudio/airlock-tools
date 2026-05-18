# MCP, AI Agents, and Airlock Stored Procedures

This note explains what MCP is, why it is popular with AI agents, and how
Airlock's Snowflake stored procedures relate to that idea. Airlock itself is a
database-native API, not an MCP endpoint. This repository provides an optional
MCP adapter around the stored procedure API.

For the concrete server design, see [design.md](design.md).
For proposed user-to-agent delegation semantics, see
[agent_delegation.md](agent_delegation.md).

## What MCP Is

Model Context Protocol (MCP) is a structured way for an AI client, such as an IDE
assistant or desktop agent, to talk to external capabilities over a well-defined
protocol. A typical MCP server advertises:

- Tools: named operations with machine-oriented descriptions and typed
  arguments.
- Resources: addressable content the model can read, such as docs or query
  results.
- Prompts: reusable prompt templates.

The host discovers tools, lets the model choose them, and executes calls with
structured arguments. That reduces one-off command snippets and makes behavior
more inspectable and repeatable.

## Why MCP Is Popular With Agents

MCP fits the agent tool-use loop well:

- Discovery: clients can list tools and intended use without hardcoding every
  product.
- Structured I/O: arguments and errors are easier to validate than free-form
  shell commands.
- Separation of concerns: the model reasons about what to call while the server
  handles authentication, transport, and auditing.
- Ecosystem momentum: many tools now expose MCP adapters, so agents get a
  familiar integration pattern.

MCP is not the only viable integration style. REST with OpenAPI, GraphQL, gRPC,
raw SQL, and Snowflake stored procedures can all be sound interfaces. MCP is
useful when the primary caller is an agent host that already understands the
protocol.

## How Airlock Is Like MCP

Airlock exposes a named, versioned surface of operations:

| MCP idea | Airlock analogue |
| --- | --- |
| Tool name | `airlock.user.*` and `airlock.admin.*` procedures |
| Tool description | `airlock.user.documentation(...)`, `airlock.user.help(...)`, and `airlock.admin.help(...)` |
| Catalog / discovery | `airlock.user.documentation(CONTENT_MODE => 'PROCEDURES')` and `airlock.admin.api_info()` |
| Invocation | `CALL airlock.user.load_data(...)`, `CALL airlock.admin.create_spec(...)`, and other stored procedure calls |
| Bounded behavior | Snowflake grants, application roles, Airlock roles, licenses, and in-procedure PDP checks |

Conceptually, each stored procedure is tool-like: it has a name, parameters,
return shape, and documentation intended for humans and agents.

Agents should keep the role model precise. Snowflake roles and Snowflake
application roles determine which procedures can be called. Airlock roles
determine business access inside those procedures. A spec owner is the Airlock
role named as a spec's owner role; it can see all data for that spec and manage
its workflows even when it is not a spec admin. An Airlock spec-admin role is
delegated business administration for editing spec configuration or
expectations, not Snowflake `app_admin`, and it is not required to own a spec.
Airlock role hierarchy uses `managed_by_role`: a manager role can include access
from managed child roles where procedures support managed-role expansion, while
the child does not automatically inherit the manager's access.

## How Airlock Is Unlike MCP

| Aspect | MCP | Airlock stored procedure API |
| --- | --- | --- |
| Transport | MCP messages over stdio or HTTP | Snowflake SQL, Snowpark, or drivers |
| Discovery format | MCP tool/resource/prompt listing | Procedure registry rows and documentation payloads |
| Argument schema | JSON Schema generated from tool definitions | SQL procedure signatures plus structured documentation |
| Resources | First-class MCP resource URIs | Read-only procedures and governed Snowflake data access |
| Identity | MCP host and server context | Snowflake session, application roles, Airlock roles, and license state |

Airlock's stored procedures are the source of truth. An MCP server should
translate MCP calls into documented procedure calls, not move business logic or
authorization out of Snowflake.

## What This Adapter Adds

This repository makes Airlock more convenient for MCP-centric agents by wrapping
the procedure API:

- MCP tools map to documented `airlock.user.*` procedures.
- MCP resources map to read-only documentation/spec/file procedure calls.
- MCP prompts describe safe agent workflows, such as describe, validate, load,
  attach, and report.
- Responses preserve structured Airlock status, codes, issues, rows, and
  identifiers.

The same pattern can later extend to explicitly enabled admin tools or other
documented schemas when the product surface requires it.

Future delegation support should remain procedure-driven. MCP tools should add
`on_behalf_of_user` and `delegation_id` only after installed Airlock
documentation exposes those parameters. Delegated calls must preserve actor,
principal, and delegation id in structured output; they must not summarize an
agent's delegated action as if the principal directly performed it.

## Architecture Narrative

MCP tools should teach agents how to use Airlock, but prompts can also teach the
architectural idea behind it:

- cognition happens with humans, agents, and task-specific tools
- governance happens through Airlock specs, permissions, validation, attachments,
  workflow, and controlled procedures
- durable recordkeeping happens in Snowflake

That narrative helps agents understand why direct writes are not just unsafe,
but conceptually wrong for the Airlock model. Agents should see specs as the
durable business contract and apps as potentially flexible cognition surfaces.
They should also understand that Snowflake is positioned as the direct system of
record in this architecture, not simply a downstream analytics warehouse where
records arrive after the real workflow happens in another app.

For spec design, agents should prefer stable typed columns for durable business
facts and use validated `variant` columns for evolving context. The flexible
payload should still be governed by Airlock rules, such as `variant_shape` or
documented `field_path` checks, rather than becoming an unvalidated escape hatch.

## Would MCP Be Better?

Sometimes. MCP is helpful when the main user is an IDE or desktop agent and the
team wants zero manual SQL. It is less necessary when operators are already
Snowflake-native and call procedures from SnowSQL, Snowsight, tasks, or drivers.

The stored procedure approach is strong for correctness, security, and
operations. MCP is a presentation and transport layer for agents, not a
replacement for procedures, grants, licensing, policy decisions, or audit events.

## Help and Documentation

Airlock's installed documentation gives agents the source of truth:

- `airlock.user.documentation()` returns a structured table of contents.
- `airlock.user.documentation(CONTENT_MODE => 'PROCEDURES')` returns a compact
  structured procedure registry.
- `airlock.user.documentation(CONTENT_MODE => 'SECTION')` returns selected
  sections.
- `airlock.admin.api_info()` returns admin procedure version metadata when the
  caller has admin access.

Public docs are useful context but should not override installed app contracts:

- [Airlock documentation](https://reunionstudio.io/airlock/docs/index.html) for
  product concepts, guides, and operator-facing workflows.
- [Airlock spec library](https://reunionstudio.io/airlock/docs/spec-library.html)
  for reusable spec examples and business-object modeling patterns.
- [Airlock Marketplace listing](https://app.snowflake.com/marketplace/listing/GZTSZ1QRFJ6L/reunion-studio-airlock)
  for install entrypoint and listing context.

Agents should read public docs for orientation and examples, then verify exact
procedure names, signatures, return shapes, reason codes, and available sections
with the installed `airlock.user.documentation(...)` procedure.

For installation and uninstall planning, agents should also know Snowflake Native
App behavior: consumers grant requested privileges to the application, Airlock
may request `CREATE DATABASE` to create and own `AIRLOCK_DATA`, and app-owned
objects should be transferred before uninstall if files/data must be retained.
If retained `AIRLOCK_DATA` remains in the account, rename it before reinstalling
Airlock so the new app can create and own its expected storage database.

For many agent workflows, this is enough context. The adapter adds standard MCP
tool discovery and stable tool names so the agent does not need to construct SQL
directly.

## Summary

MCP standardizes how agents discover and call tools. Airlock already has a
tool-like surface through stored procedures and installed documentation, but over
Snowflake rather than MCP. This server wraps that surface for agent hosts while
preserving Snowflake and Airlock as the authorization, validation, lifecycle, and
audit authority.
