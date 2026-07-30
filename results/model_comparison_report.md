# Model Comparison Report: Claude Sonnet vs. Qwen 2.5 72B

Both models evaluated on the **GSM-Hard** dataset (n=200, seed=42).

## 1. Accuracy Summary (with 95% Bootstrap CI)
| Condition | Claude Sonnet Accuracy (95% CI) | Qwen 2.5 72B Accuracy (95% CI) |
| :--- | :---: | :---: |
| **A** | 0.655 [0.590, 0.720] | 0.625 [0.560, 0.695] |
| **B** | 0.695 [0.630, 0.760] | 0.625 [0.560, 0.690] |
| **C1** | 0.665 [0.600, 0.730] | 0.625 [0.560, 0.695] |
| **C2** | 0.605 [0.540, 0.670] | 0.585 [0.515, 0.650] |
| **D1** | 0.645 [0.580, 0.710] | 0.610 [0.545, 0.675] |
| **D2** | 0.515 [0.445, 0.585] | 0.505 [0.440, 0.575] |

## 2. McNemar Exact Paired Significance Tests
| Comparison | Claude p-value (Holm) | Qwen 2.5 p-value (Holm) |
| :--- | :---: | :---: |
| **A:B** | 0.0645 | 1.0000 |
| **B:C1** | 0.1406 | 1.0000 |
| **C1:D1** | 0.4240 | 1.0000 |
| **C2:D2** | 0.0382 | 0.0781 |

## 3. Error Fate Metrics (C1 vs. C2)
| Metric | Claude (C1) | Qwen (C1) | Claude (C2) | Qwen (C2) |
| :--- | :---: | :---: | :---: | :---: |
| Valid Injections ($n$) | 139 | 125 | 139 | 125 |
| Propagation Rate | 5.0% [0.025, 0.100] | 4.0% [0.017, 0.090] | 12.9% [0.084, 0.195] | 11.2% [0.068, 0.179] |
| Catch Rate | 7.9% [0.045, 0.136] | 8.8% [0.050, 0.151] | 33.8% [0.265, 0.420] | 62.4% [0.537, 0.704] |
| Correction Rate | 63.6% [0.354, 0.848] | 54.5% [0.280, 0.787] | 66.0% [0.517, 0.778] | 85.9% [0.765, 0.919] |
| Absorbed (No Flag) | 125 | 114 | 90 | 44 |
| Caught & Corrected | 7 | 6 | 31 | 67 |

## 4. Severity Propagation Rates (Number Swaps only)
| Severity Level | Claude (C1) | Qwen (C1) | Claude (C2) | Qwen (C2) | Claude (D2 - No Verifier) | Qwen (D2 - No Verifier) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mild** | 1/9 (11.1%) | 1/11 (9.1%) | 0/17 (0.0%) | 1/11 (9.1%) | 5/20 (25.0%) | 2/11 (18.2%) |
| **Moderate** | 1/17 (5.9%) | 0/12 (0.0%) | 3/16 (18.8%) | 3/15 (20.0%) | 1/12 (8.3%) | 1/17 (5.9%) |
| **Severe** | 1/15 (6.7%) | 1/11 (9.1%) | 1/13 (7.7%) | 4/18 (22.2%) | 0/17 (0.0%) | 0/14 (0.0%) |

## 5. Fault Survival Logit Odds Ratios (H2)
| Predictor | Claude OR [95% CI] (p-val) | Qwen 2.5 OR [95% CI] (p-val) |
| :--- | :---: | :---: |
| **early_stage** | 0.28 [0.11, 0.72] (p=0.0084) | 0.35 [0.12, 1.01] (p=0.0515) |
| **operation_flip** | 0.13 [0.02, 1.09] (p=0.0596) | 0.09 [0.01, 0.76] (p=0.0263) |
| **semantic_logic_error** | 2.52 [0.97, 6.54] (p=0.0571) | 0.69 [0.25, 1.87] (p=0.4642) |