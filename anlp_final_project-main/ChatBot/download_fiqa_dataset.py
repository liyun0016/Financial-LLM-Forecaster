from datasets import load_dataset, DatasetDict

# Step 1: Load from Hugging Face
print("Downloading FIQA-2018 dataset from Hugging Face...")
dataset: DatasetDict = load_dataset("pauri32/fiqa-2018")

# Step 2: Save to local folder for reuse
print("Saving to disk: data/fiqa-2018/")
dataset.save_to_disk("data/fiqa-2018")

print("Done! Dataset is now available at ./data/fiqa-2018/")
