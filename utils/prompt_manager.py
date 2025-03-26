import os
import datetime
from pymongo import MongoClient
from utils.config import get_config, MONGODB_URI, get_mongodb_connection
from utils.env_loader import load_environment_variables

# 診療科リスト
DEFAULT_DEPARTMENTS = [
     "内科", "消化器内科", "整形外科", "眼科",
]

def get_prompt_collection():
    """プロンプトコレクションを取得"""
    db = get_mongodb_connection()
    collection_name = os.environ.get("MONGODB_PROMPTS_COLLECTION", "prompts")
    return db[collection_name]

def get_department_collection():
    """診療科コレクションを取得"""
    db = get_mongodb_connection()
    collection_name = os.environ.get("MONGODB_DEPARTMENTS_COLLECTION", "departments")
    return db[collection_name]

def initialize_default_prompt():
    """初期プロンプトをDBに登録"""
    prompt_collection = get_prompt_collection()
    
    # すでにデフォルトプロンプトが存在するか確認
    default_prompt = prompt_collection.find_one({"department": "default", "is_default": True})
    
    if not default_prompt:
        # config.iniからデフォルトプロンプトを取得
        config = get_config()
        default_prompt_content = config['PROMPTS']['discharge_summary']
        
        # DBに登録
        now = datetime.datetime.now()
        prompt_collection.insert_one({
            "department": "default",
            "name": "退院時サマリ",
            "content": default_prompt_content,
            "is_default": True,
            "created_at": now,
            "updated_at": now
        })
        print("デフォルトプロンプトをDBに登録しました")

def initialize_departments():
    """初期診療科マスタをDBに登録"""
    department_collection = get_department_collection()
    
    # すでに診療科が登録されているか確認
    existing_count = department_collection.count_documents({})
    
    if existing_count == 0:
        # デフォルト診療科リストを登録
        now = datetime.datetime.now()
        for dept in DEFAULT_DEPARTMENTS:
            department_collection.insert_one({
                "name": dept,
                "created_at": now,
                "updated_at": now
            })
        print(f"デフォルト診療科（{len(DEFAULT_DEPARTMENTS)}件）をDBに登録しました")

def get_all_departments():
    """すべての診療科を取得"""
    department_collection = get_department_collection()
    return [dept["name"] for dept in department_collection.find().sort("name")]

def create_department(name):
    """診療科を新規作成"""
    if not name:
        return False, "診療科名を入力してください"
    
    department_collection = get_department_collection()
    
    # 既に同名の診療科が存在するか確認
    existing = department_collection.find_one({"name": name})
    if existing:
        return False, "この診療科は既に存在します"
    
    # 新規登録
    now = datetime.datetime.now()
    department_collection.insert_one({
        "name": name,
        "created_at": now,
        "updated_at": now
    })
    
    return True, "診療科を登録しました"


def delete_department(name):
    """診療科を削除"""
    department_collection = get_department_collection()
    prompt_collection = get_prompt_collection()

    # 削除前にこの診療科に紐づくプロンプトを確認
    # エラー修正: count()メソッドをcount_documents()に変更
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
    
    # 指定の診療科のプロンプトを検索
    prompt = prompt_collection.find_one({"department": department})
    
    # 見つからない場合はデフォルトプロンプトを返す
    if not prompt:
        prompt = prompt_collection.find_one({"department": "default", "is_default": True})
    
    return prompt

def get_all_prompts():
    """すべてのプロンプトを取得"""
    prompt_collection = get_prompt_collection()
    return list(prompt_collection.find().sort("department"))

def create_or_update_prompt(department, name, content):
    """プロンプトを作成または更新"""
    if not department or not name or not content:
        return False, "すべての項目を入力してください"
    
    prompt_collection = get_prompt_collection()
    now = datetime.datetime.now()
    
    # すでに同じ診療科のプロンプトが存在するか確認
    existing = prompt_collection.find_one({"department": department})
    
    if existing:
        # 更新
        prompt_collection.update_one(
            {"department": department},
            {"$set": {
                "name": name,
                "content": content,
                "updated_at": now
            }}
        )
        return True, "プロンプトを更新しました"
    else:
        # 新規作成
        prompt_collection.insert_one({
            "department": department,
            "name": name,
            "content": content,
            "is_default": False,
            "created_at": now,
            "updated_at": now
        })
        return True, "プロンプトを作成しました"

def delete_prompt(department):
    """プロンプトを削除"""
    if department == "default":
        return False, "デフォルトプロンプトは削除できません"

    prompt_collection = get_prompt_collection()
    result = prompt_collection.delete_one({"department": department})

    if result.deleted_count == 0:
        return False, "プロンプトが見つかりません"

    return True, "プロンプトを削除しました"

def initialize_database():
    """データベースの初期化（アプリ起動時に実行）"""
    initialize_default_prompt()
    initialize_departments()
