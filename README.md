# FishToucher 摸鱼

**An evidence-first multi-agent harness standard for LinxISA NPU development.**

FishToucher coordinates GPT and DeepSeek agents across three independently paced engineering loops:

- **Software:** programming framework → compiler → ISA → functional model
- **Architecture:** ISA → functional model → cycle-accurate model
- **Hardware:** microarchitecture/RTL → UT/IT/ST → synthesis and P&R

The name is playful; the contract is not. Agents can propose, implement, test, and review. Only validators can derive gate status, and only a human can freeze cross-repository interfaces, approve waivers, resolve model conflicts, or promote a release.

## Why FishToucher?

A capable agent can write code quickly and still “finish” by weakening a test, changing a reference output, swallowing an exit code, or reporting a stale green run. FishToucher treats this as a systems problem:

```text
propose → authorize → execute → collect evidence → verify → promote or escalate
```

It binds each task to exact repository revisions, write scopes, gates, budgets, artifacts, and an independent verifier. Markdown summaries are views; fresh machine-readable reports are truth.

## Quick start

FishToucher currently ships the v1alpha1 standard, an executable validator, a deterministic plan renderer, LinxISA examples, and role prompts. It does not call provider APIs or mutate LinxISA by itself.

```bash
git clone https://github.com/LinxISA/FishToucher.git
cd FishToucher

PYTHONPATH=src python3 -m fishtoucher.cli validate config/linxisa.example.json
PYTHONPATH=src python3 -m fishtoucher.cli plan config/linxisa.example.json
PYTHONPATH=src python3 -m fishtoucher.cli evidence examples/evidence.pass.json
PYTHONPATH=src python3 -m fishtoucher.cli mailbox examples/runs/software-loop-001/mailbox.jsonl
PYTHONPATH=src python3 -m fishtoucher.cli invocation examples/runs/software-loop-002/invocation-002.json
python3 -m unittest discover -s tests -v
```

Expected plan:

```text
[software] ...
  1. software_contract: gpt_architect -> contract_integrity -> deepseek_verifier
  2. software_implementation: deepseek_executor -> software_functional -> gpt_verifier

[architecture] ...
[hardware] ...
```

## Core contracts

1. **Human authority is explicit.** Agents do not make architecture freezes, waivers, release decisions, or PPA claims.
2. **GPT and DeepSeek have different default lanes.** GPT handles architecture, decomposition, cross-layer diagnosis, and independent review. DeepSeek handles bounded implementation, tests, regressions, and mechanical work.
3. **The implementer never self-verifies.** High-value stages use a verifier from the other provider.
4. **The first red hard break owns the lane.** Downstream work stops; timeout, crash, skipped, and missing evidence are not pass.
5. **Evidence is replayable.** A gate record includes command, working directory, time, status, artifact hashes, SHA manifest, dirty state, and agent/prompt identity. Online provider calls add a versioned receipt that hash-binds the authorized packet to the exact request and response byte streams.
6. **LinxISA remains authoritative.** FishToucher consumes its canonical manifests and runners; it does not duplicate ISA truth or invent alternate source trees.
7. **Cross-loop changes invalidate dependent evidence.** ISA, ABI, ELF, trace, benchmark, counter, or microarchitecture contract changes require an impact matrix and human decision.

## LinxISA profile

The example profile reads these canonical inputs from the LinxISA superproject:

- `docs/bringup/agent_runs/manifest.yaml`
- `docs/bringup/agent_runs/waivers.yaml`
- `docs/bringup/benchmark_qemu_linux_flow.json`
- `docs/bringup/ai_workload_bringup_flow.json`

FishToucher must preserve LinxISA’s profile-aware hard-break order. The included current-state fixture records the routing distinction on 2026-07-15: the strict PR lane first stops at the TSVC QEMU timeout; the BusyBox `finish_task_switch` / `FRET.ST` regression remains real but is off that PR stop path. The fixture is not closure evidence and must be replaced by a fresh runner report before use.

## Documentation

- [Normative standard](docs/standard.md)
- [Architecture and data flow](docs/architecture.md)
- [Agent communication SOP](docs/agent-communication-sop.md)
- [LinxISA integration profile](docs/linxisa-profile.md)
- [Threat model](docs/threat-model.md)
- [Contributing](CONTRIBUTING.md)

## Status

`v1alpha1` defines and validates flow, evidence, invocation-receipt, agent-message, and mailbox contracts. The [first software-loop iteration](examples/runs/software-loop-001/) demonstrates the durable handoff protocol with a simulated executor provider. The [second iteration](examples/runs/software-loop-002/) uses a paid DeepSeek V4 Pro executor behind a Codex coordinator, preserves a rejected first result, and closes on an independently accepted repair with two hash-bound invocation receipts. FishToucher still does not ship credentials or a provider adapter, and unsigned receipts do not prove remote identity. Worktree isolation and coordinator-owned append-only storage remain future work; the repository does not claim that an NPU, RTL closure, or tapeout has been completed.

## License

Apache-2.0. See [LICENSE](LICENSE).
