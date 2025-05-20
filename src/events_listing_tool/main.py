import os
import pdb

import pandas as pd
from litellm import completion

from src.events_listing_tool.contants import OUTPUT_FILENAME, POST_OUTPUT_FILENAME
from src.events_listing_tool.post_csv_deduplication import merge_csv_records_by_name
from src.events_listing_tool.web_crawler import crawl_to_json

async def main():
    recrawl_data = input("Do you want to recrawl data? (yes/no): ")

    if recrawl_data.lower() == "yes":
        # urls = input("Enter URLs separated by spaces: ").split()
        urls = [
            # "https://members.sbf.org.sg/event",
            "https://members.sbf.org.sg/training?page=1",
            "https://members.sbf.org.sg/training?page=2",
            "https://members.sbf.org.sg/training?page=3",
            # "https://members.sbf.org.sg/businessmissions",
            # "https://www.sgtech.org.sg/upcomingEvents",
            # "https://smecentre-sccci.sg/past-events"
        ]

        # recrawl_depth = int(input("Enter recrawl depth: "))
        # export_to_excel(await crawl_to_json("https://www.gobusiness.gov.sg/gov-assist/grants/", 0, recrawl_depth))
        if os.path.isfile(OUTPUT_FILENAME):
            os.remove(OUTPUT_FILENAME)

        await crawl_to_json(urls)
        merge_csv_records_by_name(OUTPUT_FILENAME, POST_OUTPUT_FILENAME, 'event_title')
        # for url in urls:
        #     export_to_excel(await crawl_to_json(url))
    # post_data_cleaning()
    user_input = input(
        "Enter event recommendation query: ")  #"I am a manufacturing company doing steel works and am looking to leverage on technology to automate my internal processes what grants can i apply for"
    csv_file_path = POST_OUTPUT_FILENAME  # Make sure this file exists
    print("\n🔹 Recommending Events...\n")
    from src.events_listing_tool.events_recommender import recommend
    recommendations = recommend(user_input, csv_file_path)
    print("\n🔹 Recommended Events:\n")
    print(recommendations)

import os
import pandas as pd

def post_data_cleaning(file_path=OUTPUT_FILENAME, output_path=POST_OUTPUT_FILENAME):
    # Read CSV file and convert to CSV string
    df = pd.read_csv(file_path)
    data_string = df.to_csv(index=False)

    SYSTEM_PROMPT = """
    You are given CSV data that contains detailed information about government-organized events. The CSV may include multiple rows with the same event title, where each row contains additional or complementary details for that event. Your task is to:

    1. Process the CSV data.
    2. Identify rows that share the same event title.
    3. Merge rows with the same event title into a single consolidated event entry. When merging:
       - Ensure that all key information is preserved.
       - If a field appears in multiple rows, combine the information appropriately (for example, concatenate descriptions, merge lists without duplicates, etc.).
    4. Do not remove any events that do not have duplicate rows; include non-duplicate events in the final output as they are.
    5. Output the final consolidated result in CSV format, ensuring that each event is represented as a single row. Use snake_case for all column headers.

    For example, if the CSV data includes two rows with the event title "Tech Expo 2025" — one row providing details on event date, time, and summary, and another row providing additional information on venue and cost — your final CSV output should contain one row for "Tech Expo 2025" that includes all merged details from both rows. Events that appear only once should remain unchanged.

    **Important:** Return only the CSV data in your response, with no additional commentary, explanation, or formatting.
    """

    formatted_prompt = f"User Request:\n{SYSTEM_PROMPT}\n\nCSV Events Data:\n{data_string}"

    response = completion(
        model="azure/gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": formatted_prompt}
        ],
        temperature=0.3
    )

    lines = response.choices[0].message["content"].splitlines()
    result = "\n".join(lines[1:-1])

    # Write the consolidated CSV output to the specified output file
    with open(output_path, mode="w", encoding="utf-8") as f:
        f.write(result)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
