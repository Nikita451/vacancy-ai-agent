# pytest test_search_routing.py -v
# python -m pytest test_search_routing.py -v
# python -m pytest test_search_routing.py -v -s

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch
from pydantic_ai.models.function import FunctionModel
from pydantic_ai import ModelRequest, ModelResponse
from langchain_core.runnables import RunnableConfig
import pytest
from agents.scout import fetch_market_skills, skill_agent
from agents.finance import salary_agent
from agents.mentor import study_agent
from agents.auditor import quality_agent
from pydantic_ai.models.test import TestModel
from graph import app

from pydantic_ai.messages import ModelResponse, ToolCallPart, TextPart

from schema import HRState, SkillDetail, SkillMap, create_initial_state
from utils.requester import perform_search

vacancy = "Python developer"

def mock_skill_agent_behavior(messages, info):
    """Имитирует поведение LLM, управляя двухшаговым циклом."""

    print("\n\n=== 📜 ИСТОРИЯ СООБЩЕНИЙ АГЕНТА ===")
    if not messages:
        print(" История пуста (Самый первый запуск агента)")
    else:
        for i, msg in enumerate(messages):
            # Определяем, кто отправил сообщение (Пользователь / Модель)
            role = "👤 User/System" if isinstance(msg, ModelRequest) else "🤖 LLM Model"
            print(f"\n[{i}] {role} ({type(msg).__name__}):")
            
            # Перебираем внутренние части сообщения (parts)
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    print(f"   ↳ [Тип: {part.part_kind}]")
                    if part.part_kind == 'text':
                        print(f"     Текст: {part.content}")
                    elif part.part_kind == 'tool-call':
                        print(f"     Вызов тула: {part.tool_name}(args={part.args})")
                    elif part.part_kind == 'tool-return':
                        print(f"     Ответ от тула: {part.content}")
    print("===================================\n")



    # Шаг 1: Если история пуста — принудительно заставляем вызвать инструмент
    if not messages:
        return ModelResponse(parts=[
            ToolCallPart(
                tool_name="fetch_market_skills", 
                args={"specialty": vacancy}
            )
        ])
        
    # Шаг 2: Если инструмент вернул данные (tool-return), отдаем валидный JSON
    last_message = messages[-1]
    if hasattr(last_message, 'parts') and any(p.part_kind == 'tool-return' for p in last_message.parts):
        valid_skill_map = SkillMap(
            skill_map={
                "languages": [SkillDetail(name="Python", demand="critical", trend="stable")],
                "frameworks": [SkillDetail(name="FastAPI", demand="critical", trend="growing")],
                "infrastructure": [SkillDetail(name="Docker", demand="critical", trend="stable")],
                "soft_skills": [SkillDetail(name="Командная работа", demand="important", trend="stable")],
                "other": [SkillDetail(name="gRpc", demand="important", trend="stable")]
            }
        )
        return ModelResponse(parts=[TextPart(content=valid_skill_map.model_dump_json())])
        
    return ModelResponse(parts=[ToolCallPart(tool_name="fetch_market_skills", args={"specialty": vacancy})])


@pytest.mark.asyncio
# ВАЖНО: Патчим строго внутри agents.scout, так как там написан @skill_agent.tool
# Патчить нужно там, где функция используется, а не там, где она объявлена.
@patch("agents.scout.perform_search", new_callable=AsyncMock)
@patch("agents.scout.perform_searchDDG", new_callable=AsyncMock)
@pytest.mark.parametrize("engine", ["tavily", "ddg"])
async def test_full_chain_routing(
    mock_ddg, mock_tavily, engine
):
    initial_state = create_initial_state(vacancy)

     # Сбрасываем моки и задаем им дефолтные ответы
    mock_tavily.reset_mock()
    mock_ddg.reset_mock()
    mock_tavily.return_value = "Результаты поиска Tavily"
    mock_ddg.return_value = "Результаты поиска DuckDuckGo"

    with ExitStack() as stack:
        # Для skill_agent используем FunctionModel, чтобы гарантировать вызов инструмента
        stack.enter_context(skill_agent.override(model=FunctionModel(mock_skill_agent_behavior)))
        stack.enter_context(salary_agent.override(model=TestModel()))
        stack.enter_context(study_agent.override(model=TestModel()))
        stack.enter_context(quality_agent.override(model=TestModel()))

        # Запуск графа с Tavily
        config: RunnableConfig = {"configurable": {
            "thread_id": vacancy,
            "search_engine": engine,  # "tavily" or "ddg"
        }}
        await app.ainvoke(initial_state, config=config)

        # Проверяем, что роутинг пробился через всю логику
        # mock_tavily.assert_any_call(query="актуальный стек технологий и навыки Python Developer 2025 2026")
        if engine == "tavily":
            mock_tavily.assert_called()
            mock_ddg.assert_not_called()
        else:
            mock_ddg.assert_called()
            mock_tavily.assert_not_called()
