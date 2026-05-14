from datetime import datetime

from pydantic import BaseModel
from agents.scout import skill_agent
from agents.finance import salary_agent
from agents.mentor import study_agent
from agents.auditor import quality_agent
from schema import AgentDeps, HRState
from utils.format import safe_dump
from utils.telemetry import run_with_telemetry
import json
from langchain_core.runnables import RunnableConfig

async def skill_node(state: HRState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    selected_engine = configurable.get("search_engine", "ddg")
    dependencies = AgentDeps(search_engine=selected_engine)
    print(f"🔎 Узел: Поиск навыков...Search engine: {selected_engine}")
    
    log_entry = f"[{datetime.now()}] Skill Agent started searching for {state['vacancy_name']}"
    # result = await skill_agent.run(state["vacancy_name"])
    
    result = await run_with_telemetry(
        skill_agent,
        state["vacancy_name"],
        scenario_id=state["scenario_id"],
        scenario_label=state["scenario_label"],
        framework="langgraph",
        step="skill_agent.run",
        deps=dependencies,
    )
    return {
      "skill_map": result.output,
      "logs": state.get("logs", []) + [log_entry]
    }

async def salary_node(state: HRState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    selected_engine = configurable.get("search_engine", "ddg")
    dependencies = AgentDeps(search_engine=selected_engine)
    print(f"💰 Узел: Анализ зарплат...Search engine: {selected_engine}")

    log_entry = f"[{datetime.now()}] Salary Agent started searching for {state['vacancy_name']}"
    skill_result = safe_dump(state["skill_map"])

    result = await run_with_telemetry(
        salary_agent,
        f"Проанализируй рынок зарплат на основе этой карты навыков: {skill_result}",
        scenario_id=state["scenario_id"],
        scenario_label=state["scenario_label"],
        framework="langgraph",
        step="salary_agent.run",
        deps=dependencies,
    )
    return {
        "salary_report": result.output,
        "logs": state.get("logs", []) + [log_entry]
    }


async def study_node(state: HRState, config: RunnableConfig):
    configurable = config.get("configurable", {})
    selected_engine = configurable.get("search_engine", "ddg")
    dependencies = AgentDeps(search_engine=selected_engine)

    print(f"📚 Узел: Разработка плана обучения...Search engine: {selected_engine}")
    log_entry = f"[{datetime.now()}] Study Agent started searching for {state['vacancy_name']}"
    # Собираем контекст из предыдущих узлов
    context = {
        "skills": safe_dump(state["skill_map"]),
        "salaries": safe_dump(state["salary_report"])
    }
    
    result = await run_with_telemetry(
        study_agent,
        f"Составь план обучения на основе этих данных: {json.dumps(context, ensure_ascii=False )}",
        scenario_id=state["scenario_id"],
        scenario_label=state["scenario_label"],
        framework="langgraph",
        step="study_agent.run",
        deps=dependencies,
    )
    return {
      "study_plan": result.output,
      "logs": state.get("logs", []) + [log_entry]
    }


async def quality_node(state: HRState):
    print("⚖️ Узел: Валидация отчета...")
    log_entry = f"[{datetime.now()}] Study Agent started searching for {state['vacancy_name']}"
    full_report = {
        "skills": safe_dump(state["skill_map"]),
        "salaries": safe_dump(state["salary_report"]),
        "plan": safe_dump(state["study_plan"]),
    }
    
    result = await run_with_telemetry(
        quality_agent,
        f"Проведи аудит этого полного отчета: {json.dumps(full_report, ensure_ascii=False)}",
        scenario_id=state["scenario_id"],
        scenario_label=state["scenario_label"],
        framework="langgraph",
        step="quality_agent.run",
    )
    return {
      "quality_report": result.output,
      "logs": state.get("logs", []) + [log_entry]
    }