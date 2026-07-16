# 乱序摸鱼（FishToucher）

**乱序摸鱼**是 FishToucher 仓库的中文名。它是一个面向 LinxISA NPU 大型系统开发的多 Agent harness 原型：描述岗位、权限、交付、验证、升级和人类决策点，但当前不直接启动 Agent 或调用付费模型。

它协调三条独立推进的循环：

- 软件：编程框架 → LLVM → ISA/ABI → QEMU/功能模型 → Linux/workloads
- 架构：冻结 ISA → 功能金模 → cycle-accurate model → 相关性证据
- 硬件：微架构/RTL → UT/IT/ST → model/RTL 相关性 → 发布证据

正常通信只有三条记录：

```text
assignment → result → verdict
```

## 管家入口

人类只与 `steward`（管家）对话。管家负责接管现场、拆任务、spawn、监督、路由每层问题，并生成完整工程报告；接口冻结、waiver、模型冲突和发布仍由人类决定。

在新的 Codex task 中打开 [`prompts/steward.md`](prompts/steward.md)。新管家必须先完成 takeover 清单并输出第一份全量报告，之后才能 spawn：

```text
已接管“乱序摸鱼”管家角色。
```

## LinxISA 岗位

- `isa-architect`：看护 v0.56 golden ISA 的自洽性、语义与编码空间。
- `isa-verification-engineer`：ISA/LLVM/QEMU/model 兼容性交通警察；在授权时提交可复现 issue。
- `llvm-designer` / `llvm-verification-engineer`：LLVM 实现与独立验证。
- `qemu-designer` / `qemu-verification-engineer`：QEMU 实现与独立验证。
- `superproject-bringup-observer`：只读观察 canonical flow、SHA 和 first red hard break。
- `senior-coder` / `specialist-coder`：尚无专岗时的 LinxISA GPT 实现岗；专项岗可选 DeepSeek driver。
- `cross-stack-verification-engineer`：验证 model、RTL、kernel、workload 和集成结果。
- `harness-auditor` / `harness-efficiency-engineer`：审计流程与度量优化。
- `role-skill-curator`：按配置扩展新的 LinxISA 岗位和技能，不在 runtime 写 role-id 分支。

规范 Role Card 位于 [`config/linxisa.example.json`](config/linxisa.example.json)。每个岗位都声明目标、修改范围、工具/网络/委派权限、输入、结果、完成条件和升级条件。

## Provider 边界

岗位与模型 provider 分离：

- `codex` 是默认且已启用的 GPT driver。
- `deepseek` 是默认关闭的可选外部 driver，只用于明确授权的 `specialist-coder` 任务。
- `fake` 是确定性的测试替身。

Codex 原生 subagent 可以使用项目级 custom agent 和权限继承，但没有可移植的“每次 spawn 任意切换 provider”字段。DeepSeek 因而通过独立 driver 实现同一生命周期：`start → follow_up → wait → cancel`。详见[协议调研与取舍](docs/protocol-research.md)。

## 验证

```bash
PYTHONPATH=src python3 -m fishtoucher.cli validate config/linxisa.example.json
PYTHONPATH=src python3 -m fishtoucher.cli plan config/linxisa.example.json
PYTHONPATH=src python3 -m fishtoucher.cli role config/linxisa.example.json steward
PYTHONPATH=src python3 -m fishtoucher.cli route config/linxisa.example.json isa-verification-engineer
PYTHONPATH=src python3 -m fishtoucher.cli evidence examples/evidence.pass.json
PYTHONPATH=src python3 -m fishtoucher.cli invocation examples/invocation.pass.json
PYTHONPATH=src python3 -m fishtoucher.cli mailbox examples/runs/harness-loop-001/mailbox.jsonl
python3 -m unittest discover -s tests -v
```

这些是 harness contract tests：验证岗位注册、takeover prompt、权限边界、消息、driver 路由和三循环拓扑。它们不会 spawn Agent、调用 provider、提交 issue 或运行 LinxISA 性能测试。原型阶段保留这类测试是必要的，因为它们防止岗位扩展时静默放宽权限或破坏接管协议。

参见[规范](docs/standard.md)、[管家 SOP](docs/steward-sop.md)、[岗位表](docs/roles.md)、[架构](docs/architecture.md)、[通信 SOP](docs/agent-communication-sop.md)和[效率策略](docs/harness-optimization.md)。
