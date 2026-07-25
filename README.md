# Multi-Agent Error Propagation & Verification Resilience

This repository contains the official implementation, datasets, traces, and analytical reports for the **SISTER Program** research paper on **Multi-Agent Error Propagation and Verification Resilience**.

The project investigates how errors introduced at different stages of a cooperative multi-agent LLM pipeline (Planning/Decomposer vs. Execution/Solver) propagate to the final answer, how models naturally absorb errors, and how verifier prompting strategies (**Direct**, **Chain-of-Thought**, and **Rubric**) mitigate systemic failure.

---

## 🌟 Key Research Discoveries

1. **Error Absorption at Stage Boundaries:**
   * LLM Solvers act as active semantic filters: **over 90% of plan-stage errors** ($C_1$) are naturally absorbed or corrected by the Solver without needing a verifier.
   * Execution-stage errors ($C_2$) are significantly more lethal, propagating at **11.2%–12.9%** when a verifier is present, and exploding to **24.8%–27.3%** when the verifier is ablated ($D_2$).

2. **Verifier Prompt Strategy Impact (RQ2):**
   * **Direct Verifiers Suffer from Bad Corrections:** Baseline direct verifiers make calculation slips while attempting to correct flagged errors, yielding a correction precision of only **66.0%**.
   * **CoT & Rubric Eliminate Bad Corrections:** Scratchpad reasoning (**CoT**) and 4-point checklists (**Rubric**) increase verifier correction precision to **95.9%–100.0%**, reducing net solver error propagation from **12.9% down to 1.4%** (a 9.2x drop on Claude).

3. **Cross-Model Validation:**
   * Experiments evaluated on both a state-of-the-art closed model (**Claude Sonnet 4.6**) and a leading open-weights model (**Qwen 2.5 72B Instruct**) on **GSM-Hard** ($n=200$), proving these error dynamics are universal properties of LLM pipelines.

---

## 📁 Repository Architecture

```text
├── configs/                          # YAML experiment configuration files
│   ├── experiment.yaml               # Claude Sonnet Direct Baseline
│   ├── experiment_cot.yaml           # Claude Sonnet Chain-of-Thought
│   ├── experiment_rubric.yaml        # Claude Sonnet Rubric Checklist
│   ├── replication_deepinfra.yaml    # Qwen 2.5 72B Direct Baseline
│   ├── replication_qwen_cot.yaml     # Qwen 2.5 72B Chain-of-Thought
│   └── replication_qwen_rubric.yaml  # Qwen 2.5 72B Rubric Checklist
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
├── .env.example                      # Template for API credentials
└── README.md                         # Project documentation
```

---

## 🛠️ Setup & Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/multiagent-error-propagation.git
cd multiagent-error-propagation
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPINFRA_API_KEY=your_deepinfra_api_key_here
```

---

## 🚀 Reproducing the Experiments

### 1. Run Claude Sonnet 4.6 Experiments
To run the full 200-problem GSM-Hard grid across verifier strategies:

```bash
# Direct Strategy (Baseline)
python -m src.runner --config configs/experiment.yaml --overwrite

# Chain-of-Thought (CoT) Strategy
python -m src.runner --config configs/experiment_cot.yaml --conditions B C1 C2 --overwrite

# Rubric Strategy
python -m src.runner --config configs/experiment_rubric.yaml --conditions B C1 C2 --overwrite
```

### 2. Run Qwen 2.5 72B Instruct Experiments
To run the replication on Qwen 2.5 via DeepInfra:

```bash
# Direct Strategy (Baseline)
python -m src.runner --config configs/replication_deepinfra.yaml --overwrite

# Chain-of-Thought (CoT) Strategy
python -m src.runner --config configs/replication_qwen_cot.yaml --conditions B C1 C2 --overwrite

# Rubric Strategy
python -m src.runner --config configs/replication_qwen_rubric.yaml --conditions B C1 C2 --overwrite
```

---

## 📊 Generating Statistical Reports

All analysis scripts print formatted results to stdout and automatically save/overwrite report files:

### 1. General Error Propagation Report (RQ1)
```bash
python -m src.stats --traces results/traces
```
*Generates and saves `results/rq1_report.txt`.*

### 2. Verifier Prompt Strategy Master Report (RQ2)
```bash
python -m src.analyze_rq2_verifier_strategies
```
*Generates and saves `results/rq2_report.txt` and `results/rq2_verifier_strategies_report.md`.*

### 3. Cross-Model Comparison Report (Claude vs. Qwen)
```bash
python -m src.compare_models
```
*Generates and saves `results/model_comparison_report.md`.*

---

## 🧪 Running Unit Tests
To verify pipeline integrity, fault injectors, and verifier parsing:
```bash
python -m unittest tests/test_harness.py
```

---

## 📜 Citation & License
Developed as part of the SISTER Research Program. Released under the MIT License.
