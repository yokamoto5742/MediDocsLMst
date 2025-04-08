import datetime
import os

from pymongo import MongoClient

from utils.config import get_config, MONGODB_URI
from utils.constants import DEFAULT_DEPARTMENTS, MESSAGES
from utils.db import DatabaseManager
from utils.env_loader import load_environment_variables
from utils.exceptions import DatabaseError, AppError


def get_prompt_collection():
    try:
        db_manager = DatabaseManager.get_instance()
        collection_name = os.environ.get("MONGODB_PROMPTS_COLLECTION", "prompts")
        return db_manager.get_collection(collection_name)
    except Exception as e:
        raise DatabaseError(f"プロンプトコレクションの取得に失敗しました: {str(e)}")


def get_department_collection():
    try:
        db_manager = DatabaseManager.get_instance()
        collection_name = os.environ.get("MONGODB_DEPARTMENTS_COLLECTION", "departments")
        return db_manager.get_collection(collection_name)
    except Exception as e:
        raise DatabaseError(f"診療科コレクションの取得に失敗しました: {str(e)}")


def get_current_datetime():
    return datetime.datetime.now()


def insert_document(collection, document):
    try:
        now = get_current_datetime()
        document.update({
            "created_at": now,
            "updated_at": now
        })
        return collection.insert_one(document)
    except Exception as e:
        raise DatabaseError(f"ドキュメントの挿入に失敗しました: {str(e)}")


def update_document(collection, query, update_data):
    try:
        now = get_current_datetime()
        update_data.update({"updated_at": now})
        return collection.update_one(
            query,
            {"$set": update_data}
        )
    except Exception as e:
        raise DatabaseError(f"ドキュメントの更新に失敗しました: {str(e)}")


def initialize_departments():
    try:
        department_collection = get_department_collection()
        existing_count = department_collection.count_documents({})
        if existing_count == 0:
            for dept in DEFAULT_DEPARTMENTS:
                insert_document(department_collection, {"name": dept})
    except Exception as e:
        raise DatabaseError(f"診療科の初期化に失敗しました: {str(e)}")


def get_all_departments():
    try:
        department_collection = get_department_collection()
        return [dept["name"] for dept in department_collection.find().sort("name")]
    except Exception as e:
        raise DatabaseError(f"診療科の取得に失敗しました: {str(e)}")


def create_department(name):
    try:
        if not name:
            return False

        department_collection = get_department_collection()
        prompt_collection = get_prompt_collection()  # 追加

        existing = department_collection.find_one({"name": name})
        if existing:
            return False, MESSAGES["DEPARTMENT_EXISTS"]

        insert_document(department_collection, {"name": name})

        default_prompt = prompt_collection.find_one({"department": "default", "is_default": True})
        if not default_prompt:
            config = get_config()
            default_prompt_content = config['PROMPTS']['discharge_summary']
        else:
            default_prompt_content = default_prompt.get("content", "")

        insert_document(prompt_collection, {
            "department": name,
            "name": "退院時サマリ",
            "content": default_prompt_content,
            "is_default": False
        })

        return True, MESSAGES["DEPARTMENT_CREATED"]
    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"診療科の作成中にエラーが発生しました: {str(e)}")


def delete_department(name):
    try:
        department_collection = get_department_collection()
        prompt_collection = get_prompt_collection()
        result = department_collection.delete_one({"name": name})

        if result.deleted_count == 0:
            return False, "診療科が見つかりません"

        prompt_collection.delete_many({"department": name})

        return True, "診療科を削除しました"
    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"診療科の削除中にエラーが発生しました: {str(e)}")


def initialize_default_prompt():
    try:
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
    except Exception as e:
        raise DatabaseError(f"デフォルトプロンプトの初期化に失敗しました: {str(e)}")


def get_prompt_by_department(department="default"):
    """指定された診療科のプロンプトを取得"""
    try:
        prompt_collection = get_prompt_collection()
        prompt = prompt_collection.find_one({"department": department})

        if not prompt:
            prompt = prompt_collection.find_one({"department": "default", "is_default": True})

        return prompt
    except Exception as e:
        raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")


def get_all_prompts():
    try:
        prompt_collection = get_prompt_collection()
        return list(prompt_collection.find().sort("department"))
    except Exception as e:
        raise DatabaseError(f"プロンプト一覧の取得に失敗しました: {str(e)}")


def create_or_update_prompt(department, name, content):
    try:
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
    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"プロンプトの作成/更新中にエラーが発生しました: {str(e)}")


def delete_prompt(department):
    try:
        if department == "default":
            return False, "デフォルトプロンプトは削除できません"

        prompt_collection = get_prompt_collection()
        department_collection = get_department_collection()

        result = prompt_collection.delete_one({"department": department})

        if result.deleted_count == 0:
            return False, "プロンプトが見つかりません"

        department_collection.delete_one({"name": department})

        return True, "プロンプトと関連する診療科を削除しました"
    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"プロンプトの削除中にエラーが発生しました: {str(e)}")


def initialize_database():
    try:
        initialize_default_prompt()
        initialize_departments()
    except Exception as e:
        raise DatabaseError(f"データベースの初期化に失敗しました: {str(e)}")
