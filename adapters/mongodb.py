import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_USER_NAME = os.getenv('MONGO_USER_NAME')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')

def get_mongo_client():
    mongo_client = MongoClient(
        f"mongodb+srv://{MONGO_USER_NAME}:{MONGO_PASSWORD}@trekcluster.gpygzfw.mongodb.net/?retryWrites=true&w=majority"
    )
    return mongo_client
