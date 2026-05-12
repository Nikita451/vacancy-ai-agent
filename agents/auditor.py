from pydantic_ai import Agent
from config import Config
from schema import QualityReport


quality_agent = Agent(
    Config.DEFAULT_MODEL,
    output_type=QualityReport,
    instructions="""
    Ты — Senior Quality Assurance Auditor. Твоя задача: проверить отчет на логическую целостность.
    
    ЧЕК-ЛИСТ ПРОВЕРКИ:
    1. СООТВЕТСТВИЕ ЗАРПЛАТ: Если в skill_map много 'critical' и 'growing' навыков, зарплаты в таблице не могут быть ниже рыночных (например, <200к для Middle в Москве).
    2. ЛОГИКА ОБУЧЕНИЯ: В learning_path должны быть в первую очередь те навыки, которые помечены как 'critical' в skill_map.
    3. ТРЕНДЫ: Если навык помечен как 'declining', он не должен быть ключевым в плане обучения или проекте.
    4. ГЕОГРАФИЯ: Проверь, чтобы разница между Москвой и Регионами была логичной (обычно 20-30%).
    
    Если найдешь серьезное противоречие — ставь is_consistent = False и снижай quality_score.
    """
)
