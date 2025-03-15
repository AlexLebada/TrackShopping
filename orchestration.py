from langgraph.graph import MessagesState, END
from typing import Annotated, List, Tuple, TypedDict, Union
import operator, functools, langchain, datetime
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field
from results.queries.queries import queries
from utils import get_mongo_db
from agents import programmer_agent, supervisor_agent, supervisor_prompt, Response, researcher_agent,\
    planner_agent, replanner_agent, accountant_agent, bookkeeper_agent
from langchain_community.callbacks.manager import get_openai_callback
from langgraph.managed.is_last_step import RemainingSteps


# Nodes state
class PlanExecute(MessagesState):
    input: str # instead will be messages
    plan: List[Tuple[str, str]]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str
    remaining_steps: RemainingSteps
    query_response: str





def supervisor_node(state: PlanExecute):
    print("State: ",state)
    if state["remaining_steps"] <= 2:
        return Command(
            update={
                "response": "RECURSION_LIMIT"
            },
            goto="developer"
        )
    response = supervisor_agent.invoke(state)
    #print("past steps:", state["past_steps"])
    if isinstance(response.action, Response):
        if response.action.response == "HELP":
            return Command(
                update={
                    "response": response.action.response
                },
                goto="developer"
            )
        else:
            return Command(
                update={
                    "response": response.action.response
                },
                goto=END
            )
    else:
        return Command(
            update={
                "plan": response.action.steps
            },
            goto=response.action.steps[0].agent

        )


def developer_node(state: PlanExecute):
    db = get_mongo_db()
    data = {
        "query": state["input"],
        "results": state["query_response"],
        "error_type": state["response"],
        "status": "waiting"
    }
    db_returned = db["user_request_issues"].insert_one(data)

    return Command(
        update={
            "response": "There is a problem.An issue is raised for developer"
        },
        goto=END
    )


#not_used
def planner_node(state: PlanExecute):
    plan = planner_agent.invoke(
        {"messages": [("user", state["input"])]}
    )
    print("print:", plan.steps)
    print("print:", plan.steps[0].agent)
    return Command(
        update={
            "plan": plan.steps
        },
        goto=plan.steps[0].agent

    )


#not used
def replanner_node(state: PlanExecute):
    output =  replanner_agent.invoke(state)
    if isinstance(output.action, Response):
        return Command(
            update={
                "response": output.action.response
            },
            goto=END
        )
    else:
        return Command(
            update={
                "plan": output.action.steps
            },
            goto=output.action.steps[0].agent

        )

#not used
def human_node(state: PlanExecute):
    user_response = interrupt("Continue or not:(y/n)")
    if user_response != "y":
        return Command(
            goto=END
        )



def programmer_node(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}.{step}" for i, step in enumerate(plan))
    task = plan[0].task
    task_formatted = f"""For the following plan:
    {plan_str}\n\nYou are tasked with the following step {1}, {task}."""
    agent_response = programmer_agent.invoke(
        {"messages": [("assistant", task_formatted)]}
    )
    return Command(
        update={
        "past_steps": [(task, agent_response["messages"][-1])]
    },
        goto="supervisor",
    )


def researcher_node(state: PlanExecute):
    print(state["plan"])
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}.{step}" for i, step in enumerate(plan))
    task = plan[0].task
    task_formatted = f"""For the following plan:
        {plan_str}\n\nYou are tasked with the following step {1}, {task}."""
    agent_response = researcher_agent.invoke(
        {"messages": [("assistant", task_formatted)]}
    )
    print("agent response:", agent_response["messages"][-1])
    return Command(
        update={
            "past_steps": [(task, agent_response["messages"][-1])]
        },
        goto="supervisor",
    )


def accountant_node(state: PlanExecute):
    print("State: ",state)
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}.{step}" for i, step in enumerate(plan))
    task = plan[0].task
    task_formatted = f"""For the following plan:
        {plan_str}\n\nYou are tasked with the following step {1}, {task}."""
    agent_response = accountant_agent.invoke(
        {"messages": [("assistant", task_formatted)]}
    )
    print("agent response:", agent_response["messages"][-1])
    return Command(
        update={
            "past_steps": [(task, agent_response["messages"][-1])]
        },
        goto="supervisor",
    )





if __name__ == "__main__":

    langchain.debug = True
    print("asd")
    current_date = datetime.datetime.now()
    filename = "./results/answer_%s%s%s_%s%s.txt" % (
    current_date.year, current_date.strftime("%m"), current_date.strftime("%d"), current_date.hour, current_date.minute)
    #with get_openai_callback() as cb:
    with open(filename, "w", encoding="utf-8") as file:
        for step in bookkeeper_agent.stream(
            {"messages": [("user", queries[12])]}
        ):
            print(step)
            file.write(str(step))
            file.write("\n----\n")

        token_info = (
            #f"Total Tokens: {cb.total_tokens}\n"
            #f"Prompt Tokens: {cb.prompt_tokens}\n"
            #f"Completion Tokens: {cb.completion_tokens}\n"
            #f"Total Cost (USD): ${cb.total_cost}\n"
        )
        #print(token_info)
        #file.write(token_info)
