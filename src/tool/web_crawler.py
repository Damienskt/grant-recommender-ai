import csv
import json
import os
import asyncio
import pdb
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
import validators
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

class Grant(BaseModel):
    name: str
    description: str | None
    agency: str | None
    link: str | None

# Use secure environment variables
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")  
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

MAX_DEPTH = 4  # Allow crawling 1 level deep

extraction_strategy = LLMExtractionStrategy(
    provider="azure/gpt-4o",
    api_base=os.environ["AZURE_API_BASE"],
    api_token=os.environ["AZURE_API_KEY"],
    instruction="""Extract information related to grants, specifically capturing the grant name, description, administering agency, and the URL link to the grant details. Ensure the extracted information is structured clearly and concisely, maintaining accuracy and completeness.""",
    schema=Grant.model_json_schema(),
    extraction_type="schema",
    apply_chunking=False,
    input_format="markdown",
    extra_args={"temperature": 0.1},
    verbose=True)

config = CrawlerRunConfig(
    extraction_strategy=extraction_strategy,
    cache_mode=CacheMode.BYPASS,
    scan_full_page=True,
    delay_before_return_html=2.5,
    exclude_social_media_links=True,
    magic=True
)

async def main():
    url = "https://www.wsg.gov.sg/"
    overall_combined_json = await crawl_to_json(url, 0, 1)
    print(overall_combined_json)
    export_to_excel(overall_combined_json)


async def crawl_to_json(url, current_depth, target_depth, crawled_url_list):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config) if url not in crawled_url_list else None
        crawled_url_list.append(url)
        # pdb.set_trace()

        if result and result.success and current_depth < target_depth:
            try:
                extracted_data = json.loads(result.extracted_content)
            except json.JSONDecodeError:
                print("Error: Extracted content is not valid JSON.")
                return []

            overall_combined_json = extracted_data

            for link in result.links.get("internal", []):
                if validators.url(link["href"]):
                    print(f"🔗 Crawling {link['href']}...")
                    child_data = await crawl_to_json(link["href"], current_depth + 1, target_depth, crawled_url_list)
                    overall_combined_json = overall_combined_json + child_data
            return overall_combined_json
        elif result and result.success:
            try:
                return json.loads(result.extracted_content)
            except json.JSONDecodeError:
                print("Error: Extracted content is not valid JSON.")
                return []
        else:
            return []

def export_to_excel(json_data, filename="grants.csv"):
    if not json_data:
        print("No data to export.")
        return

    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=json_data[0].keys())
        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerows(json_data)


if __name__ == "__main__":
    asyncio.run(main())