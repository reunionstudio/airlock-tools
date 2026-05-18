# MCP and Skill Reference Benchmarks

This repository should stay aligned with the agent tooling patterns Snowflake
and the MCP ecosystem are making familiar. These references are useful as
benchmarks, not as sources of Airlock procedure truth. Installed Airlock
documentation remains authoritative for procedure signatures and return
contracts.

## Primary References

### Snowflake Cortex Code Extensibility

Reference:
[Cortex Code CLI extensibility](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility)

Use this as the benchmark for Cortex Code skill packaging:

- skill directories containing `SKILL.md`
- YAML frontmatter with `name`, `description`, and optional `tools`
- project, user, global, remote, and bundled skill locations
- `cortex skill add`, `cortex skill list`, `cortex skill publish`, and
  stage/Git distribution mechanics
- focused skill guidance with examples and edge cases

Airlock's repo-local skill under `.cortex/skills/airlock/` should stay close to
this model. It should teach workflow and safety, not duplicate stored procedure
logic.

### Snowflake-Managed MCP Server

Reference:
[Snowflake-managed MCP server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)

Use this as the benchmark for Snowflake-native MCP expectations. Snowflake's
managed MCP server can expose Cortex Search, Cortex Analyst, SQL execution,
Cortex Agents, and generic UDF or stored procedure tools with input schemas.

For Airlock, this creates two valid integration paths:

- **Snowflake-managed MCP path**: expose selected Airlock stored procedures as
  generic stored procedure tools from inside Snowflake, where that deployment
  model fits the customer's agent stack.
- **Airlock Tools MCP path**: run this typed wrapper when agents need
  Airlock-specific tool names, safety gates, result normalization, resources,
  prompts, delegation context, and file/attachment guardrails.

The managed MCP path is a useful compatibility target. It does not replace this
repo's Airlock-specific adapter because generic procedure exposure does not
encode the workflow guidance that agents need to use Airlock well.

### Cortex Code Bundled Skills

Reference:
[Cortex Code CLI bundled skills](https://docs.snowflake.com/en/user-guide/cortex-code/bundled-skills)

Use this as a product taxonomy benchmark. Bundled skills show how Snowflake
groups repeatable workflows such as data quality, semantic views, dynamic
tables, cost intelligence, machine learning, governance, lineage, security, and
workload performance.

Airlock skills should follow the same spirit: make the agent better at one
focused domain, with clear triggers and expected behavior.

### Snowflake AI Kit

Reference:
[Snowflake-Labs/snowflake-ai-kit](https://github.com/Snowflake-Labs/snowflake-ai-kit)

Use this as a README and setup ergonomics benchmark. It is useful for:

- Snowflake CLI and Cortex Code CLI setup language
- shared Snowflake connection configuration expectations
- `cortex skill list` / `cortex skill add` usage
- clear separation between install, usage, skills, plugins, and troubleshooting

Airlock Tools should stay less installer-heavy unless the repo grows into a
packaged distribution, but the setup flow should be similarly scan-friendly.

For `v0.1.0`, the package distribution target is `airlock-tools`, with
`airlock-mcp` as the primary MCP server command.

### Snowflake Telco AI Assistant Quickstart

Reference:
[Snowflake-Labs telco assistant quickstart](https://github.com/Snowflake-Labs/sfguide-build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence)

Use this as a practical example of project-local `.cortex/skills/` shipped with
a Snowflake-oriented repo. It is especially useful for seeing how a repo can
bundle deployment and cleanup skills alongside SQL assets and documentation.

Airlock Tools should borrow the idea of project-local skills with examples, but
avoid making Airlock skills too deployment-script-specific. Airlock's main skill
should remain about governed procedure use.

### Official MCP SDKs and Reference Servers

References:

- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Model Context Protocol reference servers](https://github.com/modelcontextprotocol/servers)

Use these as implementation benchmarks for MCP server structure, tool/resource
registration, stdio/HTTP transport expectations, and security boundaries. For
Airlock's current Python server, the Python SDK and FastMCP examples are the
closest implementation reference.

Reference servers, especially filesystem-style servers, are useful for boundary
discipline: expose narrow capabilities, validate inputs, avoid leaking raw host
state, and make unsafe operations explicit.

### Snowflake-Labs MCP Repository

Reference:
[Snowflake-Labs/mcp](https://github.com/Snowflake-Labs/mcp)

This repository is deprecated in favor of Snowflake's official managed MCP
server docs, but it remains useful historical context for:

- client configuration examples
- stdio and streamable HTTP transport expectations
- container deployment notes
- debug logging and MCP client troubleshooting language

Do not treat it as the current Snowflake MCP implementation benchmark.

## Design Implications for Airlock Tools

Airlock Tools should make the Snowflake-native path and the Airlock-specific
path clear:

- If a customer only needs direct stored procedure exposure, Snowflake-managed
  MCP may be enough.
- If a customer needs Airlock-aware agent behavior, use this repo's MCP server
  or Cortex Code skill.
- If Cortex Code has SQL tools but no Airlock MCP server, the Airlock skill
  should guide the agent through installed documentation and procedure calls.
- If both the skill and MCP server are available, the skill should prefer typed
  Airlock MCP tools for common workflows and fall back to SQL only when needed.

This repository should keep the README approachable, with setup commands and
implementation details in `docs/development.md`. Benchmarks and tradeoffs belong
in this document and `docs/design.md`.

## Review Checklist

When updating Airlock Tools, compare against these references:

- Does the skill still match Cortex Code's current `SKILL.md` packaging model?
- Do examples use `cortex skill add` / `cortex skill list` language where
  helpful without turning the README into a CLI manual?
- Does the MCP server remain a thin wrapper around stored procedures?
- Could a Snowflake-managed MCP generic stored procedure tool satisfy the same
  use case? If yes, document why Airlock Tools still adds value.
- Are typed Airlock tools preserving structured Airlock outputs and reason
  codes better than a generic SQL or stored procedure wrapper would?
- Are setup, authentication, and troubleshooting details consistent with
  Snowflake CLI and Cortex Code expectations?
