import csv
import json
import os
import asyncio
import pdb
from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy, CacheMode, CrawlerRunConfig, LLMConfig, \
    LXMLWebScrapingStrategy
from crawl4ai.chunking_strategy import SlidingWindowChunking
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from litellm import completion
from pydantic import BaseModel
import validators
from dotenv import load_dotenv

from src.general_info_adviser_tool.contants import OUTPUT_FILEPATH

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
You are given a text from a webpage related to investing in a country. Your task is to:

1. Analyze the **meaning and focus** of each content chunk.
2. Retain only the content that is relevant to one of the following categories:
    1. **Why Invest** – Reasons to invest in this location (e.g., economic strengths, innovation, trade access, incentives, policy support).
    2. **Where to Invest** – Recommended zones, sectors, regions, or industries for investment.
    3. **Sector Insights** – Opportunities, trends, and focus areas across industries.
    4. **Setting Up a Business** – Processes, steps, or legal requirements for registering or starting a business.
    5. **Tax & Accounting** – Tax policies, corporate tax rates, incentives, deductions, accounting standards, or compliance rules.
    6. **HR & Payroll** – Hiring practices, labor regulations, employee entitlements, payroll obligations, and workforce considerations.
3. Clean the content as needed (e.g., fix broken sentences or line breaks), and remove any duplicate or repetitive entries.
4. **Include the citation (e.g., source URL) for each chunk if available. If not, leave the citation field empty.**
""")

extraction_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="azure/gpt-4o", base_url=os.environ["AZURE_API_BASE"],
                         api_token=os.environ["AZURE_API_KEY"], temprature=0.3),
    instruction=SYSTEM_INSTRUCTIONS,
    # schema=GeneralInfo.model_json_schema(),
    extraction_type="block",
    apply_chunking=False,
    input_format="markdown",
    verbose=True)

config = CrawlerRunConfig(
    # extraction_strategy=extraction_strategy,
    cache_mode=CacheMode.BYPASS,
    scan_full_page=True,
    scraping_strategy=LXMLWebScrapingStrategy(),
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

# For separate LLM processing
# async def crawl_to_text(urls):
#     async with AsyncWebCrawler() as crawler:
#         for url, filename in urls:
#             print(f"🔗 Crawling {url}...")
#             results = await crawler.arun(url, config=config)
#             for result in results:
#                 if result.markdown.markdown_with_citations:
#                     formatted_prompt = f"Data:\n{result.markdown.markdown_with_citations}"
#                     response = completion(
#                         model="azure/gpt-4o",
#                         messages=[
#                             {"content": SYSTEM_INSTRUCTIONS, "role": "system"},
#                             {"content": formatted_prompt, "role": "user"}
#                         ],
#                         temperature=0.2
#                     )
#                     pdb.set_trace()
#                     export_to_txt(response.choices[0].message["content"], OUTPUT_FILEPATH + filename)
#         return

async def crawl_to_text(urls):
    async with AsyncWebCrawler() as crawler:
        for url, filename in urls:
            print(f"🔗 Crawling {url}...")
            results = await crawler.arun(url, config=config)
            for result in results:
                if result.markdown and result.markdown.markdown_with_citations:
                    export_to_txt(result.markdown.markdown_with_citations, OUTPUT_FILEPATH + filename, result.url)
                # if result.cleaned_html:
                #     export_to_txt(result.cleaned_html, OUTPUT_FILEPATH + filename, result.url)
        return

def export_to_txt(txt_data, filename, url):
    if not txt_data:
        print("No data to export.")
        return

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        f.write(txt_data)
        f.write("\nAbove data is from **Source url:** " + url)
        f.write("\n")

# if __name__ == "__main__":
#     asyncio.run(main())
