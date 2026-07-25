# RQ2 Master Report: Verifier Prompting Strategies

# RQ2 Comprehensive Report: Verifier Prompt Strategies (Claude Sonnet 4.6)

Evaluating **Direct**, **Chain-of-Thought (CoT)**, and **Rubric** prompting strategies on GSM-Hard (n=200).

## 1. Accuracy & Performance Breakdown
| Condition | Description | Direct Strategy (95% CI) | CoT Strategy (95% CI) | Rubric Strategy (95% CI) |
| :--- | :--- | :---: | :---: | :---: |
| **A** | Single Agent Baseline | 0.655 [0.590, 0.720] | 0.655 [0.590, 0.720] | 0.655 [0.590, 0.720] |
| **B** | Clean Multi-Agent Pipeline | 0.695 [0.630, 0.760] | 0.695 [0.630, 0.760] | 0.700 [0.635, 0.765] |
| **C1** | Plan Injected (Verifier ON) | 0.665 [0.600, 0.730] | 0.695 [0.630, 0.760] | 0.695 [0.635, 0.760] |
| **C2** | Solver Injected (Verifier ON) | 0.605 [0.540, 0.670] | 0.700 [0.635, 0.765] | 0.695 [0.630, 0.755] |
| **D1** | Plan Injected (Verifier OFF) | 0.645 [0.580, 0.710] | 0.645 [0.580, 0.710] | 0.645 [0.580, 0.710] |
| **D2** | Solver Injected (Verifier OFF) | 0.515 [0.445, 0.585] | 0.515 [0.445, 0.585] | 0.515 [0.445, 0.585] |

## 2. McNemar Exact Paired Significance Tests (Holm-Bonferroni Adjusted)
| Comparison Contrast | Metric Evaluated | Direct ($p_{holm}$) | CoT ($p_{holm}$) | Rubric ($p_{holm}$) |
| :--- | :--- | :---: | :---: | :---: |
| **A:B** | Single vs. Clean Pipeline | 0.0645 (+$n_{01}$=9, -$n_{10}$=1) | 0.0771 (+$n_{01}$=10, -$n_{10}$=2) | 0.0078 (+$n_{01}$=9, -$n_{10}$=0) |
| **B:C1** | Clean vs. Plan Sabotage | 0.1406 (+$n_{01}$=1, -$n_{10}$=7) | 1.0000 (+$n_{01}$=2, -$n_{10}$=2) | 1.0000 (+$n_{01}$=2, -$n_{10}$=3) |
| **C1:D1** | Plan Protection (Verifier Impact) | 0.4240 (+$n_{01}$=5, -$n_{10}$=9) | 0.0388 (+$n_{01}$=2, -$n_{10}$=12) | 0.0059 (+$n_{01}$=0, -$n_{10}$=10) |
| **C2:D2** | Solver Protection (Verifier Impact) | 0.0382 (+$n_{01}$=13, -$n_{10}$=31) | 0.0000 (+$n_{01}$=2, -$n_{10}$=39) | 0.0000 (+$n_{01}$=1, -$n_{10}$=37) |

## 3. Error Fate & Defense Dynamics
### A. Plan Injected Condition (C1)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 139 | 139 | 140 |
| **Propagation Rate** | 5.0% | 1.4% | 2.1% |
| **Catch Rate** | 7.9% | 7.9% | 6.4% |
| **Correction Rate** | 63.6% | 90.9% | 88.9% |
| Natural Absorption (No Flag) | 125 | 127 | 129 |
| Caught & Corrected | 7 | 10 | 8 |
| Caught but Not Corrected | 4 | 1 | 1 |

### B. Solver Injected Condition (C2)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 139 | 139 | 140 |
| **Propagation Rate** | 12.9% | 1.4% | 1.4% |
| **Catch Rate** | 33.8% | 35.3% | 36.4% |
| **Correction Rate** | 66.0% | 95.9% | 100.0% |
| Natural Absorption (No Flag) | 90 | 90 | 87 |
| Caught & Corrected | 31 | 47 | 51 |
| Caught but Not Corrected | 16 | 2 | 0 |

## 4. Severity Propagation Comparison (Number Swaps)
| Severity Level | Condition | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **Mild** | C1 (Plan) | 1/9 (11.1%) | 0/17 (0.0%) | 0/17 (0.0%) |
| **Mild** | C2 (Solver) | 0/17 (0.0%) | 1/15 (6.7%) | 0/15 (0.0%) |
| **Moderate** | C1 (Plan) | 1/17 (5.9%) | 0/20 (0.0%) | 0/19 (0.0%) |
| **Moderate** | C2 (Solver) | 3/16 (18.8%) | 0/15 (0.0%) | 1/15 (6.7%) |
| **Severe** | C1 (Plan) | 1/15 (6.7%) | 0/20 (0.0%) | 0/13 (0.0%) |
| **Severe** | C2 (Solver) | 1/13 (7.7%) | 0/16 (0.0%) | 0/15 (0.0%) |

## 5. Cost & Token Efficiency Analysis
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Total Pipeline Tokens (C2) | 228,899 | 283,725 | 300,587 |
| Verifier Stage Tokens (C2) | 103,378 | 157,191 | 173,825 |
| Avg Tokens / Problem | 1144.5 | 1418.6 | 1502.9 |
| Tokens / Solved Problem | 1891.7 | 2026.6 | 2162.5 |

## 6. Logistic Regression Odds Ratios (H2 Survival Factors)
| Predictor Variable | Direct OR [95% CI] (p-val) | CoT OR [95% CI] (p-val) | Rubric OR [95% CI] (p-val) |
| :--- | :---: | :---: | :---: |
| **early_stage** | 0.28 [0.11, 0.72] (p=0.0084) | 1.00 [0.14, 7.31] (p=0.9974) | 1.60 [0.26, 9.83] (p=0.6094) |
| **operation_flip** | 0.13 [0.02, 1.09] (p=0.0596) | 1.24 [0.08, 20.45] (p=0.8783) | 3.29 [0.34, 32.37] (p=0.3066) |
| **semantic_logic_error** | 2.52 [0.97, 6.54] (p=0.0571) | 2.27 [0.20, 25.46] (p=0.5072) | 0.98 [0.06, 15.98] (p=0.9909) |

---

# RQ2 Comprehensive Report: Verifier Prompt Strategies (Qwen 2.5 72B Instruct)

Evaluating **Direct**, **Chain-of-Thought (CoT)**, and **Rubric** prompting strategies on GSM-Hard (n=200).

## 1. Accuracy & Performance Breakdown
| Condition | Description | Direct Strategy (95% CI) | CoT Strategy (95% CI) | Rubric Strategy (95% CI) |
| :--- | :--- | :---: | :---: | :---: |
| **A** | Single Agent Baseline | 0.625 [0.560, 0.695] | 0.625 [0.560, 0.695] | 0.625 [0.560, 0.695] |
| **B** | Clean Multi-Agent Pipeline | 0.625 [0.560, 0.690] | 0.650 [0.585, 0.715] | 0.635 [0.570, 0.700] |
| **C1** | Plan Injected (Verifier ON) | 0.625 [0.560, 0.695] | 0.645 [0.580, 0.710] | 0.615 [0.545, 0.680] |
| **C2** | Solver Injected (Verifier ON) | 0.585 [0.515, 0.650] | 0.630 [0.565, 0.695] | 0.620 [0.550, 0.685] |
| **D1** | Plan Injected (Verifier OFF) | 0.610 [0.545, 0.675] | 0.610 [0.545, 0.675] | 0.610 [0.545, 0.675] |
| **D2** | Solver Injected (Verifier OFF) | 0.505 [0.440, 0.575] | 0.505 [0.440, 0.575] | 0.505 [0.440, 0.575] |

## 2. McNemar Exact Paired Significance Tests (Holm-Bonferroni Adjusted)
| Comparison Contrast | Metric Evaluated | Direct ($p_{holm}$) | CoT ($p_{holm}$) | Rubric ($p_{holm}$) |
| :--- | :--- | :---: | :---: | :---: |
| **A:B** | Single vs. Clean Pipeline | 1.0000 (+$n_{01}$=7, -$n_{10}$=7) | 0.6035 (+$n_{01}$=10, -$n_{10}$=5) | 1.0000 (+$n_{01}$=7, -$n_{10}$=5) |
| **B:C1** | Clean vs. Plan Sabotage | 1.0000 (+$n_{01}$=5, -$n_{10}$=5) | 1.0000 (+$n_{01}$=3, -$n_{10}$=4) | 0.6562 (+$n_{01}$=1, -$n_{10}$=5) |
| **C1:D1** | Plan Protection (Verifier Impact) | 1.0000 (+$n_{01}$=7, -$n_{10}$=10) | 0.3554 (+$n_{01}$=4, -$n_{10}$=11) | 1.0000 (+$n_{01}$=7, -$n_{10}$=8) |
| **C2:D2** | Solver Protection (Verifier Impact) | 0.0781 (+$n_{01}$=13, -$n_{10}$=29) | 0.0003 (+$n_{01}$=7, -$n_{10}$=32) | 0.0012 (+$n_{01}$=8, -$n_{10}$=31) |

## 3. Error Fate & Defense Dynamics
### A. Plan Injected Condition (C1)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 125 | 130 | 127 |
| **Propagation Rate** | 4.0% | 3.1% | 3.9% |
| **Catch Rate** | 8.8% | 5.4% | 2.4% |
| **Correction Rate** | 54.5% | 57.1% | 33.3% |
| Natural Absorption (No Flag) | 114 | 122 | 121 |
| Caught & Corrected | 6 | 4 | 1 |
| Caught but Not Corrected | 5 | 3 | 2 |

### B. Solver Injected Condition (C2)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 125 | 130 | 127 |
| **Propagation Rate** | 11.2% | 4.6% | 4.7% |
| **Catch Rate** | 62.4% | 38.5% | 50.4% |
| **Correction Rate** | 85.9% | 98.0% | 95.3% |
| Natural Absorption (No Flag) | 44 | 75 | 60 |
| Caught & Corrected | 67 | 49 | 61 |
| Caught but Not Corrected | 11 | 1 | 3 |

## 4. Severity Propagation Comparison (Number Swaps)
| Severity Level | Condition | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **Mild** | C1 (Plan) | 1/11 (9.1%) | 0/12 (0.0%) | 0/12 (0.0%) |
| **Mild** | C2 (Solver) | 1/11 (9.1%) | 0/10 (0.0%) | 0/16 (0.0%) |
| **Moderate** | C1 (Plan) | 0/12 (0.0%) | 1/18 (5.6%) | 0/18 (0.0%) |
| **Moderate** | C2 (Solver) | 3/15 (20.0%) | 0/13 (0.0%) | 0/12 (0.0%) |
| **Severe** | C1 (Plan) | 1/11 (9.1%) | 0/14 (0.0%) | 2/16 (12.5%) |
| **Severe** | C2 (Solver) | 4/18 (22.2%) | 1/11 (9.1%) | 0/12 (0.0%) |

## 5. Cost & Token Efficiency Analysis
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Total Pipeline Tokens (C2) | 212,546 | 291,966 | 276,553 |
| Verifier Stage Tokens (C2) | 84,165 | 164,977 | 148,567 |
| Avg Tokens / Problem | 1062.7 | 1459.8 | 1382.8 |
| Tokens / Solved Problem | 1816.6 | 2317.2 | 2230.3 |

## 6. Logistic Regression Odds Ratios (H2 Survival Factors)
| Predictor Variable | Direct OR [95% CI] (p-val) | CoT OR [95% CI] (p-val) | Rubric OR [95% CI] (p-val) |
| :--- | :---: | :---: | :---: |
| **early_stage** | 0.35 [0.12, 1.01] (p=0.0515) | 0.66 [0.18, 2.44] (p=0.5282) | 0.77 [0.23, 2.66] (p=0.6833) |
| **operation_flip** | 0.09 [0.01, 0.76] (p=0.0263) | 0.00 [0.00, inf] (p=0.9992) | 0.51 [0.05, 5.78] (p=0.5892) |
| **semantic_logic_error** | 0.69 [0.25, 1.87] (p=0.4642) | 3.27 [0.67, 15.92] (p=0.1427) | 4.24 [0.87, 20.58] (p=0.0732) |