# import os
#
# from src.grants_recommender_tool.web_crawler import crawl_to_json, export_to_excel
#
# async def main():
#
#     recrawl_data = input("Do you want to recrawl data? (yes/no): ")
#
#     if recrawl_data.lower() == "yes":
#         urls = input("Enter URLs separated by spaces: ").split()
#         # recrawl_depth = int(input("Enter recrawl depth: "))
#         # export_to_excel(await crawl_to_json("https://www.gobusiness.gov.sg/gov-assist/grants/", 0, recrawl_depth))
#         if os.path.isfile("grants.csv"):
#             os.remove("grants.csv")
#
#         await crawl_to_json(urls)
#         # for url in urls:
#         #     export_to_excel(await crawl_to_json(url))
#
#     user_input = input("Enter grant recommendation query: ") #"I am a manufacturing company doing steel works and am looking to leverage on technology to automate my internal processes what grants can i apply for"
#     csv_file_path = "grants.csv"  # Make sure this file exists
#     print("\n🔹 Recommending Grants...\n")
#     from src.grants_recommender_tool.grant_recommender import recommend
#     recommendations = recommend(user_input, csv_file_path)
#     print("\n🔹 Recommended Grants:\n")
#     print(recommendations)
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())