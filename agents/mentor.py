from pydantic_ai import Agent, RunContext
from config import Config
from schema import StudyPlan
from utils.requester import perform_search, perform_searchDDG


study_agent = Agent(
    Config.DEFAULT_MODEL,
    output_type=StudyPlan,
    tool_retries=5,
    retries=6,
    instructions="""
    Ты — ментор по карьере в IT. 
    Твоя задача: на основе карты навыков и анализа зарплат составить план роста.
    
    ПРОЦЕСС:
    1. Изучи skill_map: в первую очередь ставь в план навыки с пометкой 'critical'.
    2. Вызови fetch_learning_resources, чтобы найти актуальные курсы (Stepik, Coursera, YouTube, документация).
    3. Раздели план на 3 четкие фазы по 30 дней: Foundation, Practice, Portfolio.
    4. В gap_analysis выдели то, что даст быстрый буст к зарплате (quick wins).
    5. Придумай проект для портфолио, который объединит самые востребованные навыки.

    ПРАВИЛА ЭКОНОМИИ:
    1. Сделай максимум 2-3 вызова fetch_learning_resources.
    2. В первом вызове ищи ресурсы по всем 'critical' навыкам сразу.
    3. Во втором вызове ищи идеи для portfolio_project.
    4. Не ищи каждый навык (типа ChatGPT, Gemini, Claude) отдельно — ищи их вместе как 'LLM Models'.
    Сделай 1–2 обобщающих запроса (например, 'ресурсы для обучения Prompt Engineering 2026') и на основе этого заполни весь план.

    Используй инструмент fetch_combined_resources, объединяя все ключевые навыки в один мощный поисковый запрос 
    (например: 'обучение Python, FastAPI, Docker, LangChain курсы документация 2026'). 
    Благодаря высокому лимиту выдачи (15 результатов), ты получишь всё необходимое за один раз
    """
)

@study_agent.tool
async def fetch_learning_resources(ctx: RunContext[None], categories: list[str]) -> str:
    """Ищет учебные материалы сразу по нескольким категориям (например, ['Python', 'Javascript'])."""
    query = f"лучшие курсы и гайды по темам: {', '.join(categories)} 2025 2026"
    print(f"📚 Групповой поиск по темам: {categories}...")  
    # return await perform_search(query, max_results=15)
    return await perform_searchDDG(query=query, search_type="learning")
