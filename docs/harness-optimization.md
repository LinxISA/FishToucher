# Harness Efficiency and Evolution

## Default policy

- Use a dedicated LinxISA role before `senior-coder`; use `senior-coder` only for an uncovered domain.
- Keep normal delegation at one steward-to-role hop. Permit one Senior Coder-to-Specialist hop only when the assignment and runtime allow depth 2.
- Parallelize only independent tasks with disjoint write scopes and output directories.
- Use `specialist-coder` for one leaf task; route it to GPT unless an enabled DeepSeek driver has a measured advantage.
- Send exact sections, diffs, contract excerpts, and failure logs—not whole repositories or conversation history.
- Persist three normal records and zero internal-call mailbox chatter.

## Metrics

For each accepted run, measure:

- request and response bytes;
- input and output tokens when reported;
- call and retry count;
- elapsed and queue time;
- accepted delegated-call ratio;
- context utilization;
- rejection causes;
- parallel-write conflicts;
- generic fallback-role usage.

Do not optimize NPU performance in this harness phase. These are workflow metrics only.

## Two post-verdict jobs

The `harness-auditor` checks takeover, permissions, separation of duties, escalation visibility, and evidence provenance. The `harness-efficiency-engineer` may then change FishToucher to improve a measured workflow metric. It cannot rewrite accepted product evidence or gates.

A repeated fallback domain is an organization smell. The `role-skill-curator` converts it into a LinxISA-specific Role Card, prompt, docs, and structural tests without adding a runtime role-id branch.

## Acceptance gate

An optimization is accepted only when protocol tests stay green and before/after evidence shows lower cost, latency, retries, or coordination conflict. A new capability class may justify runtime code, but a new job title alone does not.
