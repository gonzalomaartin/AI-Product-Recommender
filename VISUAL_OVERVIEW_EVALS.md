# Evaluation Framework - Visual Overview

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   EVALUATION FRAMEWORK                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT: Ground Truth CSV                                   │
│  ├─ Product ID                                              │
│  ├─ Predicted data (or from AI pipeline)                    │
│  └─ Ground truth labels                                     │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────┐           │
│  │  run_eval.py (Orchestrator)                 │           │
│  │  ├─ Load CSV                                │           │
│  │  ├─ For each product:                       │           │
│  │  │  └─ run_single_evaluation()              │           │
│  │  └─ Collect all results                     │           │
│  └──────┬──────────────────────────────────────┘           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────┐           │
│  │  evaluators.py (Comparisons)                │           │
│  │  ├─ compare_exact_str()        → PASS/FAIL  │           │
│  │  ├─ compare_lists()            → P/R/F      │           │
│  │  ├─ compare_numbers()          → Error %    │           │
│  │  └─ compare_subjective()       → PASS/FAIL  │           │
│  └──────┬──────────────────────────────────────┘           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────┐           │
│  │  metrics.py (Aggregation & Export)          │           │
│  │  ├─ calculate_metrics()                     │           │
│  │  ├─ export_csv()               → CSV        │           │
│  │  ├─ export_metrics_summary()   → CSV        │           │
│  │  └─ print_summary()            → Terminal   │           │
│  └──────┬──────────────────────────────────────┘           │
│         │                                                   │
│         ▼                                                   │
│  OUTPUT: Reports                                           │
│  ├─ field_results.csv (all evaluations)                    │
│  ├─ metrics_summary.csv (statistics)                       │
│  └─ summary.txt (human readable)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
CSV Input
   │
   ├─→ Product 1 ─→ Compare Fields ─→ Metrics ─→ Result 1
   │
   ├─→ Product 2 ─→ Compare Fields ─→ Metrics ─→ Result 2
   │
   └─→ Product N ─→ Compare Fields ─→ Metrics ─→ Result N
                                            │
                                            ▼
                                      Aggregate All
                                            │
                                            ├─→ CSV Export
                                            ├─→ Terminal Summary
                                            └─→ Report Files
```

## Comparison Methods

```
┌─────────────────────────────────────────────────────────┐
│ FIELD TYPE          │ COMPARISON      │ OUTPUT         │
├─────────────────────────────────────────────────────────┤
│ String              │ Exact match     │ PASS/FAIL      │
│ (marca)             │ (case-insens)   │                │
├─────────────────────────────────────────────────────────┤
│ Categorical         │ Valid options   │ PASS/FAIL      │
│ (precio_relativo)   │ (enum)          │                │
├─────────────────────────────────────────────────────────┤
│ List                │ Jaccard         │ PASS/FAIL +    │
│ (alergenos)         │ similarity 80%  │ Precision/     │
│                     │                 │ Recall         │
├─────────────────────────────────────────────────────────┤
│ Numeric             │ Relative error  │ PASS/FAIL +    │
│ (energia_kj)        │ tolerance 5%    │ Error %        │
└─────────────────────────────────────────────────────────┘
```

## Module Responsibilities

```
┌─────────────────────┐
│  evaluators.py      │  What: Compare individual fields
│                     │  How: Various comparison algorithms
│  80 lines          │  Returns: (bool, details) tuples
└─────────────────────┘
         │
         │ (comparison results)
         ▼
┌─────────────────────┐
│  metrics.py         │  What: Aggregate results
│                     │  How: Count, calculate rates
│  110 lines         │  Returns: Dict with stats
└─────────────────────┘
         │
         │ (metrics)
         ▼
┌─────────────────────┐
│  run_eval.py        │  What: Orchestrate workflow
│                     │  How: Load data, loop products
│  140 lines         │  Returns: Full results + exports
└─────────────────────┘
```

## Input/Output

```
INPUT: CSV
┌────────────────────────┐
│ ID_producto │ marca    │
├────────────────────────┤
│ 12345       │ Aceite   │
│ 12346       │ Leche    │
│ ...         │ ...      │
└────────────────────────┘
        │
        ▼
    PROCESS
        │
        ▼
OUTPUT: Reports/

reports/2024-01-15_143022/
├── field_results.csv
│   ├─ product_id | field | result | detail | metric
│   ├─ 12345 | marca | PASS | ... | 
│   └─ 12345 | energia_kj | PASS | ... | 0.0286
│
├── metrics_summary.csv
│   ├─ type | name | value
│   ├─ OVERALL | Total Fields | 130
│   └─ FIELD | marca | 10/10 (100.0%)
│
└── summary.txt
    ├─ EVALUATION SUMMARY
    ├─ Total: 130 fields
    ├─ Passed: 115 (88.5%)
    └─ Failed: 12
```

## Comparison Example: Lists

```
Predicted: ["gluten", "lactosa"]
Ground Truth: "gluten, lactosa, soja"

Parse:
├─ Predicted set: {gluten, lactosa}
└─ Truth set: {gluten, lactosa, soja}

Calculate:
├─ Intersection: {gluten, lactosa}
├─ Precision: 2/2 = 100%
├─ Recall: 2/3 = 67%
└─ Jaccard: 2/3 = 67%

Result:
├─ Match: False (recall < 80%)
├─ Precision: 1.0
├─ Recall: 0.67
└─ Detail: "Faltan: {'soja'} | Sobran: set()"
```

## Metrics Calculation

```
Results: [product1, product2, ..., productN]
           │
           ▼
    For each field:
    ├─ Count PASS
    ├─ Count FAIL
    ├─ Count ERROR
    └─ Calculate success_rate

Aggregate:
├─ Total fields = sum of all
├─ Overall passed = sum of passes
├─ Overall success_rate = passed / total
└─ Per-field breakdown
```

## Integration Point

```
Current:
    Run Evaluation
         │
         ├─→ Load CSV
         ├─→ Use mock predictions
         └─→ Compare & export

After Integration:
    Run Evaluation
         │
         ├─→ Load CSV
         ├─→ Scrape products
         ├─→ Run AI pipeline
         ├─→ Compare & export
         └─→ (optional) Save to DB
```

## File Dependencies

```
run_eval.py
├─→ imports evaluators.py
│   └─ Uses: compare_exact_str, compare_lists, etc.
│
├─→ imports metrics.py
│   └─ Uses: calculate_metrics, export_csv, print_summary
│
└─→ imports pandas
    └─ Uses: read_csv
```

## Execution Flow

```
User runs: python evals/run_eval.py 10

    ├─ run_evaluations(limit=10)
    │  ├─ Load CSV (first 10 rows)
    │  ├─ run_batch_evaluation(df)
    │  │  ├─ For each product:
    │  │  │  └─ run_single_evaluation()
    │  │  │     ├─ Call comparators
    │  │  │     └─ Collect results
    │  │  └─ Gather all
    │  ├─ calculate_metrics(results)
    │  ├─ export_csv(results, ...)
    │  ├─ export_metrics_summary(metrics, ...)
    │  ├─ print_summary(metrics)
    │  └─ Save to reports/{timestamp}/
    │
    └─ Return {results, metrics, report_dir}
```

## Terminal Output

```
[1/10] Evaluating 12345...  ✓ (8/10)
[2/10] Evaluating 12346...  ✓ (7/10)
[3/10] Evaluating 12347...  ✗ (3/10)
...
[10/10] Evaluating 12354...  ✓ (9/10)

============================================================
EVALUATION SUMMARY
============================================================
Total fields: 100
Passed:  85 (85.0%)
Failed:  10
Errors:  5

By field:
  marca                    :   8/10 ( 80.0%)
  precio_relativo          :  10/10 (100.0%)
  alergenos                :   7/10 ( 70.0%)
  energia_kj               :  10/10 (100.0%)
============================================================
```

## Configuration Options

```
In evaluators.py:

compare_numbers(predicted, truth, tolerance=0.05)
                                   ──────────────
                                   Change here (5% default)

compare_lists(predicted_list, gold_str):
    match = precision >= 0.8 and recall >= 0.8
            ───────────────────────────────────
            Change here (80% default)
```

---

This visual overview should help you understand the structure at a glance!
