from credentials import MONGO_DB_KEY, MONGO_DB_PASS, MONGO_DB_USER
from pymongo import MongoClient
import base64, datetime


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


if __name__ == "__main__":
    pass
    #print(add_users().inserted_id)




