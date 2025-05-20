import os

from dotenv import load_dotenv
from litellm import completion

from src.general_info_adviser_tool.contants import OUTPUT_FILEPATH, SYSTEM_PROMPT

load_dotenv(dotenv_path=".env")

os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

def recommend(prompt, data_file_path):
    with open(data_file_path, "r", encoding="utf-8") as file:
        text_content = file.read()
    formatted_prompt = f"User Request:\n{prompt}\n\n Data:\n{text_content}"
    response = completion(
        model="azure/gpt-4o",
        messages=[
            {"content": SYSTEM_PROMPT, "role": "system"},
            {"content": formatted_prompt, "role": "user"}
        ],
        temperature=0.2
    )

    return response.choices[0].message["content"]

# Example Usage
if __name__ == "__main__":
    user_input = input(
        "Enter query:")  #"I'm a startup in the AI sector looking for funding to expand my R&D efforts."
    text_file_path = OUTPUT_FILEPATH  # Make sure this file exists
    print("\n🔹 Recommending...\n")
    recommendations = recommend(user_input, text_file_path)

    print("\n🔹 Recommended:\n")
    print(recommendations)
