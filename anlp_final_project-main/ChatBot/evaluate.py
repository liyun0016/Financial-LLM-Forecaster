import json
import re
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import accuracy_score, mean_squared_error
from rouge_score import rouge_scorer
from sentence_transformers import SentenceTransformer, util

# --- Load embedding model for FinQA ---
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# --- FinRED Soft Match Utilities ---
def extract_tuples(text):
    tuples = []
    for item in text.strip().strip('.').split(';'):
        match = re.match(r'^([a-z_]+):\s*(.*?),\s*(.*?)$', item.strip())
        if match:
            rel, h, t = match.groups()
            tuples.append((rel.strip(), h.strip(), t.strip()))
    return tuples

def normalize_entity(entity: str) -> str:
    return entity.lower().strip().replace("’", "'").replace("`", "'")

def normalize_triple(triple):
    rel, head, tail = triple
    return (rel.lower().strip(), normalize_entity(head), normalize_entity(tail))

def soft_match(a: str, b: str, threshold: float = 0.7) -> bool:
    a, b = a.lower(), b.lower()
    overlap = sum(1 for ch in a if ch in b)
    return (overlap / max(len(a), len(b))) >= threshold

def soft_match_triples(pred_triples, gold_triples, threshold=0.7):
    matched = 0
    for gt in gold_triples:
        for pt in pred_triples:
            if gt[0] == pt[0] and soft_match(gt[1], pt[1], threshold) and soft_match(gt[2], pt[2], threshold):
                matched += 1
                break
    return matched

# --- FinForecaster Parser ---
def parse_answer(answer):
    try:
        answer = answer.strip()
        pros_match = re.search(r"\[?Positive\s*Developments\]?:?\s*(.*?)\s*(?=\[|\Z)", answer, re.DOTALL | re.IGNORECASE)
        cons_match = re.search(r"\[Potential Concerns\]:\s*(.*?)\s*\[", answer, re.DOTALL)
        pred_anal_match = re.search(r"\[Prediction & Analysis\](.*)", answer, re.DOTALL)
        if not (pros_match and cons_match and pred_anal_match):
            return None
        pros = pros_match.group(1).strip()
        cons = cons_match.group(1).strip()
        pna_block = pred_anal_match.group(1).strip()

        pred_match = re.search(r"Prediction\s*[:\-]?\s*(.*)", pna_block, re.IGNORECASE)
        anal_match = re.search(r"Analysis\s*[:\-]?\s*(.*)", pna_block, re.IGNORECASE)

        pred_text = pred_match.group(1).strip() if pred_match else pna_block.split("\n")[0].strip()
        anal_text = anal_match.group(1).strip() if anal_match else " ".join(pna_block.split("\n")[1:]).strip()

        pred_bin = 0
        if re.search(r'\b(up|increase|bull|rise|gain|positive)\b', pred_text, re.IGNORECASE):
            pred_bin = 1
        elif re.search(r'\b(down|decrease|bear|drop|fall|negative)\b', pred_text, re.IGNORECASE):
            pred_bin = -1

        match_res = re.search(r'(\d+)\s*[-–~to]{1,3}\s*(\d+)\s*%', pred_text)
        if match_res:
            lower = int(match_res.group(1))
            upper = int(match_res.group(2))
            pred_margin = pred_bin * ((lower + upper) / 2)
        else:
            match_res = re.search(r'(\d+(\.\d+)?)\s*%', pred_text)
            pred_margin = pred_bin * float(match_res.group(1)) if match_res else 0.0

        return {
            "positive developments": pros,
            "potential concerns": cons,
            "prediction": pred_margin,
            "prediction_binary": pred_bin,
            "analysis": anal_text
        }
    except:
        return None

# --- Evaluation Entrypoint ---
def evaluate_pipeline_with_softmatch(jsonl_path):
    with open(jsonl_path) as f:
        data = [json.loads(line) for line in f]

    finqa_scores, finred_gold, finred_pred = [], [], []
    forecast_outputs, forecast_refs, forecast_instrs = [], [], []

    for i, entry in enumerate(data):
        module = entry.get("module", None)
        instr = entry["instruction"]
        gt = entry["expected_output"].strip()
        pred = entry["pipeline_output"].strip()

        if module == "FinQA":
            emb_ref = embedder.encode(gt, convert_to_tensor=True)
            emb_pred = embedder.encode(pred, convert_to_tensor=True)
            score = util.cos_sim(emb_ref, emb_pred).item()
            finqa_scores.append(score)

        elif module == "FinRED":
            gold = set(normalize_triple(t) for t in extract_tuples(gt))
            pred = set(normalize_triple(t) for t in extract_tuples(pred))
            finred_gold.append(gold)
            finred_pred.append(pred)

        elif module == "Forecaster":
            forecast_outputs.append(pred)
            forecast_refs.append(gt)
            forecast_instrs.append(instr)

    if finqa_scores:
        print(f"\n[FinQA Evaluation] Avg Cosine Similarity: {sum(finqa_scores)/len(finqa_scores):.4f}")

    if finred_gold:
        soft_tp = sum(soft_match_triples(p, g) for p, g in zip(finred_pred, finred_gold))
        total_pred = sum(len(p) for p in finred_pred)
        total_gold = sum(len(g) for g in finred_gold)
        prec = soft_tp / total_pred if total_pred else 0
        rec = soft_tp / total_gold if total_gold else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        print(f"\n[FinRED Evaluation - Soft Match ≥80%] Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f}")

    if forecast_refs:
        print("\n[Forecaster Evaluation]")
        correct, total = 0, 0
        for instr, output in zip(forecast_instrs, forecast_outputs):
            expected = "up" if "up" in instr.lower() else "down" if "down" in instr.lower() else "neutral"
            parsed = parse_answer(output)
            pred_bin = parsed.get("prediction_binary") if parsed else None
            pred_text = "up" if pred_bin == 1 else "down" if pred_bin == -1 else "neutral"
            if pred_text == expected:
                correct += 1
            total += 1
        acc = correct / total if total else 0
        print(f"Instruction-Based Accuracy: {acc:.2%} ({correct}/{total})")

    print(f"\n[Routing Check]")
    misroute_count = 0
    for idx, entry in enumerate(data):
        true_type = entry.get("module", None)
        predicted_type = entry.get("routed_module", None)

        if not true_type:
            if "stock price" in entry["input"].lower():
                true_type = "Forecaster"
            elif any(term in entry["input"].lower() for term in ["ceo", "headquarters", "founded"]):
                true_type = "FinRED"
            else:
                true_type = "FinQA"
        
        if predicted_type != true_type:
            misroute_count += 1
            print(f"[{idx+1}] Wrong route → Expected: {true_type}, Got: {predicted_type}")
            
    print(f"Total Misrouted: {misroute_count}/{len(data)} → Accuracy: {(1 - misroute_count/len(data)):.2%}")


# Example usage:
evaluate_pipeline_with_softmatch("FinChatBot/data/pipeline_outputs_Hermes.jsonl")