from langchain_community.tools import DuckDuckGoSearchResults

search = DuckDuckGoSearchResults(output_format="list")


def web_search(query: str):
    return search.invoke(query)