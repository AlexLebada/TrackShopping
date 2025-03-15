from langgraph.graph import StateGraph, START
from orchestration import PlanExecute, supervisor_node, programmer_node, researcher_node, \
    human_node, planner_node, replanner_node, accountant_node, developer_node



workflow = StateGraph(PlanExecute)

workflow.add_node("supervisor", supervisor_node)
#workflow.add_node("planner", planner_node)
#workflow.add_node("replanner", replanner_node)
#workflow.addnode("HIL", human_node)
workflow.add_node("programmer", programmer_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("accountant", accountant_node)
workflow.add_node("developer", developer_node)
workflow.add_edge(START, "supervisor")

app = workflow.compile()


