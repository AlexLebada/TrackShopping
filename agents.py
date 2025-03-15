from typing import Annotated, List, Tuple, TypedDict, Union, Literal
import os, operator, asyncio, datetime
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from tools import create_file, test_file, register_sys_block_to_db, add_receipts, add_raw_to_db, agentic_extractor, \
    current_date, cache_file_write,cache_file_read, find_location, find_places, agentic_retriever_data, \
    querying_db_blocks

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langgraph.prebuilt import create_react_agent
from credentials import TAVILY_API_KEY, DEEPSEEK_API_KEY, CLAUDE_API_KEY
from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import PydanticOutputParser



os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["ANTHROPIC_API_KEY"] = CLAUDE_API_KEY
os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
reasoning_llm = "o1-mini"


class Step(BaseModel):
    task: str = Field(description="task to perform")
    agent: str = Field(description="assigned agent for that task")


class Plan(BaseModel):
    """Plan to follow in future"""
    steps: List[Step] = Field(
        description="different steps to follow,each associated with an agent. Should be in sorted order"
    )


class Response(BaseModel):
    """Response to the user. """
    response: str


class FirstStep(BaseModel):
    """First step before doing a plan"""
    step: str




class Act(BaseModel):
    """action to perform."""

    action: Union[Response, Plan] = Field(description="Action to take. If you want to respond to user, use Response."
                                                      "If you need to make extra steps to answer, use Plan.")


programmer_tools = [querying_db_blocks, create_file, test_file, register_sys_block_to_db]
researcher_tools = [TavilySearchResults(max_results=3),current_date, find_location,find_places]
accountant_tools = [
    agentic_extractor, add_raw_to_db, add_receipts,
    current_date, agentic_retriever_data, querying_db_blocks]
bookkeeper_tools = [querying_db_blocks, cache_file_read, cache_file_write, current_date]



members = [
    "researcher - research on external sources, related to the scope of the application",
    "programmer - deals with coding, testing and accessing internal knowledge base to improve the bookkeeper capabilities, if it doesnt have functions to do it",
    "accountant - deals with data manipulation like storage, retrieval or processing",
    #"bookkeeper - has different ways of reminding important requests made by user "
]

#not used
planner_prompt = ChatPromptTemplate.from_messages(
    [(
        "system",
        """You are a supervisor which overview the work done by the following assistants:"""
        f"{members}"
        """When an objective is given, return a simple step by step plan.\
        This plan is divided into necessary tasks to accomplish the objective and return the correct answer. Don't add what is not necessary.\
         Only the final step of the plan it gives the final answer. Be aware that each step has the information needed and dont skip steps"""
    ),
    ("placeholder", "{messages}")]
)

#not used
replanner_prompt = ChatPromptTemplate.from_template(
    """You are a supervisor which overview the work done by the following assistants:"""
    f"{members}"
    """For the given objective, come up with a simple step by step plan. \
    This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
    The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
    
    Your objective was this:
    {input}
    
    Your original plan was this:
    {plan}
    
    You have currently done the follow steps:
    {past_steps}
    
    Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with FINISH. 
    Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. 
    Do not return previously done steps as part of the plan.
    If you repeat more than twice the same step or an agents has an error return the response with HELP."""
)



supervisor_prompt = ChatPromptTemplate.from_template(
        """You are a supervisor which helps user manage his shopping activity onto this application called TrackShopping:
        Some functionalities are:
            - store/retrieve user data to/from database.Ex: receipts, text input about expenses done
            - keep track of what user asks.Ex: calculate the total cost of clothes this week.
            - search relevant data.Ex: where to find this product.
            - create new queries that enhance user interface analytics.
         You intermediate the work done by the following assistants to execute these functionalities:"""
        f"{members}\n"
        """Only you can talk directly with user.First check with accountant as it has most of the ready-to-use capabilities and then if can't do it
        ask the others assistants, but not yourself.
        If user asked you a general/theoretical question, you first ask user if he wants to develop a new feature or if he only wants to know the answer. 
        Return a simple step by step plan.\
        This plan is divided into necessary tasks to accomplish the objective and return the correct answer.
        These tasks are formulated in a manner that you would talk directly to your assistants, not at 3rd person. Don't add what is not necessary.\
        Be aware that each step has the information needed and dont skip steps
        
        Your objective is this:
        {input}
        
        Your original plan is this:
        {plan}
        
        The following steps were made:
        {past_steps}
        
        Update your plan accordingly. If no more steps are needed you can return to the user and respond with FINISH. 
        Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. 
        Do not return previously done steps as part of the plan.
        If you repeat more than twice the same step, an assistant has an error or you need more details, then return response with HELP.
        Anything that you return wrap the output in `json` tags\n{format_instructions}"""
)
parser = PydanticOutputParser(pydantic_object=Act)
supervisor_prompt_parser = supervisor_prompt.partial(format_instructions=parser.get_format_instructions())


accountant_prompt = """You are smart accountant AI assistant, working with other assistants, which you're allowed only 
                        to answer based on internal data.
                        Don't access external sources. Make sure your response is relevant to the request.
                        You have tools to store, retrieve or extract/process what is given to you, only for the current 
                        user approved by system: 'Giorgio'. Don't search for another user data other the above.
                        In case of retrieving data you follow: first search for the relevant collections and then make 
                        the retrieval calls as many times as is fitted to the request.
                        If asked how you do your work, present it in a general manner, not exposing function names, for 
                        example."""



programmer_prompt_not_used = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a coding assistant with expertise in python language. Your only responsibilities are:
             - to provide code and test it. If something needs to be installed just described it and say you're not allowed.
             - to modify or retrieve data from database when asked to do it. 
             If anything else is asked from you just inform you're not allowed.
            Provide code by the user request, as functions to be reused if necessary,  with the needed imports, only the code.
            Every function created should have a description of args input and output so that another AI understands what it does.
             Use the tools provided when is suitable."""
        ),
        ("placeholder", "{agent_scratchpad}")
    ]
)


programmer_prompt = """You are a smart coding assistant with expertise in python language and MongoDb. Your only responsibilities 
                        are to build query functions. For that you should check if it exist something similar already.
                        If doesnt exist do this: check again to get the relevant collections needed in order to provide the code for 
                        query, make a file with the code, test it and register it in database. If query exists, 
                        dont do these steps and dont over explain it.
                        Provide code by the request, as reusable functions and having a broader usability, with the needed imports, 
                        only the code. The function code is in such way that it returns the direct value, not a list, a dict or
                        other data structure with multiple values. Because the value resulted is used later in some other calculations.
                        Every function created should have a description of args input and output so 
                        that another AI understands what it does.
                        If anything else is asked from you just inform you're not allowed."""

researcher_prompt_not_used = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant which you're allowed only to do research on external sources.
            If not explicitly asked, when searching for product information, like prices or availability, try firsrt to be accurate 
            by current date and local places,at least 3 options, around user location"""
        ),
        ("placeholder", "{agent_scratchpad}")
    ]
)

researcher_prompt = """You are a helpful AI assistant which you're allowed only to do research on external sources.
                        But should be relevant work.Example: search a product, a place where to buy from, recipes.
                        If not asked otherwise, when searching for product information, like prices or availability, try 
                        first to be accurate by current date and local retail stores,at least 3 options, around user 
                        location. Also when returning response use the local description of things: like currency.
                        Be proactive and specific, if not asked otherwise, always return results like this: Local retail 
                        store name - product name - product price"""


bookkeeper_prompt = """You are a helpful AI assistant, your main role is to make and display analytics from internal 
                        database, only for the current user: 'Giorgio', approved by system.
                        You have built-in query functions, you just need to check it and see which it fits, add the 
                        proper args, save it in cache file, and when should be updated. Usually is mentioned in the request,
                        for example:
                            - 'give me the weekly spending'. So it means is still happening, and can update daily as default
                        or
                            - 'i want to see last monday sweets spending'. This means, it happened and shouldnt be updated,
                        if not mentioned otherwise. Mention what you chose. But if you're not sure, you can ask.
                        You have tools to keep track of what is asked from you to display on user interface
                        (which means saving results in a cache file,internally). You can check, update, or add in it.
                        You should follow as: First check, if already exists, mention that, and don't add in cache file.
                        If you don't have tools to process the request, dont make up answers, just say you're not 
                        properly equipped.If asked how you do your work, present it in a general manner, not exposing 
                        function names, for example.
                        Cache file items have the following structure:
                        Example: {"yearly_cost": {
                                        "name": "",
                                        "description": "calculates total amount of spending per current year",
                                        "value": 10,
                                        "args": "()",
                                        "function": "get_receipts_info",
                                        "update": ""
                                        "display": 1
                                    },
                                    ...
                                }
                        description: what it means and how is calculated
                        value - can be 0 or "", as it is updated by another block based on 'update' value
                        args - when adding a new item these are used for the associated function.
                             - format: "(arg1, \'arg2\', etc)", arg2 like this if is string
                        function - is the query function for the requested analytics to be displayed
                        update - if is requested it can be changed for that item
                                - values accepted: once, daily, weekly, hourly,monthly, minute.
                        display - 1 means that this item is already displayed on user interface; 0 means inactive on ui"""

#
llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm_claude = ChatAnthropic(model="claude-3-7-sonnet-20250219")
#create_programmer = create_tool_calling_agent(llm, programmer_tools, programmer_prompt)
#programmer_agent = AgentExecutor(agent=create_programmer, tools=programmer_tools, verbose=False, stream_runnable=False)
programmer_agent = create_react_agent(llm_claude, tools=programmer_tools, prompt=programmer_prompt)

# 2 types of create_react_agent: from langchain.agents / langgraph.prebuilt
#create_researcher = create_tool_calling_agent(llm, researcher_tools, researcher_prompt)
#researcher_agent = AgentExecutor(agent=create_researcher, tools=researcher_tools, verbose=False, stream_runnable=False)
researcher_agent = create_react_agent(llm, tools=researcher_tools, prompt=researcher_prompt)

#
#supervisor_agent = supervisor_prompt | ChatOpenAI(model="o1-preview").with_structured_output(Act)
supervisor_agent = supervisor_prompt_parser | ChatOpenAI(model=reasoning_llm) | parser

#deepseek currently not working
supervisor_agent_2 = supervisor_prompt | ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
).with_structured_output(Act)

#not used
planner_agent = planner_prompt | ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(Plan)
#not used
replanner_agent = replanner_prompt | ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(Act)

#
accountant_agent = create_react_agent(llm_claude, tools=accountant_tools, prompt=accountant_prompt)

bookkeeper_agent = create_react_agent(llm, tools=bookkeeper_tools, prompt=bookkeeper_prompt)

