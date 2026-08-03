# RQ2 Master Report: Verifier Prompting Strategies

# RQ2 Comprehensive Report: Verifier Prompt Strategies (Claude Sonnet 4.6)

Evaluating **Direct**, **Chain-of-Thought (CoT)**, and **Rubric** prompting strategies on GSM-Hard (n=200).

## 1. Accuracy & Performance Breakdown
| Condition | Description | Direct Strategy (95% CI) | CoT Strategy (95% CI) | Rubric Strategy (95% CI) |
| :--- | :--- | :---: | :---: | :---: |
| **A** | Single Agent Baseline | 0.655 [0.590, 0.720] | 0.655 [0.590, 0.720] | 0.655 [0.590, 0.720] |
| **B** | Clean Multi-Agent Pipeline | 0.695 [0.630, 0.760] | 0.695 [0.630, 0.760] | 0.700 [0.635, 0.765] |
| **C1** | Plan Injected (Verifier ON) | 0.680 [0.615, 0.745] | 0.695 [0.630, 0.760] | 0.695 [0.635, 0.760] |
| **C2** | Solver Injected (Verifier ON) | 0.675 [0.610, 0.740] | 0.705 [0.640, 0.765] | 0.690 [0.625, 0.755] |
| **D1** | Plan Injected (Verifier OFF) | 0.645 [0.580, 0.710] | 0.645 [0.580, 0.710] | 0.645 [0.580, 0.710] |
| **D2** | Solver Injected (Verifier OFF) | 0.515 [0.445, 0.585] | 0.515 [0.445, 0.585] | 0.515 [0.445, 0.585] |

## 2. McNemar Exact Paired Significance Tests (Holm-Bonferroni Adjusted)
| Comparison Contrast | Metric Evaluated | Direct ($p_{holm}$) | CoT ($p_{holm}$) | Rubric ($p_{holm}$) |
| :--- | :--- | :---: | :---: | :---: |
| **A:B** | Single vs. Clean Pipeline | 0.0645 (+$n_{01}$=9, -$n_{10}$=1) | 0.0771 (+$n_{01}$=10, -$n_{10}$=2) | 0.0078 (+$n_{01}$=9, -$n_{10}$=0) |
| **B:C1** | Clean vs. Plan Sabotage | 0.3750 (+$n_{01}$=1, -$n_{10}$=4) | 1.0000 (+$n_{01}$=2, -$n_{10}$=2) | 1.0000 (+$n_{01}$=2, -$n_{10}$=3) |
| **C1:D1** | Plan Protection (Verifier Impact) | 0.1846 (+$n_{01}$=3, -$n_{10}$=10) | 0.0388 (+$n_{01}$=2, -$n_{10}$=12) | 0.0059 (+$n_{01}$=0, -$n_{10}$=10) |
| **C2:D2** | Solver Protection (Verifier Impact) | 0.0000 (+$n_{01}$=3, -$n_{10}$=35) | 0.0000 (+$n_{01}$=1, -$n_{10}$=39) | 0.0000 (+$n_{01}$=2, -$n_{10}$=37) |

## 3. Error Fate & Defense Dynamics
### A. Plan Injected Condition (C1)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 139 | 139 | 140 |
| **Propagation Rate** | 2.9% | 1.4% | 2.1% |
| **Catch Rate** | 7.9% | 7.9% | 6.4% |
| **Correction Rate** | 90.9% | 90.9% | 88.9% |
| Natural Absorption (No Flag) | 125 | 127 | 129 |
| Caught & Corrected | 10 | 10 | 8 |
| Caught but Not Corrected | 1 | 1 | 1 |

### B. Solver Injected Condition (C2)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 139 | 139 | 140 |
| **Propagation Rate** | 2.9% | 0.7% | 1.4% |
| **Catch Rate** | 33.8% | 35.3% | 36.4% |
| **Correction Rate** | 95.7% | 98.0% | 100.0% |
| Natural Absorption (No Flag) | 90 | 90 | 87 |
| Caught & Corrected | 45 | 48 | 51 |
| Caught but Not Corrected | 2 | 1 | 0 |

## 4. Severity Propagation Comparison (Number Swaps)
| Severity Level | Condition | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **Mild** | C1 (Plan) | 0/9 (0.0%) | 0/17 (0.0%) | 0/17 (0.0%) |
| **Mild** | C2 (Solver) | 0/17 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| **Moderate** | C1 (Plan) | 1/17 (5.9%) | 0/20 (0.0%) | 0/19 (0.0%) |
| **Moderate** | C2 (Solver) | 2/16 (12.5%) | 0/15 (0.0%) | 1/15 (6.7%) |
| **Severe** | C1 (Plan) | 0/15 (0.0%) | 0/20 (0.0%) | 0/13 (0.0%) |
| **Severe** | C2 (Solver) | 0/13 (0.0%) | 0/16 (0.0%) | 0/15 (0.0%) |

## 5. Cost & Token Efficiency Analysis
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Total Pipeline Tokens (C2) | 228,899 | 283,725 | 300,587 |
| Verifier Stage Tokens (C2) | 103,378 | 157,191 | 173,825 |
| Avg Tokens / Problem | 1144.5 | 1418.6 | 1502.9 |
| Tokens / Solved Problem | 1695.5 | 2012.2 | 2178.2 |

## 6. Logistic Regression Odds Ratios (H2 Survival Factors)
| Predictor Variable | Direct OR [95% CI] (p-val) | CoT OR [95% CI] (p-val) | Rubric OR [95% CI] (p-val) |
| :--- | :---: | :---: | :---: |
| **early_stage** | 0.94 [0.23, 3.86] (p=0.9280) | 2.20 [0.19, 24.92] (p=0.5247) | 1.60 [0.26, 9.83] (p=0.6094) |
| **operation_flip** | 0.33 [0.03, 3.27] (p=0.3450) | 6054783.12 [0.00, inf] (p=0.9940) | 3.29 [0.34, 32.37] (p=0.3066) |
| **semantic_logic_error** | 1.10 [0.24, 5.11] (p=0.8984) | 10313505.78 [0.00, inf] (p=0.9938) | 0.98 [0.06, 15.98] (p=0.9909) |

---

# RQ2 Comprehensive Report: Verifier Prompt Strategies (Qwen 2.5 72B Instruct)

Evaluating **Direct**, **Chain-of-Thought (CoT)**, and **Rubric** prompting strategies on GSM-Hard (n=200).

## 1. Accuracy & Performance Breakdown
| Condition | Description | Direct Strategy (95% CI) | CoT Strategy (95% CI) | Rubric Strategy (95% CI) |
| :--- | :--- | :---: | :---: | :---: |
| **A** | Single Agent Baseline | 0.625 [0.560, 0.695] | 0.625 [0.560, 0.695] | 0.625 [0.560, 0.695] |
| **B** | Clean Multi-Agent Pipeline | 0.630 [0.565, 0.695] | 0.650 [0.585, 0.715] | 0.635 [0.570, 0.700] |
| **C1** | Plan Injected (Verifier ON) | 0.615 [0.550, 0.680] | 0.645 [0.580, 0.710] | 0.615 [0.545, 0.680] |
| **C2** | Solver Injected (Verifier ON) | 0.560 [0.490, 0.630] | 0.630 [0.565, 0.695] | 0.620 [0.550, 0.685] |
| **D1** | Plan Injected (Verifier OFF) | 0.610 [0.545, 0.675] | 0.610 [0.545, 0.675] | 0.610 [0.545, 0.675] |
| **D2** | Solver Injected (Verifier OFF) | 0.505 [0.440, 0.575] | 0.505 [0.440, 0.575] | 0.505 [0.440, 0.575] |

## 2. McNemar Exact Paired Significance Tests (Holm-Bonferroni Adjusted)
| Comparison Contrast | Metric Evaluated | Direct ($p_{holm}$) | CoT ($p_{holm}$) | Rubric ($p_{holm}$) |
| :--- | :--- | :---: | :---: | :---: |
| **A:B** | Single vs. Clean Pipeline | 1.0000 (+$n_{01}$=8, -$n_{10}$=7) | 0.6035 (+$n_{01}$=10, -$n_{10}$=5) | 1.0000 (+$n_{01}$=7, -$n_{10}$=5) |
| **B:C1** | Clean vs. Plan Sabotage | 1.0000 (+$n_{01}$=4, -$n_{10}$=7) | 1.0000 (+$n_{01}$=3, -$n_{10}$=4) | 0.6562 (+$n_{01}$=1, -$n_{10}$=5) |
| **C1:D1** | Plan Protection (Verifier Impact) | 1.0000 (+$n_{01}$=8, -$n_{10}$=9) | 0.3554 (+$n_{01}$=4, -$n_{10}$=11) | 1.0000 (+$n_{01}$=7, -$n_{10}$=8) |
| **C2:D2** | Solver Protection (Verifier Impact) | 0.5406 (+$n_{01}$=17, -$n_{10}$=28) | 0.0003 (+$n_{01}$=7, -$n_{10}$=32) | 0.0012 (+$n_{01}$=8, -$n_{10}$=31) |

## 3. Error Fate & Defense Dynamics
### A. Plan Injected Condition (C1)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 126 | 130 | 127 |
| **Propagation Rate** | 5.6% | 3.1% | 3.9% |
| **Catch Rate** | 9.5% | 5.4% | 2.4% |
| **Correction Rate** | 41.7% | 57.1% | 33.3% |
| Natural Absorption (No Flag) | 114 | 122 | 121 |
| Caught & Corrected | 5 | 4 | 1 |
| Caught but Not Corrected | 7 | 3 | 2 |

### B. Solver Injected Condition (C2)
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Valid Injections ($n$) | 126 | 130 | 127 |
| **Propagation Rate** | 15.9% | 4.6% | 4.7% |
| **Catch Rate** | 62.7% | 38.5% | 50.4% |
| **Correction Rate** | 78.5% | 98.0% | 95.3% |
| Natural Absorption (No Flag) | 44 | 75 | 60 |
| Caught & Corrected | 62 | 49 | 61 |
| Caught but Not Corrected | 17 | 1 | 3 |

## 4. Severity Propagation Comparison (Number Swaps)
| Severity Level | Condition | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **Mild** | C1 (Plan) | 1/11 (9.1%) | 0/12 (0.0%) | 0/12 (0.0%) |
| **Mild** | C2 (Solver) | 2/11 (18.2%) | 0/10 (0.0%) | 0/16 (0.0%) |
| **Moderate** | C1 (Plan) | 1/13 (7.7%) | 1/18 (5.6%) | 0/18 (0.0%) |
| **Moderate** | C2 (Solver) | 5/15 (33.3%) | 0/13 (0.0%) | 0/12 (0.0%) |
| **Severe** | C1 (Plan) | 1/11 (9.1%) | 0/14 (0.0%) | 2/16 (12.5%) |
| **Severe** | C2 (Solver) | 6/18 (33.3%) | 1/11 (9.1%) | 0/12 (0.0%) |

## 5. Cost & Token Efficiency Analysis
| Metric | Direct Strategy | CoT Strategy | Rubric Strategy |
| :--- | :---: | :---: | :---: |
| Total Pipeline Tokens (C2) | 212,546 | 291,966 | 276,553 |
| Verifier Stage Tokens (C2) | 84,165 | 164,977 | 148,567 |
| Avg Tokens / Problem | 1062.7 | 1459.8 | 1382.8 |
| Tokens / Solved Problem | 1897.7 | 2317.2 | 2230.3 |

## 6. Logistic Regression Odds Ratios (H2 Survival Factors)
| Predictor Variable | Direct OR [95% CI] (p-val) | CoT OR [95% CI] (p-val) | Rubric OR [95% CI] (p-val) |
| :--- | :---: | :---: | :---: |
| **early_stage** | 0.32 [0.13, 0.81] (p=0.0164) | 0.66 [0.18, 2.44] (p=0.5282) | 0.77 [0.23, 2.66] (p=0.6833) |
| **operation_flip** | 0.11 [0.02, 0.48] (p=0.0037) | 0.00 [0.00, inf] (p=0.9992) | 0.51 [0.05, 5.78] (p=0.5892) |
| **semantic_logic_error** | 0.45 [0.18, 1.09] (p=0.0762) | 3.27 [0.67, 15.92] (p=0.1427) | 4.24 [0.87, 20.58] (p=0.0732) |