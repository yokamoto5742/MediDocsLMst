import os
import configparser
from pathlib import Path
from dotenv import load_dotenv


def get_config():
    """
    設定ファイルを読み込む関数

    Returns:
        configparser.ConfigParser: 設定オブジェクト
    """
    config = configparser.ConfigParser()

    # 現在のファイルからの相対パスでconfig.iniを探す
    base_dir = Path(__file__).parent.parent
    config_path = os.path.join(base_dir, 'config.ini')

    # 設定ファイルを読み込む
    config.read(config_path, encoding='utf-8')

    return config


# ローカル開発環境では.envファイルから環境変数を読み込む
# Heroku環境では、システムの環境変数が使用される
load_dotenv()

# MongoDB接続情報
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME")
MONGODB_USERS_COLLECTION = os.environ.get("MONGODB_USERS_COLLECTION")

# Gemini API認証情報
GEMINI_CREDENTIALS = os.environ.get("GEMINI_CREDENTIALS")


# 接続情報の使用例
def get_mongodb_connection():
    """MongoDBへの接続を取得する関数"""
    from pymongo import MongoClient

    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    return db


def get_gemini_client():
    """Gemini APIクライアントを取得する関数"""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_CREDENTIALS)
    return genai
