# FishToucher Three-Loop Standard

## 1. Scope

This document defines the normative control, evidence, and promotion contract for multi-agent development of the LinxISA NPU stack. The keywords **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

FishToucher coordinates work. LinxISA specifications, code, tests, canonical manifests, and fresh runner reports remain the engineering source of truth.

## 2. Control loop

Every agent action MUST follow this state transition:

```text
DRAFT → AUTHORIZED → RUNNING → VERIFYING → PASS
                                  ├──────→ FAIL
                                  ├──────→ BLOCKED
                                  └──────→ ESCALATED
```

An agent MAY propose a transition. Only the coordinator MAY authorize tools and write state. Only a deterministic gate evaluator MAY produce `PASS`.

Every work packet MUST bind:

- intent and explicit non-goals;
- loop, stage, owner, and independent verifier;
- repository and submodule SHAs;
- read, write, protected, and network scopes;
- required inputs, outputs, gates, and Definition of Done;
- time, token, tool-call, attempt, diff-size, and storage budgets;
- retry and human-escalation rules.

Attempts MUST be append-only. A retry MUST NOT overwrite failed evidence.

## 3. Human authority

The human System Engineer is the final authority for:

- target architecture and version boundaries;
- ISA, ABI, privilege, memory-model, ELF, trace, and public-interface freezes;
- cross-module conflict resolution;
- waivers and exceptions;
- release, performance, and PPA claims.

Agents MAY prepare decision records and alternatives. They MUST stop before applying a human-only decision.

## 4. Model routing

Exact model names belong in deployment configuration, never in the standard.

The GPT pool SHOULD own high-context architecture analysis, task decomposition, design review, and cross-layer diagnosis. The DeepSeek pool SHOULD own bounded module implementation, test completion, regression repair, and mechanical work.

The implementation provider MUST differ from the independent verification provider for promotion-critical work. A disagreement MUST produce a decision record for the human; agents MUST NOT resolve it by majority vote.

## 5. Bootstrap ladder

Before the steady-state loops can claim maturity, the system MUST establish these ordered executable contracts:

1. **ISA ↔ functional model:** positive, boundary, exception, and randomized instruction tests with comparable register, memory, exception, and commit traces.
2. **Compiler → ISA → functional model:** target/ABI/codegen/assembly/object/link execution at required optimization levels.
3. **C runtime → compiler → ISA → functional model:** startup, runtime support, linker/loader, syscall ABI, TLS, atomics, signals, and file interfaces.
4. **Linux/BusyBox/toolchain → system model:** boot, init, rootfs, shell, and ordinary ELF execution with privilege, MMU, interrupt, timer, and device behavior.

A later stage MUST NOT substitute for a missing earlier contract.

## 6. The three loops

### 6.1 Software loop

```text
programming framework → compiler → ISA/ABI → functional model
```

The software loop MUST optimize for fast functional feedback. Promotion evidence MUST include the programming/API contract, compiler change, ISA and ABI versions, ELF, disassembly and relocation sidecars when applicable, functional trace or digest, and regression inventory.

A successful compile MUST NOT be reported as runtime closure. A QEMU pass MUST NOT imply cycle-model, RTL, or PPA closure.

### 6.2 Architecture loop

```text
frozen ISA → functional oracle → cycle-accurate model → benchmark → decision
```

Correctness MUST pass before performance is evaluated. Every claimed improvement MUST identify a causal mechanism through instruction count, IPC, stalls, queue occupancy, bandwidth, utilization, latency, or another declared counter.

Promotion evidence MUST include benchmark and seed manifests, model configuration, baseline, functional differential, counters/traces, performance delta, causal explanation, and sensitivity results. An unexplained improvement MUST fail review.

### 6.3 Hardware loop

```text
microarchitecture RTL → UT → IT → ST → correlation → synthesis/P&R
```

UT MUST cover local module behavior. IT MUST cover interfaces, handshakes, and timing relationships. ST MUST run full programs or system scenarios. Functional results MUST be compared with the functional model, and cycle/counter behavior MUST be correlated with the CA model.

PPA evidence MUST identify tools, versions, process/corner, constraints, clocks, seeds, and raw timing, area, power, congestion, and critical-path reports.

## 7. Cross-loop contracts

Only versioned artifacts SHOULD cross loop boundaries:

- ISA and ABI versions;
- calling convention, ELF, and relocation contracts;
- trace and performance-counter schemas;
- benchmark and seed manifests;
- functional digests;
- microarchitecture configuration;
- repository and toolchain SHA manifests.

Changing a shared contract MUST generate an impact matrix, invalidate dependent cached evidence, schedule affected cross-loop gates, and require a human decision.

## 8. Gate and evidence semantics

Gate status is one of `pass`, `fail`, `timeout`, `crash`, `skipped`, or `waived`. Only `pass` satisfies an unwaived required gate. `timeout`, `crash`, `skipped`, and missing evidence MUST NOT be normalized to pass.

Executable evidence MUST record:

- literal argument vector, working directory, and allowed environment;
- start/end times, timeout, and return code;
- stdout/stderr and output artifact hashes;
- test inventory, selection, reference origin, and random seeds;
- superproject and complete submodule SHA manifest;
- dirty-tree state, tool versions, and input hashes;
- actor provider/model, role, and prompt revision;
- independent reviewer verdict and proof boundary.

A Markdown status page MUST be treated as a generated view. Fresh machine-readable runner output wins on disagreement.

A waiver MUST be visibly `waived`, not green, and MUST include owner, issue, phase/lane/profile, rationale, human identity, and expiration.

## 9. Stop, retry, and escalation

Dependent stages MUST run sequentially. A loop MUST stop at its first red hard break. Independent owners MAY run concurrently only with disjoint write scopes, resource locks, and output directories.

Infrastructure failures MAY receive two bounded retries. A code failure MAY receive another attempt only when the hypothesis or failure signature changes. Repeating the same failure twice MUST escalate.

The harness MUST escalate on contract change, scope expansion, model disagreement, destructive operations, budget exhaustion, missing licensed tools, requested/expired waiver, or any improvement obtained by weakening coverage.

## 10. Anti-gaming requirements

An implementation packet MUST NOT:

- delete or disable a failing test;
- change its oracle, reference output, gate definition, or threshold;
- add `|| true`, swallow a return code, or pass by printing a token;
- shrink a required suite or hide an unsupported case;
- use stale binaries or evidence from another SHA manifest;
- overwrite a prior failure packet;
- modify more than three LinxISA modules without explicit expansion.

Tests may change only when the packet explicitly owns them. Oracle, gate, baseline, and waiver changes require a separate human-reviewed contract packet.

## 11. Completion

A task is complete only when all required unwaived gates pass, evidence hashes verify, the independent reviewer accepts the bounded claim, the SHA manifest is reproducible, unresolved issues are recorded, and each participating module emits `skill-evolve: update ...` or `skill-evolve: no-update ...`.
