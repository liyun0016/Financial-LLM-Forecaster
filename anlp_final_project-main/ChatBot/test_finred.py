from finred import run_finred

samples = [
    # Case 1: Clear relation
    "Where is Tesla headquartered?",
    
    # Case 2: No valid relation
    "How did the S&P 500 and Dow Jones perform on Tuesday?",
    
    # Case 3: Mixed entity and role
    "Who founded Apple? And who is its CEO?",
    
    # Case 4: Slightly noisy but clear
    "On which stock exchange is Spotify listed?",
    
    # Case 5: Prompt-like format, reformulated as a real question
    "Who owns GitHub?"
]

for i, question in enumerate(samples):
    print(f"\n--- Sample {i+1} ---")
    print("Input Question:", question)
    output = run_finred(question)
    print("Extracted Relation:", output)
