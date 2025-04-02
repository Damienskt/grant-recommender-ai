import os

from src.general_info_adviser_tool.web_crawler import crawl_to_json, export_to_excel

async def grants_main():

    recrawl_data = input("Do you want to recrawl data? (yes/no): ")

    if recrawl_data.lower() == "yes":
        # urls = input("Enter URLs separated by spaces: ").split()
        urls = [
            # "https://www.india-briefing.com/doing-business-guide/india",
            "https://www.china-briefing.com/doing-business-guide/china",
            # "https://www.vietnam-briefing.com/doing-business-guide/vietnam",
            # "https://www.aseanbriefing.com/doing-business-guide/indonesia",
            # "https://www.china-briefing.com/doing-business-guide/hong-kong",
        ]

        # recrawl_depth = int(input("Enter recrawl depth: "))
        # export_to_excel(await crawl_to_json("https://www.gobusiness.gov.sg/gov-assist/grants/", 0, recrawl_depth))
        if os.path.isfile("gen_info.csv"):
            os.remove("gen_info.csv")

        await crawl_to_json(urls)
        # for url in urls:
        #     export_to_excel(await crawl_to_json(url))

    user_input = input("Enter recommendation query: ") #"I am a manufacturing company doing steel works and am looking to leverage on technology to automate my internal processes what grants can i apply for"
    csv_file_path = "gen_info.csv"  # Make sure this file exists
    print("\n🔹 Recommending...\n")
    from src.general_info_adviser_tool.general_info_advisor import recommend
    recommendations = recommend(user_input, csv_file_path)
    print("\n🔹 Recommended:\n")
    print(recommendations)

if __name__ == "__main__":
    import asyncio
    asyncio.run(grants_main())
