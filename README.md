# Which Verifier Catches What? Mapping Error Severity to Verifier Strategy in Multi-Agent LLM Pipelines

Controlled fault-injection study of error propagation in LLM agent pipelines (Decomposer → Solver → Verifier), evaluating error severity levels (Mild, Moderate, Severe), stage boundaries (Planning vs. Execution), and verifier prompting strategies (Direct, Chain-of-Thought, Rubric) with paired statistical testing.

**SISTER 2026 · AI/ML Track (Dubai Computer Science Society & Delta Rising Foundation)**  
Authors: Tilak Parajuli, Johnny Kozman, Arushi Waddepalli

---

## 📖 Paper Abstract

Pipelines of specialized LLM agents (one plans, another executes, a third verifies) are now a default design for applied language-model systems. The design carries an implicit promise: later stages should absorb the mistakes of earlier ones. Whether they actually do is unresolved.

This repository implements a controlled fault-injection methodology adapted from software reliability engineering to corrupt single intermediate artifacts with known, scripted perturbations (`number_swap`, `operation_flip`, `semantic_logic_error`) and trace their fate through the pipeline. Faults are graded into three severity levels (Mild, Moderate, Severe), and the verification stage is evaluated under three prompt strategies (**Direct**, **Chain-of-Thought**, and **Rubric**). Across GSM-Hard ($n=200$) evaluated on both closed (**Claude Sonnet 4.6**) and open-weights (**Qwen 2.5 72B Instruct**) models, we compare single-agent baselines, clean multi-agent pipelines, early- and late-stage injections, and verifier-removed ablations.

---

## 🎯 Key Contributions

1. **Controlled Fault-Injection Methodology:** Scripted, reproducible perturbation operators graded into 3 severity levels.
2. **Quantitative Propagation & Absorption:** Empirical measurement of natural solver absorption vs. verifier defense across plan ($C_1$) and execution ($C_2$) stages.
3. **Causal Verifier Ablation:** Paired comparison ($C_2$ vs. $D_2$) isolating the exact causal contribution of the verification stage.
4. **Strategy-Level Map of Verification:** Performance, correction precision, and token trade-off mapping across Direct, Chain-of-Thought (CoT), and Rubric verifier prompts.
5. **Open Reproducibility:** Code, prompts, configuration, and complete JSONL trace logs sufficient to regenerate every number in the paper.

---

## 🔬 Experimental Design Matrix

| Condition | Description | Inject Stage | Verifier |
| :--- | :--- | :---: | :---: |
| **A** | Single-agent end-to-end baseline | N/A | OFF |
| **B** | Clean 3-agent pipeline (Decomposer → Solver → Verifier) | None | ON |
| **C1** | Pipeline + fault injected at Decomposer (Plan stage) | Decomposer ($C_1$) | ON |
| **C2** | Pipeline + fault injected at Solver (Execution stage) | Solver ($C_2$) | ON |
| **D1** | Decomposer injection with Verifier ablated | Decomposer ($D_1$) | OFF |
| **D2** | Solver injection with Verifier ablated | Solver ($D_2$) | OFF |

*Paired experimental design with fixed problem samples ($n=200$) across every condition.*

---

## 🌟 Key Research Discoveries

1. **Natural Error Absorption at Stage Boundaries:**
   * LLM Solvers act as active semantic filters: **over 90% of plan-stage errors** ($C_1$) are naturally absorbed or corrected by the Solver without needing a verifier.
   * Execution-stage errors ($C_2$) are lethal: turning OFF the verifier ($D_2$) more than doubles solver error propagation (Claude: 12.9% $\rightarrow$ 27.3%; Qwen: 11.2% $\rightarrow$ 24.8%).

2. **Verifier Prompt Strategy Impact (RQ2):**
   * **Direct Verifiers Suffer from Bad Corrections:** Baseline zero-shot verifiers make calculation slips during corrections, yielding only **66.0%** correction precision on Claude.
   * **CoT & Rubric Eliminate Bad Corrections:** Scratchpad reasoning (**CoT**) and 4-point checklists (**Rubric**) increase verifier correction precision to **95.9%–100.0%**, dropping solver error propagation from **12.9% down to 1.4%** (a 9.2x drop on Claude).

3. **Cross-Model Validation:**
   * Validated on both closed (**Claude Sonnet 4.6**) and open-weights (**Qwen 2.5 72B Instruct**) models, proving these error dynamics are fundamental architectural properties of multi-agent LLM systems.

---

## ⚡ Quickstart (3 Commands)

```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY and DEEPINFRA_API_KEY
python -m src.runner --config configs/experiment.yaml && python -m src.stats
```

Smoke-test the pipeline harness and run unit tests without spending API credits:
```bash
python -m src.runner --config configs/experiment.yaml --dry-run
python -m unittest discover -s tests
```

---

## 📁 Repository Architecture

```text
├── configs/                          # YAML experiment configuration files
│   ├── experiment.yaml               # Claude Sonnet Direct Baseline
│   ├── experiment_cot.yaml           # Claude Sonnet Chain-of-Thought
│   ├── experiment_rubric.yaml        # Claude Sonnet Rubric Checklist
│   ├── replication_deepinfra.yaml    # Qwen 2.5 72B Direct Baseline
│   ├── replication_qwen_cot.yaml     # Qwen 2.5 72B Chain-of-Thought
│   ├── replication_qwen_rubric.yaml  # Qwen 2.5 72B Rubric Checklist
│   └── pilot.yaml                    # Pilot run configuration
│
├── src/                              # Core python source code
│   ├── pipeline.py                   # Multi-agent execution loop & prompt definitions
│   ├── injection.py                  # Fault injectors (number_swap, operation_flip, semantic_logic_error)
│   ├── runner.py                     # Execution harness for paired condition grids
│   ├── stats.py                      # Statistical engine (Bootstrap CIs, McNemar, Logistic Regression)
│   ├── compare_models.py             # Side-by-side Claude vs. Qwen report generator
│   └── analyze_rq2_verifier_strategies.py # Master RQ2 prompt strategy analyzer
│
├── tests/                            # Automated unit & integration tests
│   └── test_harness.py               # 26 unit tests covering injectors, pipeline, & verifiers
│
├── results/                          # Complete experimental trace data & reports
│   ├── traces/                       # Claude Direct trace files (A.jsonl - D2.jsonl)
│   ├── traces_cot/                   # Claude CoT trace files
│   ├── traces_rubric/                # Claude Rubric trace files
│   ├── traces_replication_qwen25/    # Qwen 2.5 Direct trace files
│   ├── traces_replication_qwen25_cot/# Qwen 2.5 CoT trace files
│   ├── traces_replication_qwen25_rubric/# Qwen 2.5 Rubric trace files
│   ├── rq1_report.txt                # Auto-generated RQ1 text report
│   ├── rq2_report.txt                # Auto-generated RQ2 text report
│   ├── rq2_verifier_strategies_report.md # Comprehensive RQ2 Markdown Report
│   └── model_comparison_report.md    # Model comparison report
│
├── paper/                            # LaTeX paper source code & figure assets
│   ├── main.tex                      # Main paper draft
│   └── proposal.tex                  # Research proposal document
│
├── .env.example                      # Template for API credentials
└── README.md                         # Project documentation
```

---

## 🛠️ Detailed Setup & Execution

### 1. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in `.env`:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPINFRA_API_KEY=your_deepinfra_api_key_here
```

### 2. Run Experiments Across Prompt Strategies

```bash
# Claude Sonnet 4.6 (Direct, CoT, Rubric)
python -m src.runner --config configs/experiment.yaml --overwrite
python -m src.runner --config configs/experiment_cot.yaml --conditions B C1 C2 --overwrite
python -m src.runner --config configs/experiment_rubric.yaml --conditions B C1 C2 --overwrite

# Qwen 2.5 72B Instruct (Direct, CoT, Rubric)
python -m src.runner --config configs/replication_deepinfra.yaml --overwrite
python -m src.runner --config configs/replication_qwen_cot.yaml --conditions B C1 C2 --overwrite
python -m src.runner --config configs/replication_qwen_rubric.yaml --conditions B C1 C2 --overwrite
```

### 3. Generate Analysis Reports

```bash
# General Error Propagation (RQ1)
python -m src.stats --traces results/traces

# Verifier Prompt Strategies (RQ2)
python -m src.analyze_rq2_verifier_strategies

# Model Comparison (Claude vs. Qwen)
python -m src.compare_models
```

---

## 📜 Reproducibility Contract

Fixed sample seeds, fixed injection seeds, temperature 0 for main runs, exact model strings pinned in configs, all prompts in `src/pipeline.py`, and every number in the paper regenerable via the analysis scripts.

---

## 📜 License
Released under the MIT License.
