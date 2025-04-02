import csv
import json
import os
import asyncio
import pdb
from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy, CacheMode, CrawlerRunConfig, LLMConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
import validators
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

class GeneralInfo(BaseModel):
    title: str
    source_url: str | None
    why_invest: str | None
    where_to_invest: str | None
    sector_insights: str | None
    setting_up_a_business: list[str] | None
    tax_and_accounting: str | None
    hr_and_payroll: str | None

# Use secure environment variables
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

MAX_DEPTH = 4  # Allow crawling 1 level deep

SYSTEM_INSTRUCTIONS = ("""
You are provided with content from a website or document about investing or conducting business in a specific country or region. Your task is to extract pertinent information related to the categories outlined below and return them as structured data in JSON format.

Categories:
	1.	Why Invest: Reasons to invest in this location (e.g., economic strengths, innovation, trade access, incentives, policy support).
	2.	Where to Invest: Recommended zones, sectors, regions, or industries for investment. ￼
	3.	Sector Insights: Opportunities, trends, and focus areas across industries.
	4.	Setting Up a Business: Processes, steps, or legal requirements for registering or starting a business.
	5.	Tax & Accounting: Tax policies, corporate tax rates, incentives, deductions, accounting standards, or compliance rules.
	6.	HR & Payroll: Hiring practices, labor regulations, employee entitlements, payroll obligations, and workforce considerations.

Instructions:
	•	Extract the value for each field based on the definitions above. If a field is not present in the input, return an empty string ("") for that key.
	•	Do not include category headers or irrelevant formatting from the source content.
	•	Ensure that the extracted information is accurate and directly corresponds to the thematic areas specified.
	•	Do not summarize or invent information—only extract what is present in the input.
	•	The tone should be clear, concise, and easy to understand.

Example Output:
{
  "title": "Doing Business in Singapore",
  "source_url": "https://example.com/singapore-investment-guide",
  "why_invest": "Singapore offers a strategic location in Southeast Asia, robust infrastructure, and a pro-business environment...",
  "where_to_invest": "Key sectors for investment include biotechnology, financial services, and information technology...",
  "sector_insights": "The fintech industry in Singapore is experiencing rapid growth, with numerous opportunities for innovation...",
  "setting_up_a_business": "To establish a business in Singapore, one must register with the Accounting and Corporate Regulatory Authority (ACRA)...",
  "tax_and_accounting": "Singapore has a corporate tax rate of 17%, with various incentives available for startups...",
  "hr_and_payroll": "The Employment Act outlines employee rights, including working hours, overtime pay, and leave entitlements..."
}
""")

extraction_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="azure/gpt-4o", base_url=os.environ["AZURE_API_BASE"],
                         api_token=os.environ["AZURE_API_KEY"], temprature=0.3),
    instruction=SYSTEM_INSTRUCTIONS,
    schema=GeneralInfo.model_json_schema(),
    extraction_type="schema",
    apply_chunking=False,
    input_format="markdown",
    verbose=True)

config = CrawlerRunConfig(
    extraction_strategy=extraction_strategy,
    cache_mode=CacheMode.BYPASS,
    scan_full_page=True,
    delay_before_return_html=2.5,
    exclude_social_media_links=True,
    exclude_external_links=True,
    magic=True,
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        include_external=False
    ),
    # markdown_generator=DefaultMarkdownGenerator()
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
                pdb.set_trace()
                if result.extracted_content:
                    overall_combined_json = overall_combined_json + json.loads(result.extracted_content)

            export_to_excel(overall_combined_json)
        return

def export_to_excel(json_data, filename="gen_info.csv"):
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
