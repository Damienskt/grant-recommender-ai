import os

from src.grants_stocktake_tool.contants import OUTPUT_FILENAME, POST_PROCESSED_OUTPUT
from src.grants_stocktake_tool.post_csv_deduplication import merge_csv_records_by_name
from src.grants_stocktake_tool.web_crawler import crawl_to_json, export_to_excel

async def grants_main():

    recrawl_data = input("Do you want to recrawl data? (yes/no): ")

    if recrawl_data.lower() == "yes":
        # urls = input("Enter URLs separated by spaces: ").split()
        urls = [
            "https://www.mas.gov.sg/schemes-and-initiatives/fsti-scheme",
            "https://www.mas.gov.sg/schemes-and-initiatives/artificial-intelligence-and-data-analytics-aida-grant",
            "https://www.mas.gov.sg/development/fintech/mas-fsti-innovation-acceleration-track---early-innovation",
            "https://www.mas.gov.sg/schemes-and-initiatives/fsti-esg-fintech-grant",
            "https://www.mas.gov.sg/development/fintech/regtech-grant",
            "https://www1.bca.gov.sg/buildsg/buildsg-transformation-fund/productivity-innovation-project",
            "https://www.stb.gov.sg/licensing-support/grants/business-improvement-fund",
            "https://www.stb.gov.sg/licensing-support/grants/experience-step-up-fund/",
            "https://www.startupsg.gov.sg/programmes/4897/startup-sg-tech",
            "https://www.sportsingapore.gov.sg/support-resources/support-for-sport-businesses/grants/the-enterprise-innovation-and-capability/",
            "https://www.ncss.gov.sg/grants/organisation-development/tech-and-go/start-digital/",
            "https://www.ncss.gov.sg/grants/organisation-development/tech-and-go/consultancy-subsidy/",
            "https://www.mpa.gov.sg/maritime-singapore/what-maritime-singapore-offers/programmes-to-support-your-maritime-business/maritime-cluster-fund-(mcf)",
            "https://www.mpa.gov.sg/maritime-singapore/what-maritime-singapore-offers/programmes-to-support-your-maritime-business/mint-fund",
            "https://www.caas.gov.sg/who-we-are/areas-of-responsibility/developing-the-industry/aviation-development-fund",
            "https://www.sfa.gov.sg/recognition-programmes-grants/grants/agri-food-cluster-transformation-act-fund",
            "https://www.imda.gov.sg/how-we-can-help/5g-open-testbed",
            "https://www.iras.gov.sg/digital-collaboration/for-software-developers/accounting-tax-software/iras-digital-integration-incentive-(dii)",
            "https://www.enterprisesg.gov.sg/financial-support/enterprise-development-grant",
            "https://www.imda.gov.sg/how-we-can-help/smes-go-digital",
            "https://www1.bca.gov.sg/buildsg/buildsg-transformation-fund/growth-and-transformation-scheme",
            "https://www.enterprisesg.gov.sg/financial-support/productivity-solutions-grant",
            "https://www.sgsocialsupport.com/resource/4KwjxJ5Sfxy",
            "https://www.enterprisesg.gov.sg/grow-your-business/innovate-with-us/innovation-talent/technology-for-enterprise-capability-upgrading",
            "https://www.imda.gov.sg/how-we-can-help/smes-go-digital/advanced-digital-solutions",
            "https://www.wsg.gov.sg/home/employers-industry-partners/workforce-development-job-redesign/omip-for-employers",
            "https://www.enterprisesg.gov.sg/financial-support/double-tax-deduction-for-internationalisation",
            "https://www.enterprisesg.gov.sg/financial-support/market-readiness-assistance-grant",
            "https://www.enterprisesg.gov.sg/financial-support/local-enterprise-and-association-development-programme",
            "https://www.enterprisesg.gov.sg/grow-your-business/boost-capabilities/talent-attraction-and-development/career-conversion-programme---internationalisation-professionals"
        ]

        # recrawl_depth = int(input("Enter recrawl depth: "))
        # export_to_excel(await crawl_to_json("https://www.gobusiness.gov.sg/gov-assist/grants/", 0, recrawl_depth))
        if os.path.isfile(OUTPUT_FILENAME):
            os.remove(OUTPUT_FILENAME)

        await crawl_to_json(urls)
        # for url in urls:
        #     export_to_excel(await crawl_to_json(url))
        merge_csv_records_by_name(OUTPUT_FILENAME, POST_PROCESSED_OUTPUT, 'incentive_name')

    user_input = input("Enter grant recommendation query: ") #"I am a manufacturing company doing steel works and am looking to leverage on technology to automate my internal processes what grants can i apply for"
    # csv_file_path = OUTPUT_FILENAME  # Make sure this file exists
    print("\n🔹 Recommending Grants...\n")
    from src.grants_recommender_tool.grant_recommender import recommend
    recommendations = recommend(user_input, POST_PROCESSED_OUTPUT)
    print("\n🔹 Recommended Grants:\n")
    print(recommendations)


if __name__ == "__main__":
    import asyncio
    asyncio.run(grants_main())
