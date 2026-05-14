
from langgraph.graph import END, START, StateGraph

from nodes import quality_node, salary_node, skill_node, study_node
from schema import GraphConfiguration, HRState


workflow = StateGraph(state_schema=HRState, context_schema=GraphConfiguration)

# Добавляем узлы в граф
workflow.add_node("skill_node", skill_node)
workflow.add_node("salary_node", salary_node)
workflow.add_node("study_node", study_node)
workflow.add_node("quality_node", quality_node)


workflow.add_edge(START, "skill_node")
workflow.add_edge("skill_node", "salary_node")
workflow.add_edge("salary_node", "study_node")
workflow.add_edge("study_node", "quality_node")
workflow.add_edge("quality_node", END)

# Компилируем
app = workflow.compile()