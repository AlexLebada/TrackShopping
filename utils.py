from credentials import MONGO_DB_KEY, MONGO_DB_PASS, MONGO_DB_USER
from pymongo import MongoClient
import base64, datetime, json, os
import streamlit as st
from typing import Literal
from PIL import Image


MONGO_CLIENT = {
    'HOST': MONGO_DB_KEY,         # MongoDB host
    'PORT': 27017,               # MongoDB port
    'USERNAME': MONGO_DB_USER,              # MongoDB username (if required)
    'PASSWORD': MONGO_DB_PASS,              # MongoDB password (if required)
    'DB_NAME': 'TrackShopping',  # Your MongoDB database name
}

MONGO_DB_NAME = "TrackShopping"
default_collection = "sys_blocks"


def get_mongo_db():
    client = MongoClient(
            host=MONGO_DB_KEY,
            port=27017,
            username=MONGO_DB_USER,
            password=MONGO_DB_PASS
        )

    db = client[MONGO_DB_NAME]
    return db



def load_image_as_base64(image_path: str) -> str:
    """Encode the image as a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# not used yet
def add_users():
    db = get_mongo_db()
    current_date = datetime.datetime.now()
    data = {
        "username": "Giovanni Giorgio",
        "info": "alex.lebada@gmail.com",
        "usage": "i want to use this app for shopping",
        "date": current_date
    }
    output = db["users"].insert_one(data)
    return output



def files_rename_store(files: list):
    with open("./user_input/storage_cache.json", 'r') as file:
        number = json.load(file)
        number['folder_number'] = number['folder_number']+1

    renamed_list = []
    i = 0
    #folder_name = f"img_{next_value}"
    folder_path = f"./user_input/raw/img_{number['folder_number']}"
    if files is not None:
        os.makedirs(folder_path, exist_ok=True)
        for file in files:
            i += 1
            file.name = f"img_{number['folder_number']}_{i}.jpg"
            # as RGB format
            image = Image.open(file)
            st.image(image, caption="Uploaded Image", width=50)
            # user storage path
            file_path = os.path.join(folder_path, file.name)
            # save file
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            renamed_list.append(file.name)

    with open("./user_input/storage_cache.json", 'w') as file:
        json.dump(number, file, indent=4)

    return renamed_list


