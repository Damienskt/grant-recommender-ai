import csv
import json
import os
import asyncio
import pdb
from typing import List, Optional

from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy, CacheMode, CrawlerRunConfig, LLMConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
import validators
from dotenv import load_dotenv

from src.grants_stocktake_tool.contants import OUTPUT_FILENAME

load_dotenv(dotenv_path=".env")

class Grant(BaseModel):
    incentive_name: str
    agency_administering: Optional[str] = None
    validity_period: Optional[str] = None
    website_link: Optional[str] = None
    incentive_type: Optional[str] = None  # "Grant", "Tax Incentive", "Programme", "Loan"
    eligibility_criteria: Optional[List[str]] = None  # Bullet-point format
    other_prerequisites: Optional[str] = None
    grant_sub_category: Optional[str] = None
    activity: str
    supportable_cost_expense_items: Optional[str] = None
    funding_support: Optional[str] = None
    deliverables: Optional[str] = None
    industry: Optional[List[str]] = None  # e.g., ["Retail", "Logistics"]
    capability_areas: Optional[List[str]] = None  # e.g., ["Digitalisation", "Human Capital"]

# Use secure environment variables
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

MAX_DEPTH = 4  # Allow crawling 1 level deep

SYSTEM_INSTRUCTIONS = ("""
You are given text that contains information about a public sector support scheme. This may be a grant, tax incentive, programme, or loan. Your task is to extract the following fields from the web page and return them as structured data in JSON format.

Each extracted field must follow the specific instructions and definitions below. If a field is not present in the input, return an empty string, empty array, or null as appropriate. Your output must be in JSON format using the exact keys provided below.

IMPORTANT:  
If the scheme includes **multiple distinct activities** or **sub-categories of grants** (e.g., "Centre of Excellence Grant", "AI Grant", "Regulatory Tech Grant" under the same overarching scheme), you must treat each of them as a **separate record**.  
Each record must contain:
- The specific sub-grant or activity name in the `incentive_name`
- Any activity-specific values for cost, benefits, deliverables, etc.
- All shared fields (e.g., agency_administering, validity_period, incentive_type) duplicated across the records

---

**Fields to extract:**

- **incentive_name**: The full name of the scheme or sub-grant (e.g., “Market Readiness Assistance” or “FSTI 3.0 – AI Grant”). If the text lists sub-schemes or components, create a separate record for each.

- **agency_administering**: The full name of the agency (or agencies) responsible for administering the scheme.

- **validity_period**: The application deadline or validity period as stated on the website (e.g., “until 30 June 2025”, “open until further notice”).

- **website_link**: A valid URL that points to the official source of the information.

- **incentive_type**: Select **only one** of the following types based on the scheme’s main form of support:
    1. "Grant" – if the scheme includes any direct financial funding or reimbursement.
    2. "Tax Incentive" – if the scheme involves tax deductions, exemptions, or credits.
    3. "Programme" – if the scheme offers structured, non-financial support (e.g., training, mentorship).
    4. "Loan" – if the scheme enables applicants to take on a loan from a financial institution under preferred terms.

- **eligibility_criteria**: All eligibility requirements as stated in the content. Present the requirements in bullet point format. Do not condense, summarise, or omit any part of the original criteria.

- **other_prerequisites**: Extract **additional mandatory conditions** that are not part of the eligibility criteria but would result in application rejection if unmet. These may include conditions such as submission timelines, audit requirements, or necessary documentation. These should be clearly stated and important for a grant applicant to note.

- **grant_sub_category**: If available, include any categorisation or grouping of supportable activities (e.g., “Productivity Solutions”, “Overseas Expansion”). Leave blank if not explicitly stated.

- **activity**: The key supported activity. If multiple distinct activities are listed, each activity should result in a **separate JSON object**. Examples: “Overseas market entry”, “Productivity enhancement”, “Capability development”.

- **supportable_cost_expense_items**: A full breakdown of **tangible expense items** covered by the scheme under this activity (e.g., “salary of overseas staff”, “equipment purchase”, “marketing costs”).

- **funding_support**: The **specific financial benefits** the applicant can receive for this activity, including the **percentage, amount cap, or duration**. Examples: “Up to 70% funding support for eligible costs”, “Salary support capped at S$15,000 per staff”.

- **deliverables**: List any outputs, reports, or documentation required for disbursement or completion of the project (e.g., “Receipts”, “Final report”, “Audited statement”).

- **industry**: Choose one or more industries from the list below that are relevant to the scheme. If the scheme is not limited to any specific industry, select "All".

    - Manufacturing & Engineering
    - Sustainable Energy
    - Built Environment
    - Water and Circular Economy
    - Financial Service
    - ICT & Media
    - Food Manufacturing
    - Retail
    - Food Services
    - Agritech
    - Wholesale Trade
    - Logistics
    - Healthcare & Biomedical
    - Others
    - All

- **capability_areas**: Indicate the broad capability area(s) that the supported activity addresses. Choose one or more from the following list:
    - "Digitalisation"
    - "Internationalisation"
    - "Human Capital"
    - "Sustainability"
    - "Innovation"

    You may introduce a new capability area **only** if it applies to at least 3 schemes. Do not create a one-off or scheme-specific tag.

---

**Return your result as a list of JSON objects**, where each object corresponds to:
- A unique activity or
- A sub-scheme within a grouped scheme (e.g., different FSTI 3.0 grants)

Each object must contain all required fields in the correct format, with shared values duplicated across relevant records.
""")

extraction_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="azure/gpt-4o", base_url=os.environ["AZURE_API_BASE"], api_token=os.environ["AZURE_API_KEY"], temprature=0.5),
    instruction=SYSTEM_INSTRUCTIONS,
    schema=Grant.model_json_schema(),
    extraction_type="schema",
    apply_chunking=False,
    input_format="markdown",
    verbose=True)

config = CrawlerRunConfig(
    extraction_strategy=extraction_strategy,
    cache_mode=CacheMode.BYPASS,
    scan_full_page=True,
    delay_before_return_html=5,
    exclude_social_media_links=True,
    exclude_external_links=True,
    magic=True,
    deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=1,
            include_external=False,
            max_pages=50,
            # score_threshold=0.5
    )
)

# async def main():
#     url = "https://www.wsg.gov.sg/"
#     overall_combined_json = await crawl_to_json(url, 0, 1)
#     print(overall_combined_json)
#     export_to_excel(overall_combined_json)

async def crawl_to_json(urls):
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            print(f"🔗 Crawling {url}...")
            results = await crawler.arun(url, config=config)
            # pdb.set_trace()
            overall_combined_json = []
            for result in results:
                if result.extracted_content:
                    overall_combined_json = overall_combined_json + json.loads(result.extracted_content)

            export_to_excel(overall_combined_json)
        return


        # if result and result.success and current_depth < target_depth:
        #     try:
        #         extracted_data = json.loads(result.extracted_content)
        #     except json.JSONDecodeError:
        #         print("Error: Extracted content is not valid JSON.")
        #         return []
        #
        #     overall_combined_json = extracted_data
        #
        #     for link in result.links.get("internal", []):
        #         if validators.url(link["href"]):
        #             print(f"🔗 Crawling {link['href']}...")
        #             child_data = await crawl_to_json(link["href"], current_depth + 1, target_depth, crawled_url_list)
        #             overall_combined_json = overall_combined_json + child_data
        #     return overall_combined_json
        # elif result and result.success:
        #     try:
        #         return json.loads(result.extracted_content)
        #     except json.JSONDecodeError:
        #         print("Error: Extracted content is not valid JSON.")
        #         return []
        # else:
        #     return []

def export_to_excel(json_data, filename=OUTPUT_FILENAME):
    if not json_data:
        print("No data to export.")
        return

    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=json_data[0].keys())
        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerows(json_data)

# if __name__ == "__main__":
#     asyncio.run(main())
