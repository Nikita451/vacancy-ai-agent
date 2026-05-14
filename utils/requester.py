import asyncio
import httpx
from tavily import AsyncTavilyClient
import os
import random
from config import Config
from ddgs import DDGS
from datetime import datetime

tavily_client = AsyncTavilyClient(api_key=Config.TAVILY_API_KEY)

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



async def perform_searchDDG(*, query: str, search_type: str = "general", max_results: int = 10) -> str:
    # Получаем текущий год динамически
    current_year = datetime.now().year
    
    filters = {
        "skills": f"{current_year} site:habr.com OR site:medium.com -курс -обучение",
        # Для зарплат год критически важен
        "salary": f"{current_year} site:habr.com OR site:getmatch.ru OR site:hh.ru зарплата вилка",
        "learning": f"{current_year} site:habr.com OR site:docs.python.org документация гайд",
        "general": f"{current_year} -курс -урок"
    }

    prefix = filters.get(search_type, filters["general"])
    enhanced_query = f"{query} {prefix}"
    
    print(f"📡 Поиск ({search_type}): {enhanced_query}")

    def sync_search():
        # Используем современный класс DDGS из новой библиотеки
        with DDGS() as ddgs:
            return list(ddgs.text(enhanced_query, max_results=max_results))

    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, sync_search)
        
        if not results:
            return "Результатов не найдено."

        return "\n\n---\n\n".join([
            f"Заголовок: {r.get('title')}\nКонтент: {r.get('body')}\nURL: {r.get('href')}" 
            for r in results
        ])
    except Exception as e:
        return f"Ошибка поиска: {e}"

# Тестовый запуск (можно закомментировать)
# if __name__ == "__main__":
#    res = asyncio.run(perform_search(query="Зарплаты Python разработчика 2026"))
#    print(res)


if __name__ == "__main__":
    asyncio.run(perform_searchDDG(query=f"site:habr.com OR site:getmatch.ru зарплаты LM-инженер"))
