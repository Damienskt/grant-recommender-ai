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

class Grant(BaseModel):
    name: str
    short_name: str | None
    type: str | None
    valid_until: str | None
    description: str | None
    administering_agencies: list[str] | None
    supportable_activities: str | None
    benefits: str | None
    eligibility_criteria: str | None
    target_audiences: list[str] | None
    outcomes: list[str] | None
    business_needs: list[str] | None
    link: str | None

# Use secure environment variables
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY", "")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE", "")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION", "")

MAX_DEPTH = 4  # Allow crawling 1 level deep

SYSTEM_INSTRUCTIONS = ("""
You are given text that contains information about a public sector support scheme. This may be a grant, fund, programme, initiative, or incentive. Your task is to extract the following fields from the web page and return them as structured data in JSON format.

Ignore any category headers or irrelevant formatting. Extract the value for each field based on the definitions below. If a field is not present in the input, return an empty string or null for that key.

- name: The name of the grant, fund, programme, solution, initiative, or incentive (e.g., “Market Readiness Assistance”). This can include any similar type of public sector support scheme regardless of the specific label used.

- short_name: The acronym of the scheme if available (e.g., "MRA"). If no acronym is provided, use the capitalized initials of the scheme name.

- type: The type of scheme. Choose from one of the following or a close variant:
    - "Grant (financial)"
    - "Programme (non-financial)"
    - "Initiative"
    - "Loan"

- valid_until: The deadline or validity period of the scheme (e.g., "3 months", "until end of funding tranche", or a specific date).

- description: A detailed description what the scheme is intended to support. This should clearly state the purpose, focus areas, and types of challenges or opportunities the scheme is designed to address. Include specific industry domains, technologies, or business functions if mentioned.
    The description should provide enough context for an LLM to make relevant recommendations based on user intent (e.g., “I’m a startup looking to digitize operations” → recommend schemes that support digital transformation, startups, or operational efficiency).
    
    Examples of useful info to include:
        •	Target industries or technologies (e.g., manufacturing, AI, green tech)
        •	Business goals supported (e.g., market expansion, capability building)
        •	Problem types addressed (e.g., lack of skilled talent, legacy systems)
        •	Nature of support (e.g., funding for trials, access to mentorship, infrastructure credits)

    If no explicit description is provided, infer from other fields like supportable_activities, outcomes, or benefits.

- administering_agencies: The full name(s) of the agency or agencies administering the scheme.

- supportable_activities: The types of projects, themes, technologies, or company types supported by the scheme.

- benefits: Detailed information about the tangible financial benefits and any related conditions or limits (e.g., "50% support for eligible costs up to S$100,000", "salary support for 9 months").

- eligibility_criteria: Extract all detailed requirements or conditions that applicants must meet to be eligible for the scheme. Ensure the extracted information includes all necessary factors (e.g., applicant type, income limits, business size, registration status, sector-specific conditions, nationality, location, or timing requirements) so that eligibility can be fully evaluated.

- target_audiences: The intended audiences or beneficiaries of the scheme (e.g., SMEs, start-ups, specific sectors, or business maturity levels).

- outcomes: Based on the definitions below, return the relevant outcomes the scheme supports. More than one may apply.
    1. Sectoral Impact: Projects that create widespread changes across an entire industry or nation, such as implementing standardised platforms, establishing new industry benchmarks, or introducing transformative services that benefit multiple stakeholders.
    2. Innovation Project: Initiatives that explore and test novel approaches, technologies, or methodologies to solve existing problems or create new opportunities, with an emphasis on learning and iteration.
    3. Technology Adoption: Projects focused on successfully implementing and integrating established technologies into existing business operations to enhance capabilities or improve efficiency.
    4. Core Business Capability Development: Strategic initiatives that strengthen fundamental business functions and competencies, including human capital management, financial systems, operational processes, and organisational infrastructure.
    5. Training and Development: Structured programmes designed to enhance workforce capabilities through skill development, knowledge transfer, and talent management initiatives that align with organisational objectives.
    6. Thematic Project: Projects that address specific industry-focused challenges or opportunities within a defined sector (e.g., maritime, healthcare, education), delivering targeted solutions that cater to the unique characteristics of that domain.

- business_needs: Based on the definitions below, return the relevant business needs that the scheme addresses. More than one may apply.
    1. Market Expansion: Strategic initiatives to grow business presence in new market segments, either through diversification into related industries (horizontal expansion) or deeper penetration into existing market verticals.
    2. Corporate Innovation: Systematic efforts to create competitive advantages through the development and implementation of novel products, services, or operational methods, supported by structured experimentation and validation processes.
    3. Cost Management: Strategic initiatives to optimise business expenditure and improve profitability through process refinement, resource optimisation, and elimination of inefficiencies.
    4. Operational Efficiency: Projects focused on maximising productivity and streamlining existing business processes through systematic improvements in workflow, resource utilisation, and performance metrics.
    5. Business Transformation: Comprehensive organisational change initiatives that fundamentally alter business models, organisational structures, or core strategies to achieve significant performance improvements or adapt to market changes.
    6. Capability Investment: Strategic initiatives that build future-ready organisational capabilities and competencies, including investments in emerging areas such as sustainability practices, digital transformation, data analytics, or new technologies that position the organisation for long-term success.

- link: A URL pointing to the original source of the scheme information.

Return your result as a JSON object with keys exactly matching the field names above. For example:

{
  "name": "Market Readiness Assistance",
  "short_name": "MRA",
  "type": "Grant (financial)",
  "valid_until": "3 months",
  "description": "A description of the grant's purpose...",
  "administering_agencies": ["Enterprise Singapore"],
  "supportable_activities": ["Overseas business development", "in-market presence setup", "market entry consultancy"],
  "benefits": "Up to 50% funding support for eligible expenses capped at S$100,000 per market",
  "eligibility_criteria": "Singapore-registered SMEs with minimum 30% local shareholding",
  "target_audience": ["SMEs looking to expand overseas"],
  "outcomes": ["Market Expansion", "Technology Adoption"],
  "business_needs": ["Market Expansion", "Operational Efficiency"],
  "link": "https://www.wsg.gov.sg/grants/market-readiness-assistance"
}
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
    delay_before_return_html=2.5,
    exclude_social_media_links=True,
    exclude_external_links=True,
    magic=True,
    deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=0,
            include_external=False,
            max_pages=50,
            # score_threshold=0.3
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

# if __name__ == "__main__":
#     asyncio.run(main())
