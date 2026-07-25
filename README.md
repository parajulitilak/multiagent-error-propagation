# Do Errors Compound? Measuring Error Propagation in Multi-Agent LLM Pipelines

Controlled fault-injection study of error propagation in LLM agent pipelines
(Decomposer → Solver → Verifier), with a single-agent baseline, verifier
ablation, and paired statistical testing.

**SISTER 2026 · AI/ML Track (Dubai CS Society + Delta Rising Foundation)**
Author: Tilak Parajuli

## Research question
When LLM agents are chained into a pipeline, do mistakes made by early agents
get caught, corrected, or amplified by later agents?

## Design
| Condition | Description |
|---|---|
| A | Single agent, end-to-end (baseline) |
| B | Clean 3-agent pipeline |
| C1 / C2 | Pipeline + controlled fault injected at Decomposer / Solver |
| D1 / D2 | C1 / C2 with Verifier removed (ablation) |

Same fixed problem sample for every condition (paired design). Fault
injection is scripted (`src/injection.py`), so ground truth about where each
failure started is known.

## Reproduce in 3 commands
```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY (or OPENAI_API_KEY)
python -m src.runner --config configs/experiment.yaml && python -m src.stats
```
Smoke-test the harness and run the unit tests without spending API credits:
```bash
python -m src.runner --config configs/experiment.yaml --dry-run
python -m unittest discover -s tests
```

## Repo layout
```
configs/     experiment parameters (models, seeds, n) - nothing hardcoded
src/         pipeline.py · injection.py · runner.py · stats.py
tests/       unit tests for scoring, extraction, and injection
results/     JSONL traces, released with the repo (the study's dataset)
paper/       LaTeX source (mirrors Overleaf)
```

## Reproducibility contract
Fixed sample seed, fixed injection seed, temperature 0 for main runs, exact
model string pinned in config, all prompts in `src/pipeline.py`, every number
in the paper regenerable via `python -m src.stats`.

## License
MIT
