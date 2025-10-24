import os
import csv
import requests
import json
import time

API_KEY = ""
MODELS = ["meta-llama/llama-3.3-70b-instruct", "x-ai/grok-4-fast", "openai/gpt-4o-mini"]
BASE_DIR = "code"
OUTPUT_FULL_CSV = "results_full.csv"
OUTPUT_SUMMARY_CSV = "results_summary.csv"

PROMPT_TEMPLATE = """
You are a Python expert. Check the following code and answer:

1. Is there any operation in the code that could fail on a specific operating system (Linux, Mac, Windows)? 
2. If yes, explain why and on which OS it might fail, finish saying "NonPortable!!!" If it is fully portable, finish saying "Portable!!!"

Code:
{}
"""

def call_llm(model, code):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(code)}],
    }

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(data)
    )

    if response.status_code == 200:
        r_json = response.json()
        try:
            return r_json["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            return "ERROR: no content"
    else:
        return f"ERROR: status {response.status_code}"

def classify_response(response_text):
    """Detecta Portable!!! ou NonPortable!!! no texto da LLM"""
    
    if "NonPortable!!!" in response_text:
        return "nonportable"
    elif "Portable!!!" in response_text:
        return "portable"
    else:
        return "unknown"

def main():
    f_full = open(OUTPUT_FULL_CSV, "w", newline="", encoding="utf-8")
    f_sum = open(OUTPUT_SUMMARY_CSV, "w", newline="", encoding="utf-8")

    full_writer = csv.DictWriter(f_full, fieldnames=["filename", "class", "model", "response"])
    full_writer.writeheader()

    summary_writer = csv.DictWriter(f_sum, fieldnames=["filename", "class", "model", "predicted"])
    summary_writer.writeheader()

    for cls in ["portable", "nonportable"]:
        folder = os.path.join(BASE_DIR, cls)
        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                filepath = os.path.join(folder, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    code = f.read()

                for model in MODELS:
                    print(f"Processing {filename} with {model}...")
                    output = call_llm(model, code)
                    classified = classify_response(output)

                    full_writer.writerow({
                        "filename": cls + '/' + filename,
                        "class": cls,
                        "model": model,
                        "response": output
                    })
                    f_full.flush()  

                    summary_writer.writerow({
                        "filename": cls + '/' + filename,
                        "class": cls,
                        "model": model,
                        "predicted": classified
                    })
                    f_sum.flush()

                    time.sleep(1)

    f_full.close()
    f_sum.close()
    print(f"Full results saved to {OUTPUT_FULL_CSV}")
    print(f"Summary results saved to {OUTPUT_SUMMARY_CSV}")

if __name__ == "__main__":
    main()
