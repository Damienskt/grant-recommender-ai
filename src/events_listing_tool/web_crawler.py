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

from src.events_listing_tool.contants import OUTPUT_FILENAME

load_dotenv(dotenv_path=".env")

class Event(BaseModel):
    event_title: str
    event_date: Optional[str]  # Start and end date of the event
    event_time: Optional[str]  # Start and end time of the event
    event_mode: Optional[str]  # physical, virtual, or hybrid
    event_organiser: Optional[str]
    event_summary: Optional[str]
    event_description: Optional[str]  # Detailed description parts as a list of strings
    event_venue: Optional[str]
    event_address: Optional[str]
    cost: Optional[str]  # 'paid' or 'free'
    event_type: Optional[List[str]]  # e.g., business mission, tradeshow or conference, seminar or workshop, networking event
    capability_area: Optional[List[str]]  # e.g., productivity, innovation, internationalisation, sustainability, human capital, quality & standards
    sub_capability_area: Optional[List[str]]  # Applicable when capability_area is 'internationalisation'
    industries: Optional[List[str]]  # List of industries or sectors (e.g., agritech, business services)
    market_focus: Optional[List[str]]  # e.g., asia-pacific, united states of america, no market focus
    link_to_event_page: Optional[str]

# Use secure environment variables
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

MAX_DEPTH = 4  # Allow crawling 1 level deep

SYSTEM_INSTRUCTIONS = ("""
You are given text that contains information about an event. This may be scraped from a webpage, report, or document and is in **Markdown format**. The content may include headings, bullet points, links, and other markdown elements. Your task is to extract the following fields from the text and return them as structured data in JSON format, using snake_case for all keys.

Ignore any category headers or irrelevant formatting. Extract the value for each field based on the definitions below. If a field is not present in the input, return an empty string or null for that key.

- **event_title**: The name or heading of the event.
- **event_date**: The start and end date of the event.
- **event_time**: The start and end timing of the event.
- **event_mode**: The format of the event. Possible values are "physical", "virtual", or "hybrid". (See Mode Categories below.)
- **event_organiser**: The name of the organization(s) responsible for hosting the event.
- **event_summary**: A brief 1-2 sentence overview of the event’s key value proposition and purpose.
- **event_description**: A detailed overview of the event, including:
    - Overview/objectives
    - Key topics
    - Target audience
    - Expected outcomes
    - Speaker details (if applicable)
    - Programme highlights
    - Registration information
- **event_venue**: The name of the event location or facility.
- **event_address**: The full physical location details.
- **cost**: Indicates whether the event is free or paid attendance. (See Cost Categories below.)
- **event_type**: The type of event. Possible values include "business mission", "tradeshow or conference", "seminar or workshop", or "networking event". (See Type Categories below.)
- **capability_area**: The core business capabilities or competencies that the event aims to develop for enterprises. (See Capability Area Categories below.)
- **sub_capability_area**: A detailed breakdown of the capability areas, applicable only when capability_area is 'internationalisation'. (See Sub-Capability Area Categories below.)
- **industry**: The focus industries or business sectors of the event. (See Industry Categories below.)
- **market_focus**: The specific markets or countries relevant to the event. (See Market Focus Categories below.)
- **link_to_event_page**: A URL pointing to the official event webpage.

**Categories and Definitions:**

A. **Event Mode**
   - **physical**: Events conducted in-person at a specific venue.
   - **virtual**: Events conducted entirely online.
   - **hybrid**: Events with both physical and online participation options.

B. **Cost**
   - **paid**: Events that require payment to attend.
   - **free**: Events with no registration/participation fee.

C. **Event Type**
   - **business mission**: Organized trips for SMEs to explore overseas markets and meet potential partners, government agencies, and customers.
   - **tradeshow or conference**: Platforms for SMEs to showcase products/services and engage with industry leaders on challenges, opportunities, and trends.
   - **seminar or workshop**: Events focused on knowledge sharing and capability building, including forums, roundtables, workshops, and training sessions.
   - **networking event**: Opportunities for SMEs to connect with potential partners, investors, and customers through industry mixers, pitch events, and matchmaking.

D. **Capability Area**
   - **productivity**: Events focused on improving operational efficiency, reducing costs, and optimizing business processes.
   - **innovation**: Events related to technology adoption, digital transformation, and new product/service development.
   - **internationalisation**: Events supporting overseas expansion, cross-border trade, and international market entry.
   - **sustainability**: Events covering environmental practices, ESG compliance, and sustainable business operations.
   - **human capital**: Events focused on workforce development, talent management, and leadership capabilities.
   - **quality & standards**: Events related to industry certifications, quality assurance, and standard compliance.

E. **Sub-Capability Area** (For capability_area = 'internationalisation' only)
   - **knowledge**: Events that introduce new information or skills about overseas markets.
   - **corporate operations**: Events that help companies set up and manage overseas business functions.
   - **expand network**: Events that facilitate the growth of business networks.
   - **publicity**: Events that help companies build brand awareness in overseas markets.
   - **business development**: Events that support companies in meeting potential overseas partners and expanding sales.
   - **compliance**: Events that help companies understand and meet overseas compliance requirements.
   - **export**: Events related to the export of goods/services and trade requirements.

F. **Industry**
   - Use specific tags such as "agritech", "air transport", "built environment", "business services", "electronics", "energy and chemicals", "food manufacturing", "food services", "healthcare and biomedical", "ict and media", "land transport", "logistics", "marine and offshore energy", "manufacturing & engineering", "retail", "sea transport", "urban solutions", "wholesale trade", or "all" for events relevant to any industry.

G. **Market Focus**
   - Tag events based on region or specific markets, e.g., "africa", "asia-pacific", "europe", "middle east", "north and latin america", "southeast asia", or specific countries (e.g., "united states of america", "singapore"). Use "no market focus" for agnostic events.

**Output Format:**

Return your result as a JSON object with keys exactly matching the field names above in snake_case. For example:

{
  "event_title": "sme international trade mission 2025",
  "event_date": "2025-06-01 to 2025-06-05",
  "event_time": "09:00 to 17:00",
  "event_mode": "hybrid",
  "event_organiser": "enterprise singapore",
  "event_summary": "a trade mission designed to help smes explore overseas market opportunities.",
  "event_description": "this event provides smes with the opportunity to network with international buyers, participate in workshops on market entry strategies, and attend panel discussions on regulatory requirements. the programme includes keynote speeches, roundtable discussions, and one-on-one business matching sessions.",
  "event_venue": "marina bay sands expo",
  "event_address": "10 bayfront ave, singapore 018956",
  "cost": "paid",
  "event_type": "business mission",
  "capability_area": "internationalisation",
  "sub_capability_area": "expand network",
  "industry": ["business services", "manufacturing & engineering"],
  "market_focus": ["asia-pacific", "united states of america"],
  "link_to_event_page": "https://www.enterprisesg.gov.sg/event/sme-international-trade-mission-2025"
}

Always respond as a **knowledgeable, neutral, and helpful advisor** supporting international business expansion decisions.
""")

extraction_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="azure/gpt-4o", base_url=os.environ["AZURE_API_BASE"], api_token=os.environ["AZURE_API_KEY"], temprature=0.5),
    instruction=SYSTEM_INSTRUCTIONS,
    schema=Event.model_json_schema(),
    extraction_type="schema",
    apply_chunking=False,
    input_format="markdown",
    verbose=True)

config = CrawlerRunConfig(
    extraction_strategy=extraction_strategy,
    cache_mode=CacheMode.BYPASS,
    scan_full_page=True,
    scroll_delay=1,
    delay_before_return_html=5,
    exclude_social_media_links=True,
    exclude_external_links=True,
    magic=True,
    # wait_until="domcontentloaded",
    # wait_for="js:() => window.loaded === true",
    deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=1,
            include_external=False,
            max_pages=100,
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

    # Dynamically collect all unique field names from the dataset
    all_fieldnames = set()
    for row in json_data:
        all_fieldnames.update(row.keys())
    all_fieldnames = sorted(all_fieldnames)  # Optional: sort alphabetically for readability

    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fieldnames, extrasaction='ignore')
        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()
        writer.writerows(json_data)

# if __name__ == "__main__":
#     asyncio.run(main())
