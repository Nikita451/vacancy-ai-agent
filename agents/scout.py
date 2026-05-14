from pydantic_ai import RunContext
from pydantic_ai import Agent
from schema import SkillMap
from config import Config
from utils.requester import perform_search, perform_searchDDG


skill_agent = Agent(
    Config.DEFAULT_MODEL,
    output_type=SkillMap,
    tool_retries=10,
    retries=10,
    instructions=(
        "Ты — Senior Tech Scout. Твоя задача — составить карту навыков на основе РЕАЛЬНЫХ данных из сети.\n"
        "ПРОЦЕСС:\n"
        "1. Обязательно вызови fetch_market_skills для каждой новой специальности.\n"
        "2. Проанализируй найденный контент. Ищи названия библиотек, фреймворков и облачных инструментов.\n"
        "3. Если в поиске упоминаются новые тренды 2025-2026 года (например, AI Agents, WASM, Rust-based tooling), "
        "обязательно включи их в отчет с пометкой 'growing'.\n"
        "4. ФОРМАТ: Сгруппируй всё в skill_map (languages, frameworks, infrastructure, soft-skills)."
    )
)


@skill_agent.tool
async def fetch_market_skills(ctx: RunContext[None], specialty: str) -> str:
    """Ищет в интернете актуальный стек технологий и требования для указанной специальности на 2025-2026 годы."""
    query = f"актуальный стек технологий и навыки {specialty} 2025 2026"
    print(f"🔎 Исследую рынок для: {specialty}...")
    return await perform_searchDDG(query=query, search_type="skills")
    # return await perform_search(query)
