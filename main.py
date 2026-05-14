import os
from datetime import datetime
from graph import app
import json
from langchain_core.runnables import RunnableConfig
import asyncio

from schema import HRState, create_initial_state
from utils.telemetry import export_metrics_json, reset_traces

test_cases = [
    "Backend Python Developer",
    "ML Engineer",
    "IOS Developer Swift",
]


async def generate_examples():
    os.makedirs("examples", exist_ok=True)
    
    for vacancy in test_cases:
        print(f"🚀 Запуск генерации для: {vacancy}")
        
        # Инициализируем состояние
        initial_state: HRState = create_initial_state(vacancy)
        
        # Запускаем граф
        # thread_id гарантирует, что запуски изолированы
        config: RunnableConfig = {"configurable": {
            "thread_id": vacancy,
            "search_engine": "tavily"  # "ddg"
        }}
        final_state = await app.ainvoke(initial_state, config=config)


        export_data = {
          "vacancy_name": final_state["vacancy_name"],
          "generated_at": final_state["generated_at"],
          "logs": final_state["logs"],
          # Превращаем Pydantic-объекты в обычные словари Python
          "skill_map": final_state["skill_map"].model_dump(),
          "salary_report": final_state["salary_report"].model_dump(),
          "study_plan": final_state["study_plan"].model_dump(),
          "quality_report": final_state["quality_report"].model_dump(),
        }
        
        # Сохраняем в файл
        filename = f"examples/{vacancy.lower().replace(' ', '_')}.json"
        with open(filename, "w", encoding="utf-8") as f:
          json.dump(export_data, f, indent=2, ensure_ascii=False)
            
    print("✅ Все отчеты сгенерированы в папку examples/")

async def main():
    reset_traces()
    await generate_examples()
    export_metrics_json()
    


if __name__ == "__main__":
    asyncio.run(main())

