from pymongo import MongoClient
from django.conf import settings

def get_db():
    client = MongoClient(f"mongodb+srv://{settings.MONGODB['USER']}:{settings.MONGODB['PASSWORD']}@{settings.MONGODB['HOST']}/")
    db = client[settings.MONGODB['NAME']]
    return db

def get_user_collection():
    db = get_db()
    collection = db["User"]
    return collection

def get_review_collection():
    db = get_db()
    collection = db["Review"]
    return collection

def get_precess_review_collection():
    db = get_db()
    collection = db["ProccessReview"]
    return collection