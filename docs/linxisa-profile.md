# LinxISA Integration Profile

FishToucher is an external orchestrator. It does not add a random top-level folder to `/Users/zhoubot/linx-isa`, create inter-leaf submodules, or route work through shadow checkouts.

## Canonical inputs

The profile imports LinxISA’s owner manifest, waivers, gate registry, benchmark hard-break flow, and AI workload flow. If those files change, FishToucher invalidates the compiled plan.

## Hard-break behavior

The benchmark/QEMU/Linux path follows the canonical machine-readable order. A representative order is:

```text
source-contract
→ compiler-contract
→ qemu-contract
→ tsvc-qemu-hardbreak
→ linux-userspace-entry
→ libc-hosted-runtime
→ specint-fast-gate
→ full-benchmarks
```

The runner’s current JSON, not this prose, defines the exact profile-specific order. FishToucher stops at the first red stage in the same lane and profile.

As of 2026-07-15, the strict PR lane reaches a TSVC QEMU runtime timeout. A separate BusyBox full-OS regression remains localized around `finish_task_switch` / `FRET.ST` but is off that PR stop path. FishToucher records both without allowing the downstream issue to replace the first hard break.

## Ownership and changes

Ordinary packets write at most three modules. A leaf defect is fixed, tested, and landed in the leaf repository first. Integration then updates only the intended gitlink and reruns cross-repository closure. The superproject must not hide leaf changes or unrelated repins.

Parallel agents need disjoint modules and output directories. In particular, QEMU/AVS jobs must not share mutable build outputs.

## Evidence and artifacts

Every run records the complete submodule SHA manifest, lane, profile, exact commands, dirty-tree state, logs, artifacts, and hashes. Generated workload artifacts go under `workloads/generated/<run-id>/`; sibling directories such as `workloads/generated-*` are invalid.

The canonical JSON report is authoritative. A generated Markdown page may summarize it but cannot override it. Stale evidence, compile-only evidence presented as runtime closure, and QEMU results presented as CA/RTL/PPA closure are rejected.
