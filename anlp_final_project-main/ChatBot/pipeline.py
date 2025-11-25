import json
import torch
import argparse
from model_loader import model, tokenizer
from finqa import run_finqa
from finred import run_finred
from forecaster import run_forecaster
from indices import DOW_30, EURO_STOXX_50, CRYPTO


def extract_symbol_from_question(question: str) -> str:
    q = question.upper()
    for symbol in DOW_30 + EURO_STOXX_50 + CRYPTO:
        if symbol in q:
            return symbol
    return "AAPL"


def build_router_prompt(question: str) -> str:
    return f"""
You are a classification assistant for a financial question-answering system.

Your task is to read a user's financial question or statement and classify it into exactly ONE of the following module categories:

1. **FinQA** – For financial reasoning, investment strategy, tax questions, or general financial advice.
2. **FinRED** – For factual statements or questions about structured relationships between entities (e.g. CEO of a company, ownership, headquarters, manufacturers).
3. **Forecaster** – For predicting next-week stock or crypto price movement.

Only output one of: FinQA, FinRED, or Forecaster. No explanation, just the module name.

Here are examples:

Q: Who is the CEO of Microsoft?
A: FinRED

Q: Where is Tesla headquartered?
A: FinRED

Q: What companies does Meta own?
A: FinRED

Q: Apple Inc. is the manufacturer of the iPhone.
A: FinRED

Q: Microsoft Corporation developed Windows.
A: FinRED

Q: What is the best way to invest $10,000?
A: FinQA

Q: How can I reduce my credit card debt?
A: FinQA

Q: What's the difference between growth and value stocks?
A: FinQA

Q: Will AAPL stock go up next week?
A: Forecaster

Q: Do you expect TSLA to drop in the next few days?
A: Forecaster

Q: Predict the price trend for Bitcoin next week.
A: Forecaster

Now classify this input:

Input: {question}
A:"""

def central_router(question: str, max_length: int = 1024) -> str:
    prompt = build_router_prompt(question)

    tokens = tokenizer(prompt, return_tensors='pt', truncation=True, padding=True, max_length=max_length)
    tokens = {k: v.to(model.device) for k, v in tokens.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **tokens,
            max_new_tokens=10,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id
        )

    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip().lower()
    print("[Router Output]:", output_text)
    print("[Router Output Full]:", repr(output_text))  # Use repr to see all whitespace
    
    # Extract just the last answer part
    # Look for the last occurrence of "a:" and take what follows
    if "a:" in output_text:
        last_answer = output_text.split("a:")[-1].strip()
        print("[Extracted Answer]:", last_answer)
        
        if "finqa" == last_answer:
            return "FinQA"
        elif "finred" == last_answer:
            return "FinRED"
        elif "forecaster" == last_answer:
            return "Forecaster"
    
    # Fallback to default if extraction fails
    return "FinQA"  # Or choose another default


def run_pipeline(question: str) -> dict:
    model_choice = central_router(question)
    print(f"[Routing Decision] → {model_choice}")

    if model_choice == "FinRED":
        output = run_finred(question)
    elif model_choice == "FinQA":
        output = run_finqa(question)
    elif model_choice == "Forecaster":
        symbol = extract_symbol_from_question(question)
        print(f"[Extracted Symbol] → {symbol}")
        output = run_forecaster(question, symbol=symbol)
    else:
        output = "Sorry, I couldn't determine the right model to use."

    return {
        "routed_module": model_choice,
        "output": output
    }


def batch_run_from_file(dataset_path: str, save_path: str = "pipeline_outputs.jsonl"):
    with open(dataset_path, 'r') as f:
        data = [json.loads(line.strip()) for line in f]

    results = []
    for i, item in enumerate(data):
        question = item["input"]
        print(f"\n--- [{i+1}] Question ---\n{question}")
        try:
            response = run_pipeline(question)
        except Exception as e:
            response = {
                "routed_module": "Error",
                "output": f"[Error] {str(e)}"
            }

        result = {
            "input": question,
            "expected_output": item.get("output", ""),
            "instruction": item.get("instruction", ""),
            "module": item.get("module", ""),                  # ground truth module
            "routed_module": response["routed_module"],        # model-predicted module
            "pipeline_output": response["output"]              # actual model output
        }
        results.append(result)

    with open(save_path, 'w') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Output saved to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Path to dataset JSONL file")
    args = parser.parse_args()

    if args.file:
        batch_run_from_file(args.file)
    else:
        question = "Will TSLA go up next week?"
        print(run_pipeline(question))
