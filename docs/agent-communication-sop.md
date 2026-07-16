# Agent Communication SOP

## 1. Before every call

The steward resolves a Role Card and writes one assignment containing:

- unique agent name and role id;
- one target and explicit completion conditions;
- base revision and exact context line ranges;
- read, write, tool, network, and delegation authority;
- protected paths and required commands;
- context, call, time, and retry budgets;
- escalation conditions.

The steward rejects an invalid assignment before selecting a driver.

## 2. Call prompt

Every call prompt is limited to:

```text
Role: <job title and objective>
Target: <one concrete outcome>
Modify: <authorized paths only>
May use: <tools and delegate roles>
Must not: <protected paths and human-only decisions>
Done when: <acceptance and commands>
Return: <declared structured result>
```

Do not send biographies, motivational prose, repeated policy, entire files by default, or prior transcripts. Send exact sections, diff hunks, command failures, and required contracts.

## 3. Normal exchange

```text
assignment → result → verdict
```

There is no ACK, observation, progress, feedback, or provider-call mailbox record. A blocked worker returns a `result` with status `blocked`; a human-only decision uses `escalation`. Agents do not open-endedly chat with peers: the steward routes referenced records and preserves the originating layer.

## 4. Coding and delegation

`senior-coder` owns the final patch and may complete the task directly. When delegation is useful, it creates a smaller `specialist-coder` request using only authorized context. The specialist may be GPT or DeepSeek. The senior coder integrates the response and remains accountable for the result.

Every delegated call uses:

```text
<name>-<role>-req.json
<name>-<role>-resp.json
```

The result lists invocation hashes and status. It does not copy raw provider content into the mailbox.

The ISA Verification Engineer may file a cross-stack issue only when its effective permissions include both `issue.write` and network access. It returns the issue URL in result `references`; issue creation never counts as product-source modification.

## 5. Domain verification

The matching LLVM, QEMU, ISA, or cross-stack verifier reads the original assignment, candidate diff, protected paths, raw evidence, and fresh command output. It never accepts the implementer's summary as proof.

An `accept` verdict has no defects. A `reject` verdict includes at least one concrete defect with evidence, required fix, write scope, and commands. The next attempt receives a new assignment and message id.

## 6. Optimization wave

After a verdict, the Harness Efficiency Engineer may compute context bytes, delegated calls, retries, latency, accepted-call ratio, and context utilization. The Harness Auditor verifies authority and evidence preservation. After accepted evidence, the Role and Skill Curator may add Role Cards, prompts, or regression tests. These changes require an independent harness verdict.

## 7. Human reporting

The steward follows `docs/steward-sop.md`. Its first report covers all three loops, agent tree, layer issues, revisions/evidence, human decisions, and next work. Later updates are deltas, but unresolved escalations remain visible until closed.
