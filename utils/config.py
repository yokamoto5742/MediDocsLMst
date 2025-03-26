import os
import configparser
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from pymongo import MongoClient


def get_config():
    config = configparser.ConfigParser()
    base_dir = Path(__file__).parent.parent
    config_path = os.path.join(base_dir, 'config.ini')

    config.read(config_path, encoding='utf-8')

    return config

load_dotenv()

# MongoDB接続情報
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME")
MONGODB_USERS_COLLECTION = os.environ.get("MONGODB_USERS_COLLECTION")

GEMINI_CREDENTIALS = os.environ.get("GEMINI_CREDENTIALS")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")

# アプリの認証設定
REQUIRE_LOGIN = os.environ.get("REQUIRE_LOGIN", "True").lower() in ("true", "1", "yes")


def get_mongodb_connection():
    """MongoDBへの接続を取得する関数"""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    return db


def get_gemini_client():
    """Gemini APIクライアントを取得する関数"""
    genai.configure(api_key=GEMINI_CREDENTIALS)
    return genai
