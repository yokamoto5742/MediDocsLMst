import configparser
import os
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

MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME")
MONGODB_USERS_COLLECTION = os.environ.get("MONGODB_USERS_COLLECTION")
MONGODB_PROMPTS_COLLECTION = os.environ.get("MONGODB_PROMPTS_COLLECTION", "prompts")
MONGODB_DEPARTMENTS_COLLECTION = os.environ.get("MONGODB_DEPARTMENTS_COLLECTION", "departments")

GEMINI_CREDENTIALS = os.environ.get("GEMINI_CREDENTIALS")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")

REQUIRE_LOGIN = os.environ.get("REQUIRE_LOGIN", "True").lower() in ("true", "1", "yes")

IP_WHITELIST = os.environ.get("IP_WHITELIST", "")
IP_CHECK_ENABLED = os.environ.get("IP_CHECK_ENABLED", "False").lower() in ("true", "1", "yes")


def get_mongodb_connection():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    return db


def get_gemini_client():
    genai.configure(api_key=GEMINI_CREDENTIALS)
    return genai
