from __future__ import annotations


def build_tavily_search_tool(max_results: int):
    try:
        from langchain_tavily import TavilySearch
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-tavily`. Install the packages in requirements.txt first."
        ) from exc

    return TavilySearch(max_results=max_results)
