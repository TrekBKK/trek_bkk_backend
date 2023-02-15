from typing import List
from fastapi import Depends
from pymongo import MongoClient

from adapters import get_mongo_client
from domain.models import User


def get_users(db: MongoClient = Depends(get_mongo_client)) -> List[User]:
    # Use the MongoDB connection to retrieve users from the database
    users = db.User.find()
    # Convert the database results to User models
    return ""
