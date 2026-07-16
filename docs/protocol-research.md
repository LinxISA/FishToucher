# Multi-agent 协议调研与取舍

调研目标不是选择一个大框架，而是提取 FishToucher 真正需要的最小协议。

## 可借用的设计

| 来源 | 可借用 | FishToucher 映射 | 不采用 |
|---|---|---|---|
| [A2A 1.0 specification](https://github.com/a2aproject/A2A/blob/main/docs/specification.md) | Agent Card、Task 生命周期、Message、Artifact、引用 | Role Card、assignment 状态、artifact hash、result references | 当前不实现远程 A2A server、streaming 或 push notification |
| [Microsoft AutoGen Core runtime](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/agent-and-agent-runtime.html) | runtime 管理 agent 身份、生命周期和消息投递 | 管家持有 handle，执行 start/follow-up/wait/cancel | 不使用自由 peer-to-peer group chat |
| [OpenAI Agents SDK handoffs](https://openai.github.io/openai-agents-js/guides/handoffs/) 与 [tracing](https://openai.github.io/openai-agents-python/tracing/) | 显式 handoff、generation/tool/handoff trace | 管家路由结果；调用 receipt 绑定 provider、hash、token、tool actions | raw trace 不进入 mailbox，不让 provider trace 充当产品证据 |
| [LangChain handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs) | supervisor 将控制权交给专岗 | 管家是唯一 supervisor，跨岗信息由引用传递 | 子 Agent 不直接抢占对话或自由转交人类界面 |
| [Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md) | custom agent、不同 model/reasoning、权限继承、spawn/steer/wait/stop、默认一层嵌套 | `codex` driver 和项目岗位 prompt | 原生 spawn 不是通用第三方 provider RPC；DeepSeek 不伪装成 Codex native child |

## 最终决策

1. 人类只面对管家；管家先 takeover，再 spawn。
2. 岗位是 LinxISA 组织职责，provider 只是 driver。
3. 一个 assignment 只有一个 owner、一个 target、明确修改范围和完成条件。
4. 普通 durable exchange 只有 `assignment → result → verdict`；需要人类时才 `escalation`。
5. Codex 和 DeepSeek 共用任务生命周期与日志格式，不共用未经证明的 provider-specific spawn API。
6. Codex 的原生默认是 `max_depth=1`；FishToucher 仅在明确授权 Senior Coder→Specialist Coder 时允许 depth 2，其他任务保持一层。
7. 流程审计与效率优化在产品 verdict 之后运行，不能修改已接受证据或 gate。

## 为什么不直接依赖框架

FishToucher 当前是 protocol prototype。引入 A2A/AutoGen/LangGraph SDK 会增加依赖、运行时和迁移成本，却不能替代 LinxISA 的 Role Card、first-red、SHA provenance 和模块权限。等真正需要远程 agent discovery、持久 checkpoint 或分布式 runtime 时，再按 capability class 添加 adapter，而不是重写岗位协议。
