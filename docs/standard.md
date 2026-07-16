# FishToucher Prototype Standard

## 1. Scope

FishToucher coordinates multi-agent engineering work for the LinxISA NPU stack. LinxISA specifications, repositories, manifests, tests, and fresh runner reports remain the source of technical truth.

The keywords **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

## 2. One prototype contract

Every serialized flow, message, receipt, and evidence record MUST carry:

```json
"contract": "fishtoucher.prototype"
```

There are no numbered protocol variants and no compatibility readers. A breaking prototype change updates code, schemas, fixtures, and tests together.

## 3. Organization and authority

A Role Card defines a job, not a model provider. It MUST declare:

- stable role id, title, job family, and objective;
- capabilities and permissions;
- allowed and preferred drivers;
- inputs, outputs, completion conditions, and escalation conditions.

An agent instance has a unique name and exactly one active role per assignment. Effective authority is:

```text
role permissions ∩ assignment authority ∩ runtime sandbox
```

No component may widen this intersection. Review roles MUST be read-only. An implementer MUST NOT verify its own result.

Only the human System Engineer may freeze interfaces, approve waivers, resolve model conflicts, and promote releases. The `steward` MUST be the single routine human-facing role. A new steward MUST complete the takeover inventory and publish the first full report before spawning. It MAY spawn only registered roles and MUST aggregate progress plus every unresolved layer escalation into the report defined by `docs/steward-sop.md`.

## 4. Communication

The durable normal path is:

```text
assignment → result → verdict
```

`escalation` is exceptional. A result replies to its assignment; a verdict replies to the result. Internal delegated invocations MUST NOT add mailbox messages. Cross-role communication MUST be routed by the steward as referenced structured records, not free-form peer chat.

An assignment MUST bind a named assignee, exact target, base revision, read/write/tool/network/delegation authority, protected paths, context line ranges, completion conditions, commands, budgets, and escalation rules.

A rejecting verdict MUST identify each defect with severity, evidence, required fix, write scope, and required commands. Criticism without an executable repair is invalid.

A result MAY carry compact external `references`, including filed issue URLs. Raw provider output and copied issue bodies are not references.

## 5. Drivers

Drivers execute roles. They do not define them.

- The GPT `codex` driver is the default implementation and review path.
- An optional DeepSeek driver MAY execute `specialist-coder` assignments.
- All work MAY be completed with GPT drivers only.
- Exact models are deployment configuration, never role ids.

DeepSeek has no implicit repository, shell, network, credential, or tool authority. An external provider receives only the assignment context and tools granted by the permission intersection.

The Codex native spawn surface does not provide a portable per-call provider field. A user-level custom Codex provider may work with an OpenAI-compatible API, but the portable harness boundary is a driver. A standalone implementation SHOULD use Codex SDK/MCP for repository-capable GPT agents and an Agents SDK provider or equivalent adapter for DeepSeek.

## 6. Invocation evidence

Each provider call MUST write immutable, mode-`0600` logs outside the source tree:

```text
<run>/calls/<call-id>/<name>-<role>-req.json
<run>/calls/<call-id>/<name>-<role>-resp.json
```

The receipt MUST bind driver/provider/model, request and response hashes, timestamps, status, exit code, token usage, and tool actions. Raw request or response content MUST NOT be embedded in the receipt or mailbox.

## 7. Three loops

The software, architecture, and hardware loops progress independently behind versioned LinxISA interfaces. Each loop MUST stop at its first red hard break.

- Software proves API/compiler/ISA/functional behavior.
- Architecture proves functional equivalence before causal performance analysis.
- Hardware proves UT, integration, system behavior, model correlation, and reproducible physical evidence.

A later loop MUST NOT substitute for a missing earlier contract. A QEMU result does not prove cycle-model, RTL, performance, or physical closure.

## 8. Evidence and anti-gaming

Only deterministic evaluators derive gate status. `timeout`, `crash`, `skipped`, stale, and missing evidence are not pass. Waivers remain visibly waived and require a human record with owner, issue, phase, and expiry.

An implementation MUST NOT delete failing tests, weaken oracles, swallow exit status, shrink required suites, print a pass token instead of testing, reuse stale binaries, or overwrite failed attempts.

## 9. Verification and evolution

Dedicated LLVM, QEMU, ISA, and cross-stack verification jobs remain independent from implementation. Harness audit and optimization run only after a product verdict and may measure context bytes, calls, retries, latency, accepted-call ratio, and utilization. They MUST NOT rewrite accepted product evidence or gates.

A new role SHOULD require only a Role Card, a concise prompt, and tests. Requiring a new runtime role branch is an architectural defect unless the role introduces a genuinely new capability class.

Prototype tests MUST validate contracts, role/prompt registration, capability and authority bounds, message shape, driver routing, and loop topology. They MUST NOT spawn real agents, call paid providers, file issues, or run performance workloads.
