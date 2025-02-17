from langchain.tools import tool
from utils import get_mongo_db,default_collection, load_image_as_base64
import subprocess
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing import Literal, List


class product(BaseModel):
    """product format: name-quantity-unit-price unit-total price"""
    product_format: str

class InputData(BaseModel):
    """Information that is extracted from document"""
    description: str = Field(
        default_factory=str,
        description="document type in 1-3 words")

    date: str = Field(default_factory=str,
                         description="when was created")
    type: Literal["image", "audio", "text"]
    fruits: List[product] = Field(default_factory=str,
                         description="list with all fruits")
    vegetables: List[product] = Field(default_factory=str,
                        description="list with all vegetables")
    shop_place: str = Field(default_factory=str,
                        description="from where shopping was made")
    # im not sure of this
    total_cost: str = Field(
        default_factory=str,
        description="total cost in RON currency")


@tool
def create_file(filename: str, code: str):
    """Create files with provided name and code"""
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
        return result.stdout, "file has been succesfully tested."
    else:
        return result.stderr, "some error ocurred into testing"



# this is function where AI will add info about what it created;
# program/db collection/...
@tool
def register_sys_block_to_db(
        name: str,
        description: str,
        type: Literal["program", "collection"],
        tested: Literal["yes", "no"],
        added_by: str="AI",
        ):
    """This function register a file or a collection into database for keeping track of it, only if it was tested before.
    name: name of the filename or the collection
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
def add_raw_to_db(filename: str, description: str, type: Literal["image", "audio", "text"], user: str="Giorgio"):
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
def get_receipts_info(user: str ):
    """not used yet"""
    pass


# this tool is used by programmer to reason its working based on the whole internal data
@tool
def agentic_retrieval():
    """not used yet"""
    pass


@tool
def add_receipts(
        user: str, date: str, type: Literal["receipt", "non-receipts"],
        fruits: list[str], vegetables: list[str],
        shop_place: str, document_id: str, total_cost: str):
    """This adds receipts data into db
    Add only values that you received.
    If you have a made up document_id or total_cost, dont use this function
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
        collection_name = "non-receipts"

    result = db[collection_name].insert_one(data)
    if result.acknowledged == 1:
        return "successfully added to database collection"
    else:
        return "something went wrong"


@tool
def agentic_extractor(filename: str):
    """Use this when you want to extract data from user document"""
    # user input extraction agent
    extractor_prompt = """
           Given the image, provide informations by the requested format.
           Some tips to understand receipts: 
           1.Language is: romanian
           2.On a receipt, a product details are as follows:
                Usually there are 2 rows, first with quantity, unit(kg,BUC etc.), price per unit.
                BUC - means pieces in romanian.
                Below, on the second row is product name and in right side the total price of that product.
                It can be additional rows per product, like a discount, so check it.
                
            Don't add something if you're not sure.
           """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    extractor_agent = llm.with_structured_output(InputData)
    image_base64 = load_image_as_base64(f"./user_input/raw/{filename}")
    message = HumanMessage(
        content=[
            {"type": "text", "text": extractor_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        ])
    structured_response = extractor_agent.invoke([message])
    if isinstance(structured_response, InputData):
        return structured_response
    else:
        return "Data extraction failed"


if __name__ == "__main__":
    #result = register_sys_block_to_db("test2.py")
    print(agentic_extractor("test_img.jpg"))
