import json
from pathlib import Path
from model_loader import model, tokenizer
from finqa import build_finqa_prompt
import torch

def run_finqa_test(input_text: str, max_new_tokens: int = 512):
    prompt = build_finqa_prompt(input_text)
    tokens = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True)
    tokens = {k: v.to(model.device) for k, v in tokens.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **tokens,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
        )

    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    if "Answer:" in output_text:
        return output_text.split("Answer:")[1].strip()
    return output_text.strip()


def main():
    data_path = Path("FinChatBot/data/pipeline_outputs_zero_shot.jsonl")
    with open(data_path, "r") as f:
        lines = [json.loads(l) for l in f.readlines()]

    print("\n[FinQA Output Check – First 20 Questions]")
    for i, item in enumerate(lines[:20]):
        print(f"\nQ{i+1}: {item['input']}")
        answer = run_finqa_test(item["input"])
        print(f"A{i+1}: {answer}" if answer else "[No Answer Generated]")

if __name__ == "__main__":
    main()
