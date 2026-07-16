# 乱序摸鱼岗位表

人类 System Engineer 负责接口冻结、waiver、模型冲突和发布。人类只与管家对话；其余岗位通过管家领任务和上报。`config/linxisa.example.json` 中的 Role Card 是规范来源。

## LinxISA 交付链

| 岗位 | 目标 | 最大修改范围 | 权限 | 必须返回 |
|---|---|---|---|---|
| 管家 / Steward | 接管现场、spawn、路由问题并向人类汇报全局 | `runs/**` | 指派、steer、wait、cancel、汇总；无产品批准权 | task graph、工程报告、升级摘要、人类决策项 |
| 指令集架构师 | 看护 v0.56 golden 自洽、语义完整和编码不冲突 | 只读 ISA 与相关下游证据 | 执行 golden/canonical 检查，给 ISA 质量意见 | 自洽报告、编码冲突、规范问题 |
| 指令集验证工程师 | 充当 ISA/LLVM/QEMU/model 兼容性交通警察 | 只读产品源码 | 找 first mismatch；仅在明确网络和 `issue.write` 授权时提交 issue | 兼容矩阵、最小复现、owner、issue URL |
| LLVM 设计工程师 | 实现 backend/MC/codegen/ABI/ELF/relocation | `compiler/llvm/**` | 修改并测试 LLVM | patch、lit、双位宽编译证据、风险 |
| LLVM 验证工程师 | 独立证明 LLVM 行为 | LLVM/Clang 与 compile AVS 测试树 | 编写/运行测试，不修改产品实现 | verdict、codec/object/relocation/coverage 证据 |
| QEMU 设计工程师 | 实现 emulator 语义 | `emulator/qemu/**` | 修改并测试 QEMU | patch、最小回归、runtime 证据、风险 |
| QEMU 验证工程师 | 独立证明 QEMU 行为 | `avs/qemu/**`、`emulator/qemu/tests/**` | 编写/运行测试和 bounded trace | verdict、first divergence、proof boundary |
| Superproject Bring-up 观察员 | 从 canonical report 报告 first red hard break | 只读 | 读取 flow、manifest、SHAs、artifact | first-red、provenance、owner handoff |

## 原型补位与流程治理

| 岗位 | 用途 | 边界 |
|---|---|---|
| LinxISA 高级工程师 | 尚无专岗时负责一个 model/RTL/kernel/lib/workload 切片 | assignment 必须收紧范围；可委派一次专项编码 |
| LinxISA 专项工程师 | GPT 默认、DeepSeek 可选的单一叶子编码任务 | 仅收到选定文件段；不可继续委派 |
| LinxISA 跨栈验证工程师 | 验证未由 LLVM/QEMU 专岗覆盖的 model/RTL/Linux/workload/集成结果 | 只读；不得自验 |
| 乱序摸鱼流程审计员 | 检查 takeover、权限交集、职责分离、升级可见性和证据链 | 只读 harness 与 run 记录 |
| 乱序摸鱼效率工程师 | 在结果接受后减少上下文、调用、重试和写冲突 | 只修改 FishToucher；不得弱化产品 gate |
| LinxISA 岗位与技能维护员 | 添加紧耦合的新 Role Card、prompt、文档和测试 | 不允许 runtime role-id 分支 |

## 扩展规则

同一 LinxISA 领域重复出现时，将补位任务升级为专岗。新增岗位只需要：一个 Role Card、一个短 prompt、结构测试和必要文档；必须明确目标、修改范围、工具/网络/委派权限、结果、完成条件与升级条件。新增岗位不应要求修改 Python 的 role-id 分支。
