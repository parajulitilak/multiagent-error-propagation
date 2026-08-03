# Model Comparison Report: Claude Sonnet vs. Qwen 2.5 72B

Both models evaluated on the **GSM-Hard** dataset (n=200, seed=42).

## 1. Accuracy Summary (with 95% Bootstrap CI)
| Condition | Claude Sonnet Accuracy (95% CI) | Qwen 2.5 72B Accuracy (95% CI) |
| :--- | :---: | :---: |
| **A** | 0.655 [0.590, 0.720] | 0.625 [0.560, 0.695] |
| **B** | 0.695 [0.630, 0.760] | 0.630 [0.565, 0.695] |
| **C1** | 0.680 [0.615, 0.745] | 0.615 [0.550, 0.680] |
| **C2** | 0.675 [0.610, 0.740] | 0.560 [0.490, 0.630] |
| **D1** | 0.645 [0.580, 0.710] | 0.610 [0.545, 0.675] |
| **D2** | 0.515 [0.445, 0.585] | 0.505 [0.440, 0.575] |

## 2. McNemar Exact Paired Significance Tests
| Comparison | Claude p-value (Holm) | Qwen 2.5 p-value (Holm) |
| :--- | :---: | :---: |
| **A:B** | 0.0645 | 1.0000 |
| **B:C1** | 0.3750 | 1.0000 |
| **C1:D1** | 0.1846 | 1.0000 |
| **C2:D2** | 0.0000 | 0.5406 |

## 3. Error Fate Metrics (C1 vs. C2)
| Metric | Claude (C1) | Qwen (C1) | Claude (C2) | Qwen (C2) |
| :--- | :---: | :---: | :---: | :---: |
| Valid Injections ($n$) | 139 | 126 | 139 | 126 |
| Propagation Rate | 2.9% [0.011, 0.072] | 5.6% [0.027, 0.110] | 2.9% [0.011, 0.072] | 15.9% [0.105, 0.232] |
| Catch Rate | 7.9% [0.045, 0.136] | 9.5% [0.055, 0.159] | 33.8% [0.265, 0.420] | 62.7% [0.540, 0.706] |
| Correction Rate | 90.9% [0.623, 0.984] | 41.7% [0.193, 0.680] | 95.7% [0.858, 0.988] | 78.5% [0.682, 0.861] |
| Absorbed (No Flag) | 125 | 114 | 90 | 44 |
| Caught & Corrected | 10 | 5 | 45 | 62 |

## 4. Severity Propagation Rates (Number Swaps only)
| Severity Level | Claude (C1) | Qwen (C1) | Claude (C2) | Qwen (C2) | Claude (D2 - No Verifier) | Qwen (D2 - No Verifier) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mild** | 0/9 (0.0%) | 1/11 (9.1%) | 0/17 (0.0%) | 2/11 (18.2%) | 5/20 (25.0%) | 2/11 (18.2%) |
| **Moderate** | 1/17 (5.9%) | 1/13 (7.7%) | 2/16 (12.5%) | 5/15 (33.3%) | 1/12 (8.3%) | 1/17 (5.9%) |
| **Severe** | 0/15 (0.0%) | 1/11 (9.1%) | 0/13 (0.0%) | 6/18 (33.3%) | 0/17 (0.0%) | 0/14 (0.0%) |

## 5. Fault Survival Logit Odds Ratios (H2)
| Predictor | Claude OR [95% CI] (p-val) | Qwen 2.5 OR [95% CI] (p-val) |
| :--- | :---: | :---: |
| **early_stage** | 0.94 [0.23, 3.86] (p=0.9280) | 0.32 [0.13, 0.81] (p=0.0164) |
| **operation_flip** | 0.33 [0.03, 3.27] (p=0.3450) | 0.11 [0.02, 0.48] (p=0.0037) |
| **semantic_logic_error** | 1.10 [0.24, 5.11] (p=0.8984) | 0.45 [0.18, 1.09] (p=0.0762) |