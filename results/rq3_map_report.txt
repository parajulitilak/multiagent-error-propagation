# RQ3 Master Error Map Report

# RQ3 Master Causal Error Map (Claude Sonnet 4.6)

Synthesizing interaction between Injection Stage, Verifier Ablation, Error Type, Severity, and Verifier Strategy.

## 1. Causal Error Defense Matrix by Error Type
| Error Type | Stage | Direct Prop % | CoT Prop % | Rubric Prop % | Ablated Prop % (No Verifier) | Causal Verifier Defense ($\Delta_{Direct}$) | Causal Verifier Defense ($\Delta_{CoT}$) | Causal Verifier Defense ($\Delta_{Rubric}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **number_swap** | Decomposer (Plan) | 7.3% (3/41) | 0.0% (0/57) | 0.0% (0/49) | 9.5% (4/42) | **+2.2%** | **+9.5%** | **+9.5%** |
| **number_swap** | Solver (Execution) | 8.7% (4/46) | 2.2% (1/46) | 2.2% (1/45) | 12.2% (6/49) | **+3.5%** | **+10.1%** | **+10.0%** |
| **operation_flip** | Decomposer (Plan) | 2.6% (1/38) | 2.9% (1/35) | 4.8% (2/42) | 2.4% (1/41) | -0.2% | -0.4% | -2.3% |
| **operation_flip** | Solver (Execution) | 0.0% (0/47) | 0.0% (0/48) | 2.1% (1/48) | 0.0% (0/50) | 0.0% | 0.0% | -2.1% |
| **semantic_logic_error** | Decomposer (Plan) | 5.0% (3/60) | 2.1% (1/47) | 2.0% (1/49) | 12.5% (7/56) | **+7.5%** | **+10.4%** | **+10.5%** |
| **semantic_logic_error** | Solver (Execution) | 30.4% (14/46) | 2.2% (1/45) | 0.0% (0/47) | 80.0% (32/40) | **+49.6%** | **+77.8%** | **+80.0%** |

## 2. Severity-Stratified Causal Defense Map (Number Swaps)
| Severity Level | Stage | Direct Prop % | CoT Prop % | Rubric Prop % | Ablated Prop % | Causal Defense ($\Delta_{CoT}$) | Causal Defense ($\Delta_{Rubric}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mild** | Decomposer (Plan) | 11.1% (1/9) | 0.0% (0/17) | 0.0% (0/17) | 0.0% (0/11) | 0.0% | 0.0% |
| **Mild** | Solver (Execution) | 0.0% (0/17) | 6.7% (1/15) | 0.0% (0/15) | 25.0% (5/20) | **+18.3%** | **+25.0%** |
| **Moderate** | Decomposer (Plan) | 5.9% (1/17) | 0.0% (0/20) | 0.0% (0/19) | 12.5% (2/16) | **+12.5%** | **+12.5%** |
| **Moderate** | Solver (Execution) | 18.8% (3/16) | 0.0% (0/15) | 6.7% (1/15) | 8.3% (1/12) | **+8.3%** | **+1.7%** |
| **Severe** | Decomposer (Plan) | 6.7% (1/15) | 0.0% (0/20) | 0.0% (0/13) | 13.3% (2/15) | **+13.3%** | **+13.3%** |
| **Severe** | Solver (Execution) | 7.7% (1/13) | 0.0% (0/16) | 0.0% (0/15) | 0.0% (0/17) | 0.0% | 0.0% |

---

# RQ3 Master Causal Error Map (Qwen 2.5 72B Instruct)

Synthesizing interaction between Injection Stage, Verifier Ablation, Error Type, Severity, and Verifier Strategy.

## 1. Causal Error Defense Matrix by Error Type
| Error Type | Stage | Direct Prop % | CoT Prop % | Rubric Prop % | Ablated Prop % (No Verifier) | Causal Verifier Defense ($\Delta_{Direct}$) | Causal Verifier Defense ($\Delta_{CoT}$) | Causal Verifier Defense ($\Delta_{Rubric}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **number_swap** | Decomposer (Plan) | 5.9% (2/34) | 2.3% (1/44) | 4.3% (2/46) | 5.4% (2/37) | -0.5% | **+3.1%** | **+1.1%** |
| **number_swap** | Solver (Execution) | 18.2% (8/44) | 2.9% (1/34) | 0.0% (0/40) | 7.1% (3/42) | -11.0% | **+4.2%** | **+7.1%** |
| **operation_flip** | Decomposer (Plan) | 0.0% (0/41) | 0.0% (0/39) | 2.8% (1/36) | 8.6% (3/35) | **+8.6%** | **+8.6%** | **+5.8%** |
| **operation_flip** | Solver (Execution) | 2.7% (1/37) | 0.0% (0/45) | 0.0% (0/45) | 2.1% (1/48) | -0.6% | **+2.1%** | **+2.1%** |
| **semantic_logic_error** | Decomposer (Plan) | 6.0% (3/50) | 6.4% (3/47) | 4.4% (2/45) | 9.4% (5/53) | **+3.4%** | **+3.1%** | **+5.0%** |
| **semantic_logic_error** | Solver (Execution) | 11.4% (5/44) | 9.8% (5/51) | 14.3% (6/42) | 77.1% (27/35) | **+65.8%** | **+67.3%** | **+62.9%** |

## 2. Severity-Stratified Causal Defense Map (Number Swaps)
| Severity Level | Stage | Direct Prop % | CoT Prop % | Rubric Prop % | Ablated Prop % | Causal Defense ($\Delta_{CoT}$) | Causal Defense ($\Delta_{Rubric}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mild** | Decomposer (Plan) | 9.1% (1/11) | 0.0% (0/12) | 0.0% (0/12) | 12.5% (1/8) | **+12.5%** | **+12.5%** |
| **Mild** | Solver (Execution) | 9.1% (1/11) | 0.0% (0/10) | 0.0% (0/16) | 18.2% (2/11) | **+18.2%** | **+18.2%** |
| **Moderate** | Decomposer (Plan) | 0.0% (0/12) | 5.6% (1/18) | 0.0% (0/18) | 6.2% (1/16) | **+0.7%** | **+6.2%** |
| **Moderate** | Solver (Execution) | 20.0% (3/15) | 0.0% (0/13) | 0.0% (0/12) | 5.9% (1/17) | **+5.9%** | **+5.9%** |
| **Severe** | Decomposer (Plan) | 9.1% (1/11) | 0.0% (0/14) | 12.5% (2/16) | 0.0% (0/13) | 0.0% | -12.5% |
| **Severe** | Solver (Execution) | 22.2% (4/18) | 9.1% (1/11) | 0.0% (0/12) | 0.0% (0/14) | -9.1% | 0.0% |