import torch
from pathlib import Path
from datasets import load_from_disk
import pandas as pd
from model_loader import model, tokenizer


def preprocess_finqa_dataset(dataset_path: str = None, sample_size: int = 100):
    """
    Load and preprocess the FIQA dataset, then return a list of questions (inputs).
    """
    if dataset_path is None:
        dataset_path = Path(__file__).parent.parent / 'data/fiqa-2018/'

    dataset = load_from_disk(dataset_path)
    dataset = dataset["test"].train_test_split(0.5, seed=42)['train']
    df = dataset.to_pandas()
    df = df[["sentence"]].rename(columns={"sentence": "input"})
    return df["input"].sample(n=sample_size, random_state=42).tolist()


def build_finqa_prompt(question: str) -> str:
    return f"""You are a financial assistant. Please answer the following question in 2–4 sentences with clear, practical advice.

Q: {question}
A:"""


def parse_finqa_output(output: str) -> str:
    return output.strip()


def run_finqa(question: str, max_new_tokens: int = 256) -> str:
    """
    Generate a financial answer using the FinQA module (powered by an LLM).
    Fixes previous issues where the model repeated few-shot answers.
    """
    prompt = build_finqa_prompt(question)
    prompt += "\n"

    print(f"\n===== PROMPT DEBUG =====\n{prompt}\n========================\n")

    # Tokenize without truncation
    tokens = tokenizer(
        prompt,
        return_tensors='pt',
        truncation=False
    )

    # Truncate manually to fit within the model's max context length
    max_input_len = getattr(model.config, "max_position_embeddings", 1024)
    for k in tokens:
        tokens[k] = tokens[k][:, -max_input_len:]

    # Move tokens to the model's device
    tokens = {k: v.to(model.device) for k, v in tokens.items()}

    # Generate model output
    with torch.no_grad():
        output_ids = model.generate(
            **tokens,
            max_new_tokens=256,  # increase from 128 or 256
            do_sample=False,
            temperature=0.0,
            early_stopping=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode and extract the final answer
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    if "### NEW QUESTION BELOW ###" in output_text:
        output_text = output_text.split("### NEW QUESTION BELOW ###")[-1]

    if "Answer:" in output_text:
        output_text = output_text.split("Answer:")[-1].strip()

    return parse_finqa_output(output_text)


