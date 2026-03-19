"""Evaluators for comparing predicted vs ground truth values."""


def compare_exact_str(predicted, gold):
    """Compare exact string match (case-insensitive)."""
    p = str(predicted).strip().lower() if predicted else ""
    g = str(gold).strip().lower() if gold else ""
    match = p == g
    return match, f"Esperado: '{g}', Obtenido: '{p}'"


def compare_lists(predicted_list, gold_str):
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
    
    detail = f"Faltan: {gold_set - pred_set} | Sobran: {pred_set - gold_set}, Precision: {precision}, Recall: {recall}"
    
    return match, precision, recall, detail


def compare_subjective(predicted, gold_options_str):
    """Compare against multiple valid options."""
    options = [o.strip().lower() for o in gold_options_str.split("|")]
    p = str(predicted).strip().lower() if predicted else ""
    match = p in options
    return match, f"Opciones válidas: {options}, Obtenido: '{p}'"


def compare_numbers(predicted, truth, tolerance=0.05):
    """Compare numeric values with relative error tolerance."""
    try:
        p = float(predicted) if predicted is not None else 0
        t = float(truth) if truth is not None else 0
    except (ValueError, TypeError):
        return False, 0, f"No se puede convertir a número: p={predicted}, t={truth}"
    
    if t == 0:
        # Absolute tolerance for zero
        diff = abs(p - t)
        match = diff < 0.01
    else:
        # Relative tolerance
        error_pct = abs(p - t) / abs(t)
        match = error_pct <= tolerance
        diff = error_pct
    
    return match, diff, f"Esperado: {t}, Obtenido: {p}, Error: {diff:.2%}"


# New simplified functions for export/display
def evaluate_field(predicted, gold, field_type: str = "string"):
    """Generic field evaluator."""
    if field_type == "string":
        return compare_exact_str(predicted, gold)
    elif field_type == "number":
        return compare_numbers(predicted, gold)
    elif field_type == "list":
        return compare_lists(predicted, gold)
    elif field_type == "enum":
        return compare_subjective(predicted, gold)
    else:
        return compare_exact_str(predicted, gold)
