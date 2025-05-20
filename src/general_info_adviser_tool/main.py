import os

from src.general_info_adviser_tool.contants import OUTPUT_FILEPATH
from src.general_info_adviser_tool.web_crawler import crawl_to_text

async def grants_main():

    recrawl_data = input("Do you want to recrawl data? (yes/no): ")

    if recrawl_data.lower() == "yes":
        # urls = input("Enter URLs separated by spaces: ").split()
        urls = [
            ("https://www.india-briefing.com/doing-business-guide/india", "business_guide_india.txt"),
            ("https://www.china-briefing.com/doing-business-guide/china", "business_guide_china.txt"),
            ("https://www.aseanbriefing.com/doing-business-guide/indonesia", "business_guide_indonesia.txt"),
            ("https://www.vietnam-briefing.com/doing-business-guide/vietnam", "business_guide_vietnam.txt"),
            ("https://www.china-briefing.com/doing-business-guide/hong-kong", "business_guide_hong_kong.txt"),
        ]

        # recrawl_depth = int(input("Enter recrawl depth: "))
        # export_to_excel(await crawl_to_json("https://www.gobusiness.gov.sg/gov-assist/grants/", 0, recrawl_depth))
        for url, filename in urls:
            if os.path.isfile(OUTPUT_FILEPATH + filename):
                os.remove(OUTPUT_FILEPATH + filename)

        await crawl_to_text(urls)
        # for url in urls:
        #     export_to_excel(await crawl_to_json(url))

    user_input = input("Enter recommendation query: ") #"I am a manufacturing company doing steel works and am looking to leverage on technology to automate my internal processes what grants can i apply for"
    txt_file_path = OUTPUT_FILEPATH + "business_guide_china.txt"  # Make sure this file exists
    print("\n🔹 Recommending...\n")
    from src.general_info_adviser_tool.general_info_advisor import recommend
    recommendations = recommend(user_input, txt_file_path)
    print("\n🔹 Recommended:\n")
    print(recommendations)

if __name__ == "__main__":
    import asyncio
    asyncio.run(grants_main())
