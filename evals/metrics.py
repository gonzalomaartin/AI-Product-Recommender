"""Metrics calculation from evaluation results."""
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json 

field_info = {
    "marca": "exact",
    "precio_relativo": "subjective",
    "alergenos": "list",
    "atributos": "list",
    "energia_kj": "numbers",
    "energia_kcal": "numbers",
    "grasas_g": "numbers",
    "grasas_saturadas_g": "numbers",
    "carbohidratos_g": "numbers",
    "azucar_g": "numbers",
    "fibra_g": "numbers",
    "proteina_g": "numbers",
    "sal_g": "numbers"
}

field_metrics = {
    "exact": ["passed"], 
    "subjective": ["passed", "difference"], 
    "list": ["passed", "precision", "recall"], 
    "numbers": ["passed", "difference"]
}


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate metrics from evaluation results."""
    metrics_summary = dict()
    for i, k in enumerate(field_info): 
        metrics_summary[k] = dict()
            
    for result in results: # Iterate over each test case
        for field_name, field_type in field_info.items(): # Iterate over each field 
            for metric_name in field_metrics[field_type]: 
                metrics_summary[field_name][metric_name] = metrics_summary[field_name].get(metric_name, 0) + result["comparisons"][field_name][metric_name]
 
    for field_name in field_info: 
        for metric_name in metrics_summary[field_name]: 
            metrics_summary[field_name][metric_name] = round(metrics_summary[field_name][metric_name] / len(results), 2)

    return metrics_summary
        

def export_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Export results to CSV format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for result in results:
        product_id = result.get("product_id", "unknown")
        url = result.get("url", "")
        
        for field_name, comparison in result.get("comparisons", {}).items():
            # Extract comparison data
            if isinstance(comparison, tuple):
                if len(comparison) >= 3:
                    status, metric, detail = comparison[0], comparison[1], comparison[2]
                elif len(comparison) == 2:
                    status, detail = comparison[0], comparison[1]
                    metric = None
                else:
                    status, detail, metric = comparison[0], "", None
            else:
                status = comparison
                detail = ""
                metric = None
            
            rows.append({
                "product_id": product_id,
                "url": url,
                "field": field_name,
                "result": "PASS" if status else "FAIL",
                "detail": str(detail)[:100] if detail else "",
                "metric": str(metric)[:50] if metric else "",
            })
    
    if rows:
        keys = ["product_id", "url", "field", "result", "detail", "metric"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✓ CSV exported to {output_path}")


def export_summary(metrics_summary: dict, filename: str) -> None:
    """Export metrics summary to jsonl."""
    BASE_PATH = Path.cwd()
    report_dir = BASE_PATH / "evals" / "reports" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_dir.mkdir(parents=True, exist_ok=True)

    with open(report_dir / (filename + ".json"), "w", encoding="utf-8") as f: 
        json.dump(metrics_summary, f, indent=4, ensure_ascii=False)

    
def print_evaluation_summary(results): 
    print(json.dumps(results, indent=4, ensure_ascii=False))
    for result in results: 
        print(f"Examining product: {result["product_id"]} -> {result["url"]}")
        passed = sum(1 for field_dict in result["comparisons"].values() if field_dict["passed"] is True)
        total_fields = len(result["comparisons"])
        
        print(f" ✓ ({passed}/{total_fields})")
        for field_dict in result["comparisons"].values(): 
            if not field_dict["passed"]: 
                print("\t" + field_dict["details"])
