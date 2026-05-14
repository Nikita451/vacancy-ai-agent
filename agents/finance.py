
from pydantic_ai import Agent, RunContext
from config import Config
from schema import SalaryReport
from utils.requester import perform_search, perform_searchDDG

salary_agent = Agent(
    Config.DEFAULT_MODEL,
    output_type=SalaryReport,
    tool_retries=2,
    retries=3,
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
async def fetch_salary_data(ctx: RunContext[None], specialty: str) -> str:
    """Ищет свежие зарплатные вилки (Junior, Middle, Senior) на Хабр Карьере, HH.ru и в обзорах за 2025-2026 годы."""
    query = f"зарплата {specialty} москва 2025 2026 вилка вакансии"
    print(f"💰 Ищу актуальные зарплаты для: {specialty}...")
    
    # return await perform_search(query, max_results=5)
    return await perform_searchDDG(query=query, search_type="salary")
