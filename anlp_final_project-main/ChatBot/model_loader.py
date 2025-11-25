from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# # CHANGE THIS LINE TO SWITCH MODEL
# # model_name = "mistralai/Mistral-7B-Instruct-v0.2"
# model_name = "NousResearch/Hermes-2-Pro-Mistral-7B"

# # Load tokenizer and override max length
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# tokenizer.model_max_length = 4096 

# # Make sure pad token is set
# if tokenizer.pad_token is None:
#     tokenizer.pad_token = tokenizer.eos_token  

# # Load model
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     device_map="auto",
#     torch_dtype=torch.float16 
# ).eval()

model_name = "meta-llama/Llama-2-13b-chat-hf"  # You must have accepted its license on Hugging Face

tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
tokenizer.model_max_length = 4096

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
).eval()