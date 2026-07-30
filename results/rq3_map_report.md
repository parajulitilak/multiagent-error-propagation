# RQ3 Master Error Map Report

---

# RQ3 Master Causal Error Map (Claude Sonnet 4.6)

Synthesizing the interaction between injection stage, verifier ablation, error type, severity, and verifier strategy.

## 1. Causal Error Defense Matrix by Error Type
| Error Type | Stage | Direct Catch % | Direct Corr % | Direct Prop % | CoT Catch % | CoT Corr % | CoT Prop % | Rubric Catch % | Rubric Corr % | Rubric Prop % | Ablated Prop % | Defense Δ Direct | Defense Δ CoT | Defense Δ Rubric |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **number_swap** | Decomposer (Plan) | 4.9% (2/41) | 100.0% (2/2) | 2.4% (1/41) | 5.3% (3/57) | 100.0% (3/3) | 0.0% (0/57) | 4.1% (2/49) | 100.0% (2/2) | 0.0% (0/49) | 9.5% (4/42) | **+7.1%** | **+9.5%** | **+9.5%** |
| **number_swap** | Solver (Execution) | 19.6% (9/46) | 100.0% (9/9) | 4.3% (2/46) | 19.6% (9/46) | 100.0% (9/9) | 0.0% (0/46) | 24.4% (11/45) | 100.0% (11/11) | 2.2% (1/45) | 12.2% (6/49) | **+7.9%** | **+12.2%** | **+10.0%** |
| **operation_flip** | Decomposer (Plan) | 0.0% (0/38) | 0.0% (0/0) | 2.6% (1/38) | 0.0% (0/35) | 0.0% (0/0) | 2.9% (1/35) | 0.0% (0/42) | 0.0% (0/0) | 4.8% (2/42) | 2.4% (1/41) | **-0.2%** | **-0.4%** | **-2.3%** |
| **operation_flip** | Solver (Execution) | 0.0% (0/47) | 0.0% (0/0) | 0.0% (0/47) | 0.0% (0/48) | 0.0% (0/0) | 0.0% (0/48) | 2.1% (1/48) | 100.0% (1/1) | 2.1% (1/48) | 0.0% (0/50) | **+0.0%** | **+0.0%** | **-2.1%** |
| **semantic_logic_error** | Decomposer (Plan) | 15.0% (9/60) | 88.9% (8/9) | 3.3% (2/60) | 17.0% (8/47) | 87.5% (7/8) | 2.1% (1/47) | 14.3% (7/49) | 85.7% (6/7) | 2.0% (1/49) | 12.5% (7/56) | **+9.2%** | **+10.4%** | **+10.5%** |
| **semantic_logic_error** | Solver (Execution) | 82.6% (38/46) | 94.7% (36/38) | 4.3% (2/46) | 88.9% (40/45) | 97.5% (39/40) | 2.2% (1/45) | 83.0% (39/47) | 100.0% (39/39) | 0.0% (0/47) | 80.0% (32/40) | **+75.7%** | **+77.8%** | **+80.0%** |

## 2. Severity-Stratified Causal Defense Map (Number Swaps)
| Severity Level | Stage | Direct Catch % | Direct Corr % | Direct Prop % | CoT Catch % | CoT Corr % | CoT Prop % | Rubric Catch % | Rubric Corr % | Rubric Prop % | Ablated Prop % | Defense Δ Direct | Defense Δ CoT | Defense Δ Rubric |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mild** | Decomposer (Plan) | 11.1% (1/9) | 100.0% (1/1) | 0.0% (0/9) | 11.8% (2/17) | 100.0% (2/2) | 0.0% (0/17) | 5.9% (1/17) | 100.0% (1/1) | 0.0% (0/17) | 0.0% (0/11) | **+0.0%** | **+0.0%** | **+0.0%** |
| **Mild** | Solver (Execution) | 35.3% (6/17) | 100.0% (6/6) | 0.0% (0/17) | 26.7% (4/15) | 100.0% (4/4) | 0.0% (0/15) | 26.7% (4/15) | 100.0% (4/4) | 0.0% (0/15) | 25.0% (5/20) | **+25.0%** | **+25.0%** | **+25.0%** |
| **Moderate** | Decomposer (Plan) | 0.0% (0/17) | 0.0% (0/0) | 5.9% (1/17) | 5.0% (1/20) | 100.0% (1/1) | 0.0% (0/20) | 0.0% (0/19) | 0.0% (0/0) | 0.0% (0/19) | 12.5% (2/16) | **+6.6%** | **+12.5%** | **+12.5%** |
| **Moderate** | Solver (Execution) | 12.5% (2/16) | 100.0% (2/2) | 12.5% (2/16) | 13.3% (2/15) | 100.0% (2/2) | 0.0% (0/15) | 40.0% (6/15) | 100.0% (6/6) | 6.7% (1/15) | 8.3% (1/12) | **-4.2%** | **+8.3%** | **+1.7%** |
| **Severe** | Decomposer (Plan) | 6.7% (1/15) | 100.0% (1/1) | 0.0% (0/15) | 0.0% (0/20) | 0.0% (0/0) | 0.0% (0/20) | 7.7% (1/13) | 100.0% (1/1) | 0.0% (0/13) | 13.3% (2/15) | **+13.3%** | **+13.3%** | **+13.3%** |
| **Severe** | Solver (Execution) | 7.7% (1/13) | 100.0% (1/1) | 0.0% (0/13) | 18.8% (3/16) | 100.0% (3/3) | 0.0% (0/16) | 6.7% (1/15) | 100.0% (1/1) | 0.0% (0/15) | 0.0% (0/17) | **+0.0%** | **+0.0%** | **+0.0%** |

## 3. Best Verifier by Error Type and Stage
| Subgroup | Stage | Best Catch Strategy | Best Correction Strategy | Lowest Propagation Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **number_swap** | Decomposer (Plan) | cot | direct | cot |
| **number_swap** | Solver (Execution) | rubric | direct | cot |
| **operation_flip** | Decomposer (Plan) | direct | direct | direct |
| **operation_flip** | Solver (Execution) | rubric | rubric | direct |
| **semantic_logic_error** | Decomposer (Plan) | cot | direct | rubric |
| **semantic_logic_error** | Solver (Execution) | cot | rubric | rubric |

## 4. Best Verifier by Severity and Stage
| Subgroup | Stage | Best Catch Strategy | Best Correction Strategy | Lowest Propagation Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **Mild** | Decomposer (Plan) | cot | direct | direct |
| **Mild** | Solver (Execution) | direct | direct | direct |
| **Moderate** | Decomposer (Plan) | cot | cot | cot |
| **Moderate** | Solver (Execution) | rubric | direct | cot |
| **Severe** | Decomposer (Plan) | rubric | direct | direct |
| **Severe** | Solver (Execution) | cot | direct | direct |

## 5. Global Strategy Win Summary
These counts summarize how often each verifier strategy wins across subgroups.

### Error-Type Map Wins
- Direct best catch wins: **1**
- CoT best catch wins: **3**
- Rubric best catch wins: **2**
- Direct best correction wins: **4**
- CoT best correction wins: **0**
- Rubric best correction wins: **2**
- Direct lowest propagation wins: **2**
- CoT lowest propagation wins: **2**
- Rubric lowest propagation wins: **2**

### Severity Map Wins
- Direct best catch wins: **1**
- CoT best catch wins: **3**
- Rubric best catch wins: **2**
- Direct best correction wins: **5**
- CoT best correction wins: **1**
- Rubric best correction wins: **0**
- Direct lowest propagation wins: **4**
- CoT lowest propagation wins: **2**
- Rubric lowest propagation wins: **0**

---

# RQ3 Master Causal Error Map (Qwen 2.5 72B Instruct)

Synthesizing the interaction between injection stage, verifier ablation, error type, severity, and verifier strategy.

## 1. Causal Error Defense Matrix by Error Type
| Error Type | Stage | Direct Catch % | Direct Corr % | Direct Prop % | CoT Catch % | CoT Corr % | CoT Prop % | Rubric Catch % | Rubric Corr % | Rubric Prop % | Ablated Prop % | Defense Δ Direct | Defense Δ CoT | Defense Δ Rubric |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **number_swap** | Decomposer (Plan) | 8.6% (3/35) | 0.0% (0/3) | 8.6% (3/35) | 4.5% (2/44) | 50.0% (1/2) | 2.3% (1/44) | 4.3% (2/46) | 50.0% (1/2) | 4.3% (2/46) | 5.4% (2/37) | **-3.2%** | **+3.1%** | **+1.1%** |
| **number_swap** | Solver (Execution) | 86.4% (38/44) | 65.8% (25/38) | 29.5% (13/44) | 23.5% (8/34) | 100.0% (8/8) | 2.9% (1/34) | 80.0% (32/40) | 100.0% (32/32) | 0.0% (0/40) | 7.1% (3/42) | **-22.4%** | **+4.2%** | **+7.1%** |
| **operation_flip** | Decomposer (Plan) | 4.9% (2/41) | 100.0% (2/2) | 0.0% (0/41) | 2.6% (1/39) | 100.0% (1/1) | 0.0% (0/39) | 2.8% (1/36) | 0.0% (0/1) | 2.8% (1/36) | 11.1% (4/36) | **+11.1%** | **+11.1%** | **+8.3%** |
| **operation_flip** | Solver (Execution) | 13.2% (5/38) | 60.0% (3/5) | 5.3% (2/38) | 0.0% (0/45) | 0.0% (0/0) | 0.0% (0/45) | 2.2% (1/45) | 100.0% (1/1) | 0.0% (0/45) | 2.1% (1/48) | **-3.2%** | **+2.1%** | **+2.1%** |
| **semantic_logic_error** | Decomposer (Plan) | 14.0% (7/50) | 42.9% (3/7) | 8.0% (4/50) | 8.5% (4/47) | 50.0% (2/4) | 6.4% (3/47) | 0.0% (0/45) | 0.0% (0/0) | 4.4% (2/45) | 9.4% (5/53) | **+1.4%** | **+3.1%** | **+5.0%** |
| **semantic_logic_error** | Solver (Execution) | 81.8% (36/44) | 94.4% (34/36) | 11.4% (5/44) | 82.4% (42/51) | 97.6% (41/42) | 9.8% (5/51) | 73.8% (31/42) | 90.3% (28/31) | 14.3% (6/42) | 77.8% (28/36) | **+66.4%** | **+68.0%** | **+63.5%** |

## 2. Severity-Stratified Causal Defense Map (Number Swaps)
| Severity Level | Stage | Direct Catch % | Direct Corr % | Direct Prop % | CoT Catch % | CoT Corr % | CoT Prop % | Rubric Catch % | Rubric Corr % | Rubric Prop % | Ablated Prop % | Defense Δ Direct | Defense Δ CoT | Defense Δ Rubric |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mild** | Decomposer (Plan) | 9.1% (1/11) | 0.0% (0/1) | 9.1% (1/11) | 0.0% (0/12) | 0.0% (0/0) | 0.0% (0/12) | 0.0% (0/12) | 0.0% (0/0) | 0.0% (0/12) | 12.5% (1/8) | **+3.4%** | **+12.5%** | **+12.5%** |
| **Mild** | Solver (Execution) | 81.8% (9/11) | 77.8% (7/9) | 18.2% (2/11) | 10.0% (1/10) | 100.0% (1/1) | 0.0% (0/10) | 75.0% (12/16) | 100.0% (12/12) | 0.0% (0/16) | 18.2% (2/11) | **+0.0%** | **+18.2%** | **+18.2%** |
| **Moderate** | Decomposer (Plan) | 7.7% (1/13) | 0.0% (0/1) | 7.7% (1/13) | 5.6% (1/18) | 0.0% (0/1) | 5.6% (1/18) | 5.6% (1/18) | 100.0% (1/1) | 0.0% (0/18) | 6.2% (1/16) | **-1.4%** | **+0.7%** | **+6.2%** |
| **Moderate** | Solver (Execution) | 80.0% (12/15) | 58.3% (7/12) | 33.3% (5/15) | 23.1% (3/13) | 100.0% (3/3) | 0.0% (0/13) | 75.0% (9/12) | 100.0% (9/9) | 0.0% (0/12) | 5.9% (1/17) | **-27.5%** | **+5.9%** | **+5.9%** |
| **Severe** | Decomposer (Plan) | 9.1% (1/11) | 0.0% (0/1) | 9.1% (1/11) | 7.1% (1/14) | 100.0% (1/1) | 0.0% (0/14) | 6.2% (1/16) | 0.0% (0/1) | 12.5% (2/16) | 0.0% (0/13) | **-9.1%** | **+0.0%** | **-12.5%** |
| **Severe** | Solver (Execution) | 94.4% (17/18) | 64.7% (11/17) | 33.3% (6/18) | 36.4% (4/11) | 100.0% (4/4) | 9.1% (1/11) | 91.7% (11/12) | 100.0% (11/11) | 0.0% (0/12) | 0.0% (0/14) | **-33.3%** | **-9.1%** | **+0.0%** |

## 3. Best Verifier by Error Type and Stage
| Subgroup | Stage | Best Catch Strategy | Best Correction Strategy | Lowest Propagation Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **number_swap** | Decomposer (Plan) | direct | cot | cot |
| **number_swap** | Solver (Execution) | direct | cot | rubric |
| **operation_flip** | Decomposer (Plan) | direct | direct | direct |
| **operation_flip** | Solver (Execution) | direct | rubric | cot |
| **semantic_logic_error** | Decomposer (Plan) | direct | cot | rubric |
| **semantic_logic_error** | Solver (Execution) | cot | cot | cot |

## 4. Best Verifier by Severity and Stage
| Subgroup | Stage | Best Catch Strategy | Best Correction Strategy | Lowest Propagation Strategy |
| :--- | :--- | :---: | :---: | :---: |
| **Mild** | Decomposer (Plan) | direct | direct | cot |
| **Mild** | Solver (Execution) | direct | cot | cot |
| **Moderate** | Decomposer (Plan) | direct | rubric | rubric |
| **Moderate** | Solver (Execution) | direct | cot | cot |
| **Severe** | Decomposer (Plan) | direct | cot | cot |
| **Severe** | Solver (Execution) | direct | cot | rubric |

## 5. Global Strategy Win Summary
These counts summarize how often each verifier strategy wins across subgroups.

### Error-Type Map Wins
- Direct best catch wins: **5**
- CoT best catch wins: **1**
- Rubric best catch wins: **0**
- Direct best correction wins: **1**
- CoT best correction wins: **4**
- Rubric best correction wins: **1**
- Direct lowest propagation wins: **1**
- CoT lowest propagation wins: **3**
- Rubric lowest propagation wins: **2**

### Severity Map Wins
- Direct best catch wins: **6**
- CoT best catch wins: **0**
- Rubric best catch wins: **0**
- Direct best correction wins: **1**
- CoT best correction wins: **4**
- Rubric best correction wins: **1**
- Direct lowest propagation wins: **0**
- CoT lowest propagation wins: **4**
- Rubric lowest propagation wins: **2**