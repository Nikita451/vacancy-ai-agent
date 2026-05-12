import asyncio
import httpx
from tavily import AsyncTavilyClient
import os
import random

tavily_client = AsyncTavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

async def fetch_json(url: str, params: dict | None = None) -> dict | list:
    max_attempts = 4
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(1, max_attempts + 1):
            response = await client.get(
                url,
                params=params,
                headers={"User-Agent": "supply-chain-agent-webinar/1.0"},
            )
            if response.status_code != 429:
                response.raise_for_status()
                return response.json()

            retry_after = response.headers.get("retry-after")
            if retry_after and retry_after.isdigit():
                sleep_seconds = float(retry_after)
            else:
                sleep_seconds = min(10.0, (2 ** attempt) + random.random())

            if attempt == max_attempts:
                response.raise_for_status()
            await asyncio.sleep(sleep_seconds)

    raise RuntimeError("Unexpected fetch_json flow")

# https://www.tavily.com/
async def perform_search(query: str, *, max_results: int = 5) -> str:
    """
    Универсальная обертка над поисковым движком.
    """
    response = await tavily_client.search(
        query=query, 
        search_depth="advanced", 
        max_results=max_results
    )
    
    # Сразу форматируем в текст для агентов
    results = [
        f"Источник: {r['url']}\nКонтент: {r['content']}" 
        for r in response.get("results", [])
    ]
    return "\n\n---\n\n".join(results)
