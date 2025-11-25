import torch
from prompt import get_company_prompt
from model_loader import model, tokenizer

def build_forecast_prompt(question: str, symbol: str) -> str:
    """
    Construct few-shot prompt using company profile + user question and 2 examples.
    """
    intro = get_company_prompt(symbol)

    examples = """[Company Introduction]:
Apple Inc is a major player in the technology sector, trading under AAPL. From 2024-03-01 to 2024-03-08, its stock price increased from 170.00 to 174.50.

[Positive Developments]:
1. Apple announced strong iPhone 16 pre-orders.
2. Analysts raised EPS forecasts following an earnings beat.

[Potential Concerns]:
1. Ongoing antitrust lawsuits in the U.S.
2. Slower growth in iPad segment.

[Prediction & Analysis]
Prediction: Up
Analysis: Continued strength in core product lines and positive analyst sentiment should sustain momentum.

---

[Company Introduction]:
JPMorgan Chase & Co (JPM) is the largest U.S. bank by assets. Between 2024-03-01 and 2024-03-08, its stock declined from 190.20 to 187.10.

[Positive Developments]:
1. Increased dividend payout ratio announced.
2. Expansion into AI-enhanced fraud detection.

[Potential Concerns]:
1. Regulatory fines exceeding $300M.
2. Sector-wide weakness in consumer lending.

[Prediction & Analysis]
Prediction: Down
Analysis: While innovation continues, short-term headwinds from legal costs and market sentiment may weigh on stock performance.

---
"""

    return f"{examples}[Company Introduction]:\n{intro}\n\n[Question]: {question}\n[Your Forecast]:"


def run_forecaster(question: str, symbol: str) -> str:
    prompt = build_forecast_prompt(question, symbol)

    # Tokenize without setting max_length
    tokens = tokenizer(
        prompt,
        return_tensors='pt',
        padding=True,
        truncation=True  # truncate if really needed
        # Do NOT set max_length here
    )
    tokens = {k: v.to(model.device) for k, v in tokens.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **tokens,
            max_new_tokens=256,
            eos_token_id=tokenizer.eos_token_id,
            do_sample=False
        )

    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    if "[Your Forecast]:" in output_text:
        output_text = output_text.split("[Your Forecast]:")[-1].strip()
    print(f"Prompt tokenized length: {tokens['input_ids'].shape[1]}")
    return output_text
