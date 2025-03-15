from langchain.tools import tool
from utils import get_mongo_db,default_collection, load_image_as_base64
import subprocess, datetime, json, msvcrt, os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from typing import Literal, List, Union, Dict, Any
import requests
from requests.structures import CaseInsensitiveDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from pprint import pprint
from langchain_community.callbacks.manager import get_openai_callback

class product(BaseModel):
    """product format: name-quantity-unit-price unit-total price"""
    product_format: str


class FindQueryFormat(BaseModel):
    """Format of the response in JSON output for MongoDB queries"""
    filter_query: Dict[str, Any]
    projection: Dict[str, int]


class InputData(BaseModel):
    """Information that is extracted from document
    type - type of processed document"""
    description: str = Field(
        default_factory=str,
        description="document type in 1-3 words")

    date: str = Field(default_factory="",
                         description="date from receipt .Format example: 2025-02-05")
    type: Literal["image", "audio", "text"]
    fruits: List[product] = Field(default_factory="",
                         description="list with all fruits")
    vegetables: List[product] = Field(default_factory="",
                        description="list with all vegetables")
    shop_place: str = Field(default_factory="",
                        description="Brand name of place where shopping was made")
    # im not sure of this
    total_cost: float = Field(
        default_factory=0,
        description="total cost, in RON currency value but not mention it")

    images_similarity: str = Field(default_factory="",
                      description="mention if is the same receipt in both images or not")

class Response(BaseModel):
    """Response to the user."""
    response: str


class Act(BaseModel):
    """Choose how to act"""

    action: Union[InputData, Response] = Field(description="Action to take. If you cant analyze image properly, say that as Response."
                                                      "If you are certain of the image analysis return InputData.")


@tool
def create_file(filename: str, code: str):
    """Create files with provided name and code.
    Function name is same as the filename
    Use in import section: from utils import get_mongo_db,
    and db = get_mongo_db, is connection to db
    at the bottom of the file include:
    if __name__ == "__main__":
        with the function execution to be tested later"""
    try:
        with open(f"./generated_functions/{filename}", 'x') as file:
            file.write(str(code))
            return "file succesfully created"
    except FileExistsError:
        return "file exists"


@tool
def test_file(filename: str):
    """Test a python file"""
    path = f"./generated_functions/{filename}"
    result = subprocess.run(["D:\ML_to_be\projects\LLMs_1\LLM_OpenAI/venv\Scripts\python.exe", path], capture_output=True, text=True, timeout=10)

    if result.returncode == 0:
        return result.stdout, "file has been successfully tested."
    else:
        return result.stderr, "some error occurred into testing"


@tool
def find_location():
    """Use this to find user location"""
    location_url = "https://api.geoapify.com/v1/ipinfo?&apiKey=00b4b3135450474b917041ce78270317"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(location_url, headers=headers)
    result = resp.json()
    return result["city"]["names"]["en"]


#not used
@tool
def find_places(places: list[str]):
    """Find places.
    places - a list of  local supermarket names"""
    return places

@tool
def show_values(value: bool, field: Literal["show_color"]):
    """Use this to hide/display fields"""





# this is function where AI will add info about what it created;
# program/db collection/...
@tool
def register_sys_block_to_db(
        name: str,
        description: str,
        type: Literal["function", "collection"],
        tested: Literal["yes", "no"],
        added_by: str="AI",
        ):
    """This tool register a function or a collection into database for keeping track of it, only if it was tested before.
    name: name of the query function or the collection
    description: the same description/docstring of that file created"""
    db = get_mongo_db()
    data = {
        'name': name,
        'description': description,
        'type': type,
        'added_by': added_by,
        'status': 'for_approval'
    }

    result = db[default_collection].insert_one(data)

    if result.acknowledged == 1:
        return "successfully added to database collection"
    else:
        return "something went wrong"


def delete_file():
    """Delete a previous created file"""

# this is used by programmer  ?
def connect_to_db():
    """"""

# this function adds to raw_data collection
@tool
def add_raw_to_db(filename: str, description: str, type: Literal["image", "audio", "text"], user: str):
    """This function is used everytime user inputs data/document/audio/image/text, to store its metadata.
    Args:
        filename: is the name of the file if provided.Otherwise put here the text provided
        description: Example - 'image of a receipt', or 'text with some shopping details'"""
    db = get_mongo_db()
    data = {
        "user": user,
        "filename": filename,
        "description": description,
        "type": type
    }
    result = db["raw_data"].insert_one(data)
    if result.acknowledged == 1:
        return "successfully added metadata", f"document_id:{result.inserted_id}"
    else:
        return "something went wrong"



@tool
def cache_file_read(mode:Literal["update","add"]):
    """This first reads a cache file for add/update, with analytic items.
    If update mode - only "update" and "display" fields can be changed."""
    data_extracted = {}
    with open("./generated_functions/display.json", 'r') as file:
        data = json.load(file)

    if mode == "update":
        for key, field in data.items():  # Iterate over key-value pairs
            data_extracted[key] = {"update": field["update"],
                                   "display": field["display"]}
    else:
        data_extracted = data

    return f"data_extracted: {data_extracted}"

@tool
def cache_file_write(data_extracted: dict, mode: Literal["update", "add"]):
    """This is 2nd part to write, for add/update to the cache file, after read it and get results from tools,
    and data_extracted with the new values corresponding to its items,
    this function completes the update"""
    print("new data:",data_extracted)
    with open("./generated_functions/display.json", 'r') as file:
        data = json.load(file)

    if mode == "update":
        for key, field in data.items():  # Iterate over key-value pairs
            for key2, field2 in data_extracted.items():
                if key == key2:
                    field["update"] = field2["update"]
                    field["display"] = field2["display"]
    else:
        data.update(data_extracted)

    with open("./generated_functions/display.json", 'w') as file:
        size = os.path.getsize("./generated_functions/display.json")  # get the file size
        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, size)
        json.dump(data, file, indent=4)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, size)

    return "Successfully"


@tool
def current_date():
    """Used to get a reference of the current date or when is needed to calculate dates"""
    return datetime.date.today()


# this tool is used by programmer to reason its working based on the whole internal data
@tool
def agentic_retriever_blocks():
    """not used yet"""
    pass

@tool
def querying_db_blocks(type: Literal["collection", "function"]):
    """To be able to build queries, retrieve data or to make analytics you need first to use this,
    as it gives you the collection/function that can be read.
    """
    return_list = []
    db = get_mongo_db()
    result = db["sys_blocks"].find(
        {"type": type},
        {"_id": 0, "type": 0, "added_by": 0, "status": 0})

    for document in result:
        data = {
            "name": document["name"],
            "description": document["description"]
        }
        return_list.append(data)

    return f"{type} list: ", return_list


@tool
def agentic_retriever_data(collection_name: str, collection_schema:str, description: str, query:str):
    """This function can search through any internal data,
    for a single collection per call.
    If multiple collections needs to be accessed in order to meet the request,
    you call agentic_retriever_data for each, and then you further process
    the queries results, from each call, together
    query: what exactly do you want to retrieve
        Ex. return all the spending made by user X, in last 2 weeks"""
    doc_list = []
    db = get_mongo_db()
    prompt = ChatPromptTemplate.from_template(
        f"""You are a MongoDb expert. Create a syntactically correct raw query,only for fetching with find() method, for the user question:
        {query}
        You have access to the following collection:
        {collection_name}\n
        With schema:
        {collection_schema}\n
        and description:
        {description}"""
        """Don't invent keys which are not into collection schema. Stick to what is was given to you.
        Anything that you return wrap the output in `json` tags\n{format_instructions}"""
    )
    parser = PydanticOutputParser(pydantic_object=FindQueryFormat)
    prompt_parser = prompt.partial(format_instructions=parser.get_format_instructions())

    #query_agent = prompt_parser | ChatOpenAI(model="gpt-4o") | parser
    query_agent = prompt_parser | ChatAnthropic(model="claude-3-7-sonnet-20250219") | parser

    result = query_agent.invoke(
        {"user_question": query}
    )
    print("Results: ", result)
    query_db = db[collection_name].find(result.filter_query, result.projection)

    for document in query_db:
        doc_list.append(document)

    return "Documents retrieved: ", doc_list

@tool
def add_receipts(
        user: str, date: str, type: Literal["receipt", "non-receipts"],
        fruits: list[str], vegetables: list[str],
        shop_place: str, document_id: str, total_cost: str):
    """This adds receipts data into database
    Add only values that you received.
    If you made up document_id or total_cost, dont use this function
    Args:
        type: receipt is an image with actual receipt"""

    db = get_mongo_db()
    data = {
        "user": user,
        "date": date,
        "fruits": fruits,
        "vegetables": vegetables,
        "shop_place": shop_place,
        "document_id": document_id,
        "total_cost": total_cost
    }
    if type == "receipt":
        collection_name = "receipts"
    else:
        collection_name = "non_receipts"

    result = db[collection_name].insert_one(data)
    if result.acknowledged == 1:
        return "successfully added to database collection"
    else:
        return "something went wrong"


@tool
def agentic_extractor(foldername: str, filenames: list[str]):
    """Use this when you want to extract data from user document"""

    # user input extraction agent
    extractor_prompt = """
           Given the images, provide informations by the requested format.
           Some tips to understand receipts: 
           1.Language is: romanian
           2.Multiple images can be provided as cropped parts for the same receipt,on which products details are as follows:
                Usually there are 2 rows, first with quantity, unit(kg,BUC etc.), price per unit.
                BUC - means pieces in romanian.
                Below, on the second row is product name and in right side the total price of that product.
                It can be additional rows per product, like a discount, so check it.
                Just to recap, for every product look above to extract info needed for product_format
                
            Don't add something if you're not sure.
           """
    content = [
        {"type": "text", "text": extractor_prompt}
    ]
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    extractor_agent = llm.with_structured_output(Act)

    for i in range(len(filenames)):
        img_base64 = load_image_as_base64(f"./user_input/raw/{foldername}/{filenames[i-1]}")
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})


    message = HumanMessage(content=content)
    structured_response = extractor_agent.invoke([message])
    if isinstance(structured_response, Act):
        return structured_response
    else:
        return "Data extraction failed"


if __name__ == "__main__":
    current_date = datetime.datetime.now()
    filename = "./user_input/raw/img_4/answer_%s%s%s_%s%s.txt" % (
        current_date.year, current_date.strftime("%m"), current_date.strftime("%d"), current_date.hour,
        current_date.minute)
    with get_openai_callback() as cb:
        with open(filename, "w", encoding="utf-8") as file:
            #result = register_sys_block_to_db("test2.py")
            result = agentic_extractor({"foldername": "img_4", "filenames": ["img_4_1.jpg", "img_4_2.jpg","img_4_3.jpg","img_4_4.jpg"]})
            pprint(vars(result))
            file.write(str(result))
            file.write("\n model: gpt-4o")
            file.write("\n----\n")
            #print("\n",result["raw"].response_metadata['model_name'])
            token_info = (
                f"Total Tokens: {cb.total_tokens}\n"
                f"Prompt Tokens: {cb.prompt_tokens}\n"
                f"Completion Tokens: {cb.completion_tokens}\n"
                f"Audio Tokens: {getattr(cb, 'audio_tokens', 0)}\n"  # Check for audio tokens
                f"Image Tokens: {getattr(cb, 'image_tokens', 0)}\n"
                f"Total Cost (USD): ${cb.total_cost}\n"
            )

            #get_receipts_info(collection_name="receipts", start_date="2023-01-01", end_date="2025-02-02", user="Giorgio")

            #result = test_file.invoke({"filename": "sum_two_numbers.py"})

            #file.write("model:",result["raw"].response_metadata['model_name'], "\n")
            print(token_info)
            file.write(token_info)

