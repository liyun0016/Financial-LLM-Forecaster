import pdfplumber
import requests
import urllib3
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# PDF URL
pdf_url = "https://apps.pittsburghpa.gov/redtail/images/23255_2024_Operating_Budget.pdf"

# Download the PDF file (without SSL verification)
pdf_filename = "pittsburgh_2024_budget.pdf"
response = requests.get(pdf_url, verify=False)
with open(pdf_filename, "wb") as f:
    f.write(response.content)

print("PDF downloaded successfully.")

# Extract text from the PDF using pdfplumber
pdf_text = []
with pdfplumber.open(pdf_filename) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            pdf_text.append(text)

# Combine all pages into one string
full_text = "\n".join(pdf_text)

# Combine filename and extracted text into a single content string
combined_content = f"Filename: {pdf_filename}\nExtracted Text:\n{full_text}"

# Create final output dictionary in the format { "url": "content" }
output_data = {
    pdf_url: combined_content
}

# Save the output dictionary to a JSON file
with open("pittsburgh_2024_budget.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4, ensure_ascii=False)
