import json
from pathlib import Path
from difflib import SequenceMatcher
from finred import run_finred, parse_finred_output

# --- Normalization & Matching ---
def normalize_entity(entity: str) -> str:
    return entity.lower().strip().replace("’", "'").replace("`", "'")

def normalize_triple(triple):
    rel, head, tail = triple
    return (rel.lower().strip(), normalize_entity(head), normalize_entity(tail))

def similar(a: str, b: str, threshold: float = 0.85) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold

# --- Relation Aliases for Soft Match ---
RELATION_ALIASES = {
    'employer': {'founded_by', 'owner_of', 'member_of'},
    'founded_by': {'employer', 'owner_of'},
    'owner_of': {'founded_by', 'employer'},
    'manufacturer': {'product_or_material_produced'},
    'product_or_material_produced': {'manufacturer'},
    'platform': {'distribution_format'},
    'headquarters_location': {'location_of_formation'},
}

def relation_soft_equal(r1, r2):
    return r1 == r2 or r1 in RELATION_ALIASES.get(r2, set()) or r2 in RELATION_ALIASES.get(r1, set())

def entity_alias_equal(e1: str, e2: str) -> bool:
    return normalize_entity(e1) == normalize_entity(e2) or similar(e1, e2)

def soft_match(t1, t2) -> bool:
    r1, h1, t1_ = t1
    r2, h2, t2_ = t2
    return (
        relation_soft_equal(r1, r2) and
        entity_alias_equal(h1, h2) and
        entity_alias_equal(t1_, t2_)
    )

def evaluate_soft_f1(gold_triples_list, pred_triples_list):
    soft_tp = 0
    total_pred = 0
    total_gold = 0

    for gold_set, pred_set in zip(gold_triples_list, pred_triples_list):
        matched = set()
        for pred in pred_set:
            for gold in gold_set:
                if soft_match(pred, gold) and gold not in matched:
                    soft_tp += 1
                    matched.add(gold)
                    break
        total_pred += len(pred_set)
        total_gold += len(gold_set)

    precision = soft_tp / total_pred if total_pred else 0
    recall = soft_tp / total_gold if total_gold else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    return precision, recall, f1

# --- Load Data ---
file_path = Path("FinChatBot/data/test_finred_examples.jsonl")
with file_path.open("r") as f:
    all_data = [json.loads(l.strip()) for l in f.readlines()]

gold_triples = []
pred_triples = []

print("\n[FinRED Output Check – Custom Evaluation Set]\n")

for idx, entry in enumerate(all_data, start=1):
    input_text = entry["input"]
    expected_output = entry["expected_output"]

    print(f"Q{idx}: {input_text}")
    output = run_finred(input_text)
    print(f"A{idx}: {output}\n")

    gold = set([normalize_triple(t) for t in parse_finred_output(expected_output, input_text)])
    pred = set([normalize_triple(t) for t in parse_finred_output(output, input_text)])

    print(f"Expected: {gold}")
    print(f"Predicted: {pred}")
    print(f"TP: {len(gold & pred)}, FP: {len(pred - gold)}, FN: {len(gold - pred)}\n")

    gold_triples.append(gold)
    pred_triples.append(pred)

# --- Exact Match Evaluation ---
tp = sum(len(g & p) for g, p in zip(gold_triples, pred_triples))
total_pred = sum(len(p) for p in pred_triples)
total_gold = sum(len(g) for g in gold_triples)

precision_exact = tp / total_pred if total_pred else 0
recall_exact = tp / total_gold if total_gold else 0
f1_exact = 2 * precision_exact * recall_exact / (precision_exact + recall_exact) if (precision_exact + recall_exact) else 0

# --- Soft Match Evaluation ---
precision_soft, recall_soft, f1_soft = evaluate_soft_f1(gold_triples, pred_triples)

# --- Final Report ---
print("\n[FinRED Evaluation Metrics]")
print(f"[Exact Match] Precision: {precision_exact:.4f} | Recall: {recall_exact:.4f} | F1: {f1_exact:.4f}")
print(f"[Soft Match ] Precision: {precision_soft:.4f} | Recall: {recall_soft:.4f} | F1: {f1_soft:.4f}")
