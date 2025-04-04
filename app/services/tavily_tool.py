from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def tavily_search(query: str) -> str:
    response = tavily_client.search(
        query=query,
        include_images=False,
        include_image_descriptions=False
    )

    if "results" in response:
        results = response["results"]
        return "\n\n".join([f"{r['title']}: {r['content']}" for r in results[:3]])
    else:
        return "No search results found."
