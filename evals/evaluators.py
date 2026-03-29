"""Evaluators for comparing predicted vs ground truth values."""
import numpy as np 

price_equivalence = {
    "muy caro": 5, 
    "caro": 4, 
    "estandar": 3, 
    "barato": 2, 
    "muy barato": 1 
}

def compare_exact_str(predicted, gold, field_name):
    """Compare exact string match (case-insensitive)."""
    p = str(predicted).strip().lower() if predicted else predicted
    g = str(gold).strip().lower() if gold else gold
    invalid = match = False 
    if g is None: 
        invalid = True 
    else: 
        match = p == g
    return {
        "passed": match,
        "invalid": invalid, 
        "truth": gold, 
        "predicted": predicted, 
        "details":  f"❌ Comparando {field_name}. Esperado: '{g}', Obtenido: '{p}'"
    }


def compare_lists(predicted_list, gold_str, field_name):
    """Compare lists using set intersection (precision, recall)."""

    # Auxiliary function to clean the data 
    def clean_to_set(data):
        if isinstance(data, str):
            return {a.strip().lower() for a in data.split(",") if a.strip()}
        elif isinstance(data, (list, set)):
            return {str(a).strip().lower() for a in data if a}
        return set()
    

    pred_set = clean_to_set(predicted_list)
    gold_set = clean_to_set(gold_str)
    
    # Calculate metrics
    intersection = gold_set.intersection(pred_set)
    precision = len(intersection) / len(pred_set) if pred_set else 1.0
    recall = len(intersection) / len(gold_set) if gold_set else 1.0
    
    # Determine pass/fail (both need to be good)
    match = precision >= 0.8 and recall >= 0.8
    
    detail = f"❌ Comparando {field_name}. Faltan: {gold_set - pred_set} | Sobran: {pred_set - gold_set}, Precision: {precision}, Recall: {recall}"
    
    return {
        "passed": match, 
        "precision": precision, 
        "recall": recall, 
        "truth": gold_str, 
        "predicted": ", ".join(predicted_list), 
        "details": detail
    }


def compare_subjective(predicted, gold_options_str, field_name):
    """Compare against multiple valid options."""
    options = [option.strip().lower() for option in gold_options_str.split("|")]
    casted_options = [price_equivalence.get(option, -1) for option in options]
    p = price_equivalence.get(str(predicted).strip().lower(), -1) if predicted else -1
    min_diff = 5
    for option in casted_options: 
        min_diff = min(min_diff, abs(p - option))
    match = min_diff == 0
    return {
        "passed": match,
        "difference": min_diff,  
        "truth": gold_options_str, 
        "predicted": predicted, 
        "details": f"❌ Comparando {field_name}. Opciones válidas: {gold_options_str}, Obtenido: '{predicted}'. Diferencia: {min_diff}"
    }


def compare_numbers(predicted, truth, field_name, tolerance=0.05):
    """Compare numeric values with relative error tolerance."""
    p = predicted
    t = truth
    try:
        p = float(predicted) 
        t = float(truth) 
        if t == 0:
            # Absolute tolerance for zero
            diff =  abs(p - t)
            match = diff < 1
        else:
            # Relative tolerance
            error = abs(p - t) / abs(t)
            match = error <= tolerance
            diff = abs(p - t)
    except Exception as e: 
        match = t == p
        if t is None: 
            diff = p if isinstance(p, float) else 0 
        else: 
            diff = t if isinstance(t, float) else 0
    
    return {
        "passed": match, 
        "difference": diff, 
        "truth": truth, 
        "predicted": predicted, 
        "details": f"❌ Comparando {field_name}. Esperado: {t}, Obtenido: {p}, Diferencia: {diff:.2f}"
    }


# New simplified functions for export/display
def evaluate_field(predicted, gold, field_name, field_type: str = "string"):
    """Generic field evaluator."""
    if field_type == "string":
        return compare_exact_str(predicted, gold, field_name)
    elif field_type == "number":
        return compare_numbers(predicted, gold, field_name)
    elif field_type == "list":
        return compare_lists(predicted, gold, field_name)
    elif field_type == "enum":
        return compare_subjective(predicted, gold, field_name)
    else:
        return compare_exact_str(predicted, gold, field_name)
