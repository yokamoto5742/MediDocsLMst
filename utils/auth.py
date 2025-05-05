import os

from pymongo import MongoClient

from utils.config import MONGODB_URI
from utils.db import DatabaseManager
from utils.env_loader import load_environment_variables
from utils.exceptions import DatabaseError

load_environment_variables()


def get_users_collection():
    try:
        db_manager = DatabaseManager.get_instance()
        collection_name = os.environ.get("MONGODB_USERS_COLLECTION", "users")
        return db_manager.get_collection(collection_name)

    except Exception as e:
        raise DatabaseError(f"ユーザーコレクションの取得に失敗しました: {str(e)}")
