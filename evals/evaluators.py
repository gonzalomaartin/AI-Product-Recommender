def compare_exact(predicted, gold): 
    p = str(predicted).strip().lower() 
    g = str(gold).strip().lower() 
    return p == g, f"Esperado: {g}, Obtenido: {p}"


def compare_lists(predicted_list, gold_str): 
    gold_set = {a.strip().lower() for a in gold_str.split(",")}
    pred_set = {a.strip().lower() for a in predicted_list}

    intersection = gold_set.intersection(pred_set)
    precision = len(intersection) / len(pred_set) if pred_set else 1
    recall = len(intersection) / len(gold_set) if gold_set else 1

    return precision, recall, f"Faltan: {gold_set - pred_set} | Sobran: {pred_set - gold_set}"


def compare_subjective(predicted, gold_options_str):
    options = [o.strip().lower() for o in gold_options_str.split("|")]
    p = str(predicted).strip().lower()
    return p in options, f"Opciones válidas: {options}, Obtenido: {p}"
