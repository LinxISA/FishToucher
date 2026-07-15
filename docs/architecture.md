# Architecture

FishToucher separates nondeterministic reasoning from deterministic control. Agents propose patches and interpretations; the coordinator validates scope, executes locked commands, hashes artifacts, and computes gate status.

```mermaid
flowchart TB
    H["Human SE<br/>interfaces · waivers · promotion"]
    C["FishToucher coordinator<br/>policy · state · budgets · locks"]
    G["GPT pool<br/>architecture · planning · diagnosis · review"]
    D["DeepSeek pool<br/>bounded implementation · tests · regressions"]
    V["Independent gate engine<br/>commands · hashes · verdicts"]
    L["LinxISA canonical repos and runners"]
    E["Append-only evidence packets"]

    H --> C
    C --> G
    C --> D
    G --> C
    D --> C
    C --> L
    L --> V
    V --> E
    E --> C
    C --> H
```

## Two nested feedback structures

FishToucher uses two different kinds of loop:

1. The **task control loop** authorizes one action, observes the environment, verifies evidence, and retries or escalates.
2. The **engineering loops** let software, architecture, and hardware progress at different cadences behind versioned interfaces.

```mermaid
flowchart LR
    subgraph SW["Software · fast"]
      SW1["Framework / operators"] --> SW2["Compiler"] --> SW3["ISA + functional model"]
    end
    subgraph AR["Architecture · medium"]
      AR1["ISA + functional oracle"] --> AR2["CA model"] --> AR3["Counters + causal performance"]
    end
    subgraph HW["Hardware · slow"]
      HW1["RTL"] --> HW2["UT / IT / ST"] --> HW3["Correlation + PPA"]
    end
    SW3 -- "versioned ISA / ABI / ELF / trace" --> AR1
    AR3 -- "microarchitecture + counter contract" --> HW1
    HW3 -- "timing / power / area feedback" --> AR2
    AR1 -- "functional oracle" --> HW2
```

## Deterministic plan, nondeterministic workers

A flow document compiles into an ordered plan. Ready work sorts by priority and packet ID. Concurrency is permitted only for disjoint write scopes and output directories. Provider output is never used as a gate result.

Future online adapters should implement a provider-neutral request/result protocol and load exact GPT and DeepSeek model names from environment configuration. Credentials must never enter flow documents, prompts, plans, logs, or evidence.

## Persistence

Runtime state should live outside the LinxISA checkout or in an explicitly approved location. LinxISA-generated workload artifacts remain under `workloads/generated/<run-id>/`. Each attempt gets a content-addressed evidence packet; failed attempts remain available for replay and audit.
