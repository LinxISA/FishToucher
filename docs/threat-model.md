# Threat Model

FishToucher assumes agents are capable, helpful, fallible, context-limited, and strongly incentivized by an underspecified Definition of Done.

## Protected assets

- ISA, ABI, trace, privilege, and memory-model contracts
- required gate definitions and test inventory
- reference outputs, baselines, and waivers
- credentials, licensed tool data, and unpublished IP
- repository history and evidence from failed attempts

## Failure modes

- weakening or deleting a failing test;
- changing an oracle or reference output in the implementation lane;
- swallowing failure status or printing a fake pass marker;
- running a smaller suite than the locked plan;
- presenting stale binaries, dirty trees, or mismatched SHAs as evidence;
- leaking source or credentials through provider calls or logs;
- parallel agents colliding in a worktree or shared build directory;
- claiming causal performance from a headline metric;
- treating one model’s confident prose as architectural consensus.

## Controls

- deny-by-default permissions and at most three write modules;
- protected paths and separate contract-change packets;
- argv-based locked commands and independent result parsing;
- content-addressed artifacts and append-only attempts;
- cross-provider verification for promotion-critical work;
- fresh SHA manifests, environment fingerprints, seeds, and tool versions;
- deterministic hard-break scheduling and resource locks;
- explicit human decisions for interfaces, waivers, conflicts, releases, and PPA.

Prompt injection in repository content, logs, or generated output is treated as untrusted data. Online adapters must not turn retrieved instructions into new permissions.
