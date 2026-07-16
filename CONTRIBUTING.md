# Contributing

FishToucher is still a prototype. Breaking cleanup is preferred over compatibility code.

1. Start from `docs/standard.md` and the Role Cards in `config/linxisa.example.json`.
2. Add regression tests before behavior-preserving cleanup.
3. Keep roles and providers independent; provider-specific behavior belongs behind a driver.
4. Do not add dependencies without explicit approval.
5. Do not persist credentials, full secrets, or raw provider content in committed fixtures.
6. Preserve independent review, scope intersection, hard-break ordering, and evidence honesty.
7. Prove a new role can load without changes to the runtime validator.

Before submitting:

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m fishtoucher.cli validate config/linxisa.example.json
PYTHONPATH=src python3 -m fishtoucher.cli mailbox examples/runs/harness-loop-001/mailbox.jsonl
PYTHONPATH=src python3 -m fishtoucher.cli evidence examples/evidence.pass.json
```

Use the LinxISA Lore Commit Protocol and report verification gaps honestly.
