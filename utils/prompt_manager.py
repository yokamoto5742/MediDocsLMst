import datetime
import os

from pymongo import MongoClient

from utils.config import get_config, MONGODB_URI, get_mongodb_connection
from utils.env_loader import load_environment_variables

DEFAULT_DEPARTMENTS = [
     "内科", "消化器内科", "整形外科", "眼科",
]

def get_prompt_collection():
    db = get_mongodb_connection()
    collection_name = os.environ.get("MONGODB_PROMPTS_COLLECTION", "prompts")

    return db[collection_name]


def get_department_collection():
    db = get_mongodb_connection()
    collection_name = os.environ.get("MONGODB_DEPARTMENTS_COLLECTION", "departments")

    return db[collection_name]


def get_current_datetime():
    return datetime.datetime.now()


def insert_document(collection, document):
    """ドキュメントにタイムスタンプを追加して挿入するヘルパー関数"""
    now = get_current_datetime()
    document.update({
        "created_at": now,
        "updated_at": now
    })
    return collection.insert_one(document)


def initialize_default_prompt():
    prompt_collection = get_prompt_collection()

    default_prompt = prompt_collection.find_one({"department": "default", "is_default": True})

    if not default_prompt:
        config = get_config()
        default_prompt_content = config['PROMPTS']['discharge_summary']

        insert_document(prompt_collection, {
            "department": "default",
            "name": "退院時サマリ",
            "content": default_prompt_content,
            "is_default": True
        })


def initialize_departments():
    department_collection = get_department_collection()

    existing_count = department_collection.count_documents({})

    if existing_count == 0:
        for dept in DEFAULT_DEPARTMENTS:
            insert_document(department_collection, {"name": dept})


def get_all_departments():
    department_collection = get_department_collection()
    return [dept["name"] for dept in department_collection.find().sort("name")]


def create_department(name):
    if not name:
        return False, "診療科名を入力してください"

    department_collection = get_department_collection()

    existing = department_collection.find_one({"name": name})
    if existing:
        return False, "この診療科は既に存在します"

    insert_document(department_collection, {"name": name})

    return True, "診療科を登録しました"


def delete_department(name):
    department_collection = get_department_collection()
    prompt_collection = get_prompt_collection()

    # 削除前にこの診療科に紐づくプロンプトを確認
    prompt_count = prompt_collection.count_documents({"department": name})
    if prompt_count > 0:
        return False, "この診療科に紐づくプロンプトが存在するため削除できません"

    # 診療科を削除
    result = department_collection.delete_one({"name": name})
    if result.deleted_count == 0:
        return False, "診療科が見つかりません"

    return True, "診療科を削除しました"


def get_prompt_by_department(department="default"):
    """指定された診療科のプロンプトを取得"""
    prompt_collection = get_prompt_collection()
    prompt = prompt_collection.find_one({"department": department})

    if not prompt:
        prompt = prompt_collection.find_one({"department": "default", "is_default": True})
    
    return prompt


def get_all_prompts():
    prompt_collection = get_prompt_collection()
    return list(prompt_collection.find().sort("department"))


def update_document(collection, query, update_data):
    now = get_current_datetime()
    update_data.update({"updated_at": now})

    return collection.update_one(
        query,
        {"$set": update_data}
    )


def create_or_update_prompt(department, name, content):
    if not department or not name or not content:
        return False, "すべての項目を入力してください"

    prompt_collection = get_prompt_collection()
    existing = prompt_collection.find_one({"department": department})

    if existing:
        # 更新
        update_document(
            prompt_collection,
            {"department": department},
            {
                "name": name,
                "content": content
            }
        )
        return True, "プロンプトを更新しました"
    else:
        # 新規作成
        insert_document(prompt_collection, {
            "department": department,
            "name": name,
            "content": content,
            "is_default": False
        })
        return True, "プロンプトを新規作成しました"


def delete_prompt(department):
    if department == "default":
        return False, "デフォルトプロンプトは削除できません"

    prompt_collection = get_prompt_collection()
    result = prompt_collection.delete_one({"department": department})

    if result.deleted_count == 0:
        return False, "プロンプトが見つかりません"

    return True, "プロンプトを削除しました"

def initialize_database():
    initialize_default_prompt()
    initialize_departments()
