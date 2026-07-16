# FishToucher Agent Contract

- Treat `docs/standard.md` as normative.
- FishToucher is one prototype contract: `fishtoucher.prototype`. Do not add numbered protocol variants or compatibility paths.
- Roles are configuration data. Never add runtime branches for a role id or provider name.
- Keep provider model names configurable and credentials in environment-backed deployment configuration.
- The default execution path is GPT through the `codex` driver. DeepSeek is an optional driver for `specialist-coder`, not a job title.
- The repository and package name remain `FishToucher`; the Chinese product name is `乱序摸鱼`.
- The `steward` is the only routine human-facing role. It owns spawning, routing, layered escalation, and whole-project reporting, but no human-exclusive decision.
- LinxISA domain roles must use canonical scopes and gates: ISA golden, LLVM, QEMU, their verification trees, and superproject first-red observation. Prefer a domain job over a generic company title.
- Every assignment declares one named assignee, target, base revision, context sections, authority, protected paths, commands, budgets, completion conditions, and escalation rules.
- Effective authority is the intersection of Role Card, assignment, and runtime sandbox. No layer may widen another.
- An implementer must not approve its own result. A rejection must include evidence, a concrete fix, write scope, and required commands.
- Do not weaken gates, tests, oracles, baselines, or waivers in an implementation change.
- Persist only `assignment`, `result`, `verdict`, and exceptional `escalation` records. Internal delegated calls do not create mailbox chatter; issue URLs use result `references`.
- Store invocation logs as `<name>-<role>-req.json` and `<name>-<role>-resp.json`, mode `0600`, create-once, with hashes in the receipt.
- Add a new role by extending configuration, prompt documentation, and tests; existing runtime code must continue to work unchanged.
- A new steward must complete `prompts/steward.md` takeover and publish the first full report before spawning.
- Run unit tests, flow/evidence/mailbox/invocation validation, schema JSON parsing, Ruff, compileall, and the residual-string audit before reporting completion.
- Every commit follows the LinxISA Lore Commit Protocol.
