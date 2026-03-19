"""Main evaluation runner with CSV export and reporting."""
from pathlib import Path
from datetime import datetime
import pandas as pd
import asyncio
import sys

from evals.evaluators import (
    compare_exact_str, compare_lists, compare_subjective, compare_numbers
)
from evals.metrics import calculate_metrics, export_csv, export_metrics_summary, print_evaluation_summary, field_info
from tests.test_ai import run_single_scrape


BASE_PATH = Path.cwd()
DF_PATH = BASE_PATH / "data" / "ground_truth_evals" / "product_info.csv"
BASE_PRODUCT_URL = "https://tienda.mercadona.es/product/"


def run_evaluations(limit: int = None):
    """Run all evaluations and export results."""
    
    # Load ground truth
    df = pd.read_csv(DF_PATH, sep=";", decimal=",", na_values="-", keep_default_na=False)
    if limit:
        df = df.head(limit)
    
    print(f"\n📊 Starting evaluation of {len(df)} products...")
    
    # Run evaluations
    results = asyncio.run(run_batch_evaluation(df))

    print_evaluation_summary(results)

    metrics_summary = calculate_metrics(results)

    export_metrics_summary(metrics_summary)

    print(f"✅ Evaluation complete!\n")
    

async def run_batch_evaluation(df: pd.DataFrame):
    """Run evaluation on batch of products."""
    results = []
    tasks = []

    for idx, row in df.iterrows():
        product_id = row["ID_producto"]
        url = BASE_PRODUCT_URL + str(product_id)

        #tasks.append(run_single_evaluation(url, row.to_dict(), idx, len(df)))
        results.append(await run_single_evaluation(url, row.to_dict(), idx, len(df)))

    #results = await asyncio.gather(*tasks)
    return results


async def run_single_evaluation(product_url: str, ground_truth: dict, current: int, total: int):
    """Evaluate a single product."""
    product_id = ground_truth.get("ID_producto", "unknown")
    
    # Progress
    progress = f"[{current+1}/{total}]"
    print(f"{progress} Evaluating {product_id}...", end="", flush=True)
    
    try:
        predicted = await run_single_scrape(product_url)
        
        # Run comparisons
        comparisons = {}
        for k, v in field_info.items(): 
            if v == "exact": 
                comparisons[k] = compare_exact_str(predicted[k], ground_truth[k])
            elif v == "subjective": 
                comparisons[k] = compare_subjective(predicted[k], ground_truth[k])
            elif v == "lists": 
                comparisons[k] = compare_lists(predicted[k], ground_truth[k])
            else: 
                comparisons[k] = compare_numbers(predicted[k], ground_truth[k])
        
        return {
            "product_id": product_id,
            "url": product_url,
            "comparisons": comparisons
        }
    
    except Exception as e:
        print(f" ✗ ERROR: {e}")
        return {
            "product_id": product_id,
            "url": product_url,
            "comparisons": {},
            "error": str(e),
        }


if __name__ == "__main__":
    # Run with optional limit
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_evaluations(limit=limit)
