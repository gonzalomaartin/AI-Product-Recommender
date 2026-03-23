"""Evaluators for comparing predicted vs ground truth values."""
import numpy as np 

def compare_exact_str(predicted, gold, field_name):
    """Compare exact string match (case-insensitive)."""
    p = str(predicted).strip().lower() if predicted else ""
    g = str(gold).strip().lower() if gold else ""
    match = p == g
    return {
        "passed": match,
        "truth": gold, 
        "predicted": predicted, 
        "details":  f"❌ Comparando {field_name}. Esperado: '{g}', Obtenido: '{p}'"
    }


def compare_lists(predicted_list, gold_str, field_name):
    """Compare lists using set intersection (precision, recall)."""
    # Handle predicted list
    if isinstance(predicted_list, str):
        pred_set = {a.strip().lower() for a in predicted_list.split(",")}
    elif isinstance(predicted_list, (list, set)):
        pred_set = {str(a).strip().lower() for a in predicted_list if a}
    else:
        pred_set = set()
    
    # Handle gold list
    if isinstance(gold_str, str):
        gold_set = {a.strip().lower() for a in gold_str.split(",")}
    elif isinstance(gold_str, (list, set)):
        gold_set = {str(a).strip().lower() for a in gold_str if a}
    else:
        gold_set = set()
    
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
    options = [o.strip().lower() for o in gold_options_str.split("|")]
    p = str(predicted).strip().lower() if predicted else ""
    match = p in options
    return {
        "passed": match, 
        "truth": gold_options_str, 
        "predicted": predicted, 
        "details": f"❌ Comparando {field_name}. Opciones válidas: {options}, Obtenido: '{p}'"
    }


def compare_numbers(predicted, truth, field_name, tolerance=0.05):
    """Compare numeric values with relative error tolerance."""
    try:
        p = float(predicted) if predicted is not None else 0
        t = float(truth) if truth is not None else 0
    except (ValueError, TypeError):
        return {
            False, 
            0, 
            f"No se puede convertir a número: p={predicted}, t={truth}"
        }
    if t == np.nan: 
        match = p is None 
        diff = p if not match else 0
    elif t == 0:
        # Absolute tolerance for zero
        diff =  abs(p - t)
        match = diff < 1
    else:
        # Relative tolerance
        error = abs(p - t) / abs(t)
        match = error <= tolerance
        diff = abs(p - t)
    
    return {
        "passed": match, 
        "difference": diff, 
        "truth": truth, 
        "predicted": predicted, 
        "details": f"❌ Comparando {field_name}. Esperado: {t}, Obtenido: {p}, Diferencia: {diff:.2%}"
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
