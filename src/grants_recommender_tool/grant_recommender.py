import os

from dotenv import load_dotenv
from litellm import completion
import pandas as pd

from src.grants_recommender_tool.contants import SYSTEM_PROMPT

load_dotenv(dotenv_path=".env") 

os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")  
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

def recommend(prompt, data_file_path):
    data_string = pd.read_csv(data_file_path).to_string()
    formatted_prompt = f"User Request:\n{prompt}\n\nCSV Grants Data:\n{data_string}"
    response = completion(
        model = "azure/gpt-4o", 
        messages = [
            { "content": SYSTEM_PROMPT, "role": "system"},
            { "content": formatted_prompt,"role": "user"}
        ],
        temperature=0.2
    )

    return response.choices[0].message["content"]

# Example Usage
if __name__ == "__main__":
    user_input = input("Enter grant query:") #"I'm a startup in the AI sector looking for funding to expand my R&D efforts."
    csv_file_path = "grants.csv"  # Make sure this file exists
    print("\n🔹 Recommending Grants...\n")
    recommendations = recommend(user_input, csv_file_path)
    
    print("\n🔹 Recommended Grants:\n")
    print(recommendations)
    