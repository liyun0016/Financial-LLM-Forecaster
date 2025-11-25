import re
import torch
from model_loader import model, tokenizer

RELATIONS = [
    'product_or_material_produced', 'manufacturer', 'distributed_by', 'industry',
    'position_held', 'original_broadcaster', 'owned_by', 'founded_by',
    'distribution_format', 'headquarters_location', 'stock_exchange', 'currency',
    'parent_organization', 'chief_executive_officer', 'director_/_manager',
    'owner_of', 'operator', 'member_of', 'employer', 'chairperson', 'platform',
    'subsidiary', 'legal_form', 'publisher', 'developer', 'brand',
    'business_division', 'location_of_formation', 'creator',
]

ALIAS_MAP = {
    "founder": "founded_by",
    "co_founder": "founded_by",
    "ceo": "chief_executive_officer",
    "ceo_of": "chief_executive_officer",
    "director": "director_/_manager"
}


def build_finred_prompt(text: str) -> str:
    relation_list = ", ".join(RELATIONS)

    prompt = f"""You are a financial information extraction assistant.

Your task is to extract **only one valid financial relation** that directly answers the given question.

Use **only** the following relation types:
{relation_list}

Format:
relation_type: entity1, entity2

📌 Rules:
- Only extract **a single relation** that directly answers the question.
- Do **not** generate any unrelated or extra relations.
- Do **not** repeat the input or instruction in the output.
- If no valid relation can be extracted, return:
None

✅ Example 1
Question: Who founded Tesla?
Answer:
founded_by: Tesla, Elon Musk

✅ Example 2
Question: Where is Amazon headquartered?
Answer:
headquarters_location: Amazon, Seattle

✅ Example 3
Question: What is the parent organization of Instagram?
Answer:
parent_organization: Instagram, Meta

[END OF EXAMPLES]

Now answer the following:
Question: {text.strip()}
Answer:"""
    return prompt


def parse_finred_output(output_text: str, source_text: str = ""):
    triples = []
    entries = re.split(r';|\n', output_text.strip())

    for entry in entries:
        entry = entry.strip().lstrip('-').strip()
        if not entry or ':' not in entry or ',' not in entry:
            continue

        try:
            rel_part, ent_part = entry.split(':', 1)
            rel = rel_part.strip().lower()
            rel = ALIAS_MAP.get(rel, rel)

            # skip hallucinated instruction reprints
            if rel in {"relation_type", "output", "text", "if no valid relation exists, return"}:
                continue

            # filter out malformed or hallucinated relation types
            if rel not in RELATIONS or not re.match(r'^[a-z_]+$', rel):
                print(f"Invalid relation type: {rel}")
                continue

            entities = [e.strip() for e in re.split(r',| and ', ent_part) if e.strip()]
            if len(entities) < 2:
                continue

            head, tails = entities[0], entities[1:]
            for tail in tails:
                triples.append((rel, head, tail))

        except Exception as e:
            print(f"Failed to parse line: {entry} | Error: {e}")
            continue

    return triples


def run_finred(text: str, max_new_tokens: int = 256) -> str:
    prompt = build_finred_prompt(text)
    tokens = tokenizer(prompt, return_tensors='pt', padding=True, truncation=False)
    tokens = {k: v.to(model.device) for k, v in tokens.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **tokens,
            max_new_tokens=48,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
            do_sample=False
        )

    full_output = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # Extract answer portion only (after Output:)
    if "Answer:" in full_output:
        output_text = full_output.split("Output:", 1)[-1]
    else:
        output_text = full_output

    # Remove hallucinated instruction/text reprints
    output_text = re.sub(r'Text\s*:\s*.*', '', output_text, flags=re.IGNORECASE)
    output_text = re.sub(r'^\s*Output\s*:\s*', '', output_text, flags=re.IGNORECASE)
    output_text = output_text.strip()

    print("\n--- Raw model output ---")
    print(output_text)
    print("------------------------\n")

    relations = parse_finred_output(output_text, text)

    if not relations:
        return "[No valid relation extracted]"

    return "; ".join([f"{r[0]}: {r[1]}, {r[2]}" for r in relations])
