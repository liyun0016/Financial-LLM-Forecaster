from model_loader import model, tokenizer
from finqa import run_finqa
from finred import run_finred
from forecaster import run_forecaster

print("\n=== Testing FinQA ===")
question_qa = "What are the benefits of investing in an ETF?"
answer_qa = run_finqa(question_qa)
print("FinQA Output:", answer_qa)

print("\n=== Testing FinRED ===")
question_re = "Tesla Inc. is headquartered in Austin and was founded by Elon Musk."
answer_re = run_finred(question_re)
print("FinRED Output:", answer_re)

print("\n=== Testing Forecaster ===")
question_forecast = "Will Microsoft stock go up next week?"
answer_forecast = run_forecaster(question_forecast, symbol="MSFT") 
print("Forecaster Output:", answer_forecast)