# Contributing

Open changes against `main`. Keep each change focused on one contract, validator, integration profile, or documentation concern.

Before submitting:

```bash
PYTHONPATH=src python3 -m fishtoucher.cli validate config/linxisa.example.json
PYTHONPATH=src python3 -m fishtoucher.cli evidence examples/evidence.pass.json
PYTHONPATH=src python3 -m fishtoucher.cli mailbox examples/runs/software-loop-001/mailbox.jsonl
python3 -m unittest discover -s tests -v
```

Changes to schemas, gate semantics, anti-cheat rules, or human authority require a rationale, compatibility impact, and adversarial test. Provider-specific code must remain behind a model-neutral adapter and must not persist credentials.

Commit messages follow the Lore protocol: lead with intent, explain constraints and rejected alternatives, and include `Tested:` and honest `Not-tested:` trailers.
