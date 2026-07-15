# FishToucher Agent Contract

- Treat `docs/standard.md` as normative.
- Preserve LinxISA as the source of technical truth; import canonical manifests and runner reports instead of duplicating them.
- Keep provider model names configurable. Never commit credentials.
- An implementer must not approve its own work.
- Do not weaken gates, tests, oracles, baselines, or waivers in an implementation change.
- Keep diffs bounded and add regression tests before behavior-preserving refactors.
- Run `python3 -m unittest discover -s tests -v`, flow validation, and evidence validation before reporting completion.
- Every commit message follows the LinxISA Lore Commit Protocol and records verification honestly.
