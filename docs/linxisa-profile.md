# LinxISA Integration Profile

FishToucher is an external orchestrator. It does not add a random top-level folder to `/Users/zhoubot/linx-isa`, create inter-leaf submodules, or route work through shadow checkouts.

## Canonical inputs

The profile imports LinxISA’s owner manifest, waivers, gate registry, benchmark hard-break flow, and AI workload flow. If those files change, FishToucher invalidates the compiled plan. The Superproject Bring-up Observer starts from:

- `docs/bringup/BENCHMARK_QEMU_LINUX_FLOW.md`;
- `docs/bringup/benchmark_qemu_linux_flow.json`;
- `tools/bringup/run_benchmark_linux_flow.py`;
- `docs/bringup/agent_runs/manifest.yaml`.

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

The profile never embeds a "current blocker" snapshot. During takeover, the steward reads a fresh machine-readable runner report, records its exact revision and timestamp, and then selects the first red stage. `examples/linxisa-routing-example.json` demonstrates routing only and is never evidence.

## Ownership and changes

Ordinary assignments write at most three modules. A leaf defect is fixed, tested, and landed in the leaf repository first. Integration then updates only the intended gitlink and reruns cross-repository closure. The superproject must not hide leaf changes or unrelated repins.

Parallel agents need disjoint modules and output directories. In particular, QEMU/AVS jobs must not share mutable build outputs.

## Evidence and artifacts

Every run records the complete submodule SHA manifest, lane, profile, exact commands, dirty-tree state, logs, artifacts, and hashes. Generated workload artifacts go under `workloads/generated/<run-id>/`; sibling directories such as `workloads/generated-*` are invalid.

The canonical JSON report is authoritative. A generated Markdown page may summarize it but cannot override it. Stale evidence, compile-only evidence presented as runtime closure, and QEMU results presented as CA/RTL/PPA closure are rejected.
