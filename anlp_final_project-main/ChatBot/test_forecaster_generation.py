import json
from pathlib import Path
from evaluate import parse_answer  # 确保你已定义好 parse_answer 函数

# 加载数据文件
file_path = Path("FinChatBot/data/pipeline_outputs_zero_shot.jsonl")
with open(file_path, "r") as f:
    all_data = [json.loads(line.strip()) for line in f]

# 选择最后 20 条 Forecaster 样本
forecast_data = all_data[-20:]

# 用于评估
correct, total = 0, 0

# 映射预测方向关键词
def normalize_prediction(pred_text):
    pred_text = pred_text.lower()
    if "up" in pred_text:
        return "up"
    elif "down" in pred_text:
        return "down"
    else:
        return "neutral"

print("\n[Forecast Parse + Accuracy Test]\n")
for i, entry in enumerate(forecast_data):
    raw_output = entry.get("output") or entry.get("pipeline_output") or entry.get("generated")
    instruction = entry["instruction"]
    
    parsed = parse_answer(raw_output)
    predicted = parsed.get("prediction_binary")
    expected = "up" if "up" in instruction.lower() else "down" if "down" in instruction.lower() else "neutral"

    normalized_pred = normalize_prediction(predicted or "")
    
    print(f"Q{i+1}: {instruction}")
    print(f"Parsed Prediction: {normalized_pred} | Expected: {expected}\n")

    if normalized_pred == expected:
        correct += 1
    total += 1

# 输出准确率
accuracy = correct / total if total > 0 else 0
print(f"[Evaluation Result] Accuracy: {accuracy:.2%} ({correct}/{total})")
