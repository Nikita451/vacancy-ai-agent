
from pydantic_ai import Agent, RunContext
from config import Config
from schema import AgentDeps, SalaryReport
from utils.requester import perform_search, perform_searchDDG
from langchain_core.runnables import RunnableConfig

salary_agent = Agent(
    Config.DEFAULT_MODEL,
    output_type=SalaryReport,
    tool_retries=2,
    retries=3,
    deps_type=AgentDeps,
    instructions="""
    Ты — эксперт по компенсациям в IT. 
    Твоя задача: проанализировать JSON с навыками и выдать отчет по зарплатам.
    Чем больше 'critical' навыков, тем выше 'max' граница.
    
    ТРЕБОВАНИЯ К ДАННЫМ (Рынок РФ 2026):
    1. ТАБЛИЦА: Грейды для 'Москва', 'Регионы РФ', 'Remote'.
    2. ВАЛЮТА: тыс. руб. для РФ, USD для Remote.
    3. ТРЕНД: Краткое обоснование.
    4. КОМПАНИИ: 3-5 реальных лидеров.
    """
)

@salary_agent.tool
async def fetch_salary_data(ctx: RunContext[AgentDeps], specialty: str) -> str:
    """Ищет свежие зарплатные вилки (Junior, Middle, Senior) на Хабр Карьере, HH.ru и в обзорах за 2025-2026 годы."""
    query = f"зарплата {specialty} москва 2025 2026 вилка вакансии"
    selected_engine = ctx.deps.search_engine

    print(f"💰 Ищу актуальные зарплаты для: {specialty}...Engine: {selected_engine}")

    if selected_engine == "tavily":
        return await perform_search(query)
    
    return await perform_searchDDG(query=query, search_type="salary")
