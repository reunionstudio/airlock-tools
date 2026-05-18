# Airlock Architecture Playbook

Use this reference when the user asks for Airlock architecture philosophy,
product narrative, customer explanations, or why Airlock matters for AI-agent
businesses. Do not use it to override installed Airlock procedure documentation.

## Core Thesis

Airlock is a governance layer between Snowflake and AI agents, assistants, or
humans doing adaptive business work. It supports an agent-oriented business
architecture where apps can be ephemeral, bespoke, or quickly built for the
task, while the durable layer is the governed output specification, validation,
access model, workflow state, and system of record.

The long-lived asset is not necessarily the application. It is the output
contract the work must satisfy.

## Three Layers

Airlock's recommended agent-oriented architecture separates business work into three layers:

1. Cognition layer: humans, AI agents, temporary tools, spreadsheets, bespoke
   apps, and local workflows interpret context and produce work.
2. Governance layer: Airlock defines valid work, permissions, validation,
   required attachments, references, workflow states, and controlled submission
   procedures.
3. System-of-record layer: Snowflake stores official records, shared context,
   current state, historical outputs, and audit-friendly operational history.

The key idea: cognition can stay flexible, but governance and recordkeeping
should stay centralized. In this architecture, Snowflake is not merely a
downstream analytics warehouse where data lands after the real work happens
elsewhere. Snowflake becomes the direct system of record where governed business
outputs are created, retained, audited, queried, and reused.

## What a Spec Means

In Airlock, a spec is not just a schema. It is what "done" looks like for a
class of business output:

- fields and data types
- validation rules
- required attachments
- reference checks
- permissions and role lenses
- path scopes and guest access
- flexible context payloads with explicit variant validation
- workflow states and lifecycle rules
- current and historical outputs

A spec is part form, part policy, part procedure, part permissions model, and
part training manual for agents.

## Why Apps Can Be Ephemeral

Many business processes are not exactly the same twice. A budget cycle, tax
filing, reimbursement review, or vendor onboarding process may share a governed
output but vary in context, assumptions, local calculations, and judgment.

In older enterprise software, the application often had to be the cognition
surface, governance layer, and system of record all at once. That made apps
large, sticky, expensive, and generic. In an AI-agent architecture:

- Snowflake can be the direct system of record.
- Airlock can be the governance layer.
- Apps and agents can focus on cognition: interpretation, drafting, analysis,
  exception handling, and decision support.

Short-lived or AI-generated apps become easier to evaluate when they are not
also expected to be the governance layer or the system of record. Airlock and
Snowflake move those responsibilities out of the app. That lets teams use
bespoke apps and agent-built tools for cognition while Airlock governs what can
become official.

If the output of one of these tools does not satisfy the Airlock spec, it does
not enter Snowflake. If it does enter Snowflake, workflow steps can still govern
review, rejection, archive, or handoff.

## Old Pattern, New Medium

Airlock is an AI-era implementation of an old organizational pattern:

- Pre-computer: workers did cognition; scribes, forms, ledgers, seals, and
  archives governed official records.
- Enterprise software: cognition, governance, and records were bundled into
  large applications and their databases.
- AI-agent era: cognition can happen in humans and agents; Airlock supplies
  governed contracts and procedures; Snowflake holds the official record.

The business should own the records, outputs, workflow definitions, shared data
structures, and operational context required to continue work after any one
human, model, agent, or vendor changes.

## Why Snowflake and Native Apps Matter

Snowflake gives the business a central, secure, enterprise-ready operating layer
without requiring a sprawling infrastructure stack.

Snowflake Native Apps strengthen the model because capability runs inside
Snowflake rather than adding another SaaS boundary, login, SSO integration,
network perimeter, data pipeline, procurement path, and operational dependency.
The point is outcomes, not infrastructure.

Airlock helps Snowflake move from downstream analytics destination toward direct
system of record for governed business processes carried out by humans and AI
agents. Airlock is not just another way to land data in Snowflake after a SaaS
application creates the official record. It lets governed records be created in
Snowflake first.

## Agent Collaboration Hypothesis

Without a governed shared layer, multi-agent systems drift toward fragile
coordination:

- each tool keeps its own memory
- each prompt invents conventions
- handoffs are implicit
- outputs are difficult to trust or reuse
- important state can become stranded in private files or proprietary runtimes

Airlock creates a shared operating language. Agents collaborate through
centrally governed inputs and outputs rather than private prompt history.

This improves interoperability, portability across models/vendors, agent
onboarding, auditability, and durability of business assets.

## Human-Era vs Agent-Era Pattern

| Human-era pattern | Agent-era pattern with Airlock |
| --- | --- |
| Worker logs into a SaaS system | Agent receives a governed contract |
| UI teaches the worker what to fill out | Spec teaches the agent what to produce |
| Policy lives in forms and button flows | Policy lives in specs, permissions, validation, and workflow |
| Official record lands in an app database | Official record lands in Snowflake |

This is not an argument against software. It says AI agents do not always need
the same human-shaped delivery mechanism enterprise software used to provide.
They need the underlying contract.

## Examples

Reimbursements:

- An employee sends a receipt to an agent.
- The agent performs OCR, extracts fields, and asks follow-up questions.
- Airlock provides the required submission structure and attachment policy.
- The agent submits governed data and the receipt into Snowflake.
- Managers and finance act on business-owned records, not agent-local notes.

Timesheets:

- Submission, approval, payroll handoff, and archive become governed steps.
- Each step has explicit input/output rules.
- The assigned agent needs the contract for its step, not a bespoke SaaS UI.

Budget requests:

- Department agents use local context and iteration to prepare drafts.
- Airlock defines the spec, permitted paths, validation, and review workflow.
- Final submissions land centrally in Snowflake for finance review.

## Design Principles

- The system of record belongs to the business.
- Adaptive work is allowed at the edge.
- Specs are communication as much as enforcement.
- Humans, agents, and tools change; organizational context should endure.
- Policy should be expressed as contracts.
- Flexible context belongs in governed variant fields, not in unvalidated
  side-channel state.
- Shared governed context is better than private memory.
- Current state and history both matter.

## Decision Filter

Use this filter for product ideas, architecture changes, and explanatory docs:

1. Does this make the system of record more business-owned?
2. Does this reduce private, stranded, agent-local state?
3. Does this make a workflow step easier to understand through clear inputs and
   outputs?
4. Does this improve portability from one human or agent or app to another?
5. Does this preserve flexibility at the edge while strengthening governance at
   the center?

If mostly yes, it likely fits Airlock.
