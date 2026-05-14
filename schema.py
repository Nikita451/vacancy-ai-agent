from dataclasses import dataclass
import os
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Optional, TypedDict
from datetime import datetime

# Skills
class SkillDetail(BaseModel):
    name: str = Field(description="Название навыка (например, Python или Docker)")
    demand: Literal["critical", "important", "nice-to-have"] = Field(
        description="Востребованность на рынке"
    )
    trend: Literal["growing", "stable", "declining"] = Field(
        description="Тренд популярности навыка"
    )

class SkillMap(BaseModel):
    # Используем str для ключей, но в описании жестко задаем список
    skill_map: Dict[str, List[SkillDetail]] = Field(
        description=(
            "Словарь категорий. Допустимые ключи строго: "
            "'languages', 'frameworks', 'infrastructure', 'soft-skills', 'other'."
        )
    )

# Salary
class SalaryStats(BaseModel):
    min: float
    median: float
    max: float

class SalaryReport(BaseModel):
    # Грейд (Junior/Middle...) -> Регион (Москва/РФ/Remote) -> Статистика
    grades_table: Dict[str, Dict[str, SalaryStats]] = Field(
        description="Матрица зарплат: грейд x регион. Значения в тыс. руб. или USD (укажи в обосновании)."
    )
    market_trend: str = Field(description="growing/stable/declining + краткое обоснование (1-2 предложения)")
    top_employers: List[str] = Field(description="Список из 3-5 реальных компаний (например: Sber, Yandex, Ozon, Tinkoff, Avito)")


# Study Plan
class Resource(BaseModel):
    name: str
    resource_type: Literal["курс", "книга", "документация", "статья"]
    url: str | None = None

class LearningPhase(BaseModel):
    phase_name: str
    topics: List[str]
    resources: List[Resource] = Field(description="Минимум 2 ресурса")
    milestone: str = Field(description="Конкретный результат в конце фазы")

class GapAnalysis(BaseModel):
    quick_wins: List[str] = Field(description="Навыки, которые осваиваются за 2-4 недели")
    long_term: List[str] = Field(description="Фундаментальные знания, требующие 3+ месяца")

class PortfolioProject(BaseModel):
    title: str
    description: str
    stack: List[str]

class StudyPlan(BaseModel):
    learning_path: List[LearningPhase] = Field(description="3 фазы по 30 дней")
    gap_analysis: GapAnalysis
    portfolio_project: PortfolioProject

class QualityReport(BaseModel):
    quality_score: int = Field(ge=0, le=100, description="Оценка целостности от 0 до 100")
    is_consistent: bool = Field(description="True, если данные во всех частях отчета не противоречат друг другу")
    warnings: List[str] = Field(description="Список найденных нестыковок или подозрительных данных")
    reasoning: str = Field(description="Краткое обоснование оценки (2-3 предложения)")

class GraphConfiguration(BaseModel):
    search_engine: Literal["tavily", "ddg"] = Field(
        default="ddg",
        description="Выбор поискового движка"
    )

@dataclass
class AgentDeps:
    search_engine: Literal["tavily", "ddg"]

class HRState(TypedDict):
    scenario_id: str
    scenario_label: str
    vacancy_name: str
    generated_at: str # Время запуска
    logs: List[str]   # Список всех действий системы
    # Результаты агентов (ваши Pydantic модели)
    skill_map: Optional[SkillMap]
    salary_report: Optional[SalaryReport]
    study_plan: Optional[StudyPlan]
    quality_report: Optional[QualityReport]
    # Список критических замечаний для доработки
    warnings: List[str]

def create_initial_state(vacancy: str, scenario_id: str = "default", label: str = "test") -> HRState:
    return {
       "scenario_id": "_".join(vacancy.lower().split()),
        "scenario_label": vacancy,
        "vacancy_name": vacancy,
        "generated_at": datetime.now().isoformat(),
        "logs": [],
        "skill_map": None,
        "salary_report": None,
        "study_plan": None,
        "quality_report": None,
        "warnings": [],
    }