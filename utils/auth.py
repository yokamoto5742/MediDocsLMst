import os
import streamlit as st
import bcrypt
from pymongo import MongoClient
from utils.config import get_config, MONGODB_URI
from utils.env_loader import load_environment_variables

load_environment_variables()


def get_mongo_client():
    """MongoDB Atlasに接続するクライアントを取得"""
    if not MONGODB_URI:
        raise ValueError("MongoDB接続情報が設定されていません。環境変数または設定ファイルを確認してください。")

    return MongoClient(MONGODB_URI)


def get_users_collection():
    """ユーザーコレクションを取得"""
    client = get_mongo_client()
    db_name = os.environ.get("MONGODB_DB_NAME", "discharge_summary_app")
    collection_name = os.environ.get("MONGODB_USERS_COLLECTION", "users")

    db = client[db_name]
    return db[collection_name]


def hash_password(password):
    """パスワードをハッシュ化"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def verify_password(password, hashed_password):
    """パスワードの検証"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


def register_user(username, password, is_admin=False):
    """ユーザー登録"""
    users_collection = get_users_collection()

    # ユーザー名の重複チェック
    if users_collection.find_one({"username": username}):
        return False, "このユーザー名は既に使用されています"

    # 新規ユーザー情報の作成
    user_data = {
        "username": username,
        "password": hash_password(password),
        "is_admin": is_admin
    }

    # データベースに保存
    users_collection.insert_one(user_data)
    return True, "ユーザー登録が完了しました"


def change_password(username, current_password, new_password):
    """パスワード変更"""
    users_collection = get_users_collection()

    # ユーザー名でユーザーを検索
    user = users_collection.find_one({"username": username})

    if not user:
        return False, "ユーザーが見つかりません"

    # 現在のパスワードを検証
    if not verify_password(current_password, user["password"]):
        return False, "現在のパスワードが正しくありません"

    # 新しいパスワードをハッシュ化して更新
    hashed_new_password = hash_password(new_password)
    users_collection.update_one(
        {"username": username},
        {"$set": {"password": hashed_new_password}}
    )

    return True, "パスワードが正常に変更されました"


def authenticate_user(username, password):
    """ユーザー認証"""
    users_collection = get_users_collection()

    # ユーザー名でユーザーを検索
    user = users_collection.find_one({"username": username})

    if not user:
        return False, "ユーザー名またはパスワードが正しくありません"

    # パスワードの検証
    if verify_password(password, user["password"]):
        # セッションに保存するユーザーデータ
        user_data = {
            "username": user["username"],
            "is_admin": user.get("is_admin", False)
        }
        return True, user_data

    return False, "ユーザー名またはパスワードが正しくありません"


def login_ui():
    """ログインUI"""
    st.title("退院時サマリ作成アプリ - ログイン")

    # セッション状態の初期化
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is not None:
        return True

    login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

    with login_tab:
        username = st.text_input("ユーザー名", key="login_username")
        password = st.text_input("パスワード", type="password", key="login_password")

        if st.button("ログイン", key="login_button"):
            if not username or not password:
                st.error("ユーザー名とパスワードを入力してください")
                return False

            try:
                success, result = authenticate_user(username, password)
                if success:
                    st.session_state.user = result
                    st.success(f"ようこそ、{username}さん！")
                    st.rerun()
                    return True
                else:
                    st.error(result)
                    return False
            except Exception as e:
                st.error(f"認証エラー: {str(e)}")
                return False

    with register_tab:
        new_username = st.text_input("ユーザー名", key="register_username")
        new_password = st.text_input("パスワード", type="password", key="register_password")
        confirm_password = st.text_input("パスワード（確認）", type="password", key="confirm_password")

        if st.button("登録", key="register_button"):
            if not new_username or not new_password:
                st.error("ユーザー名とパスワードを入力してください")
                return False

            if new_password != confirm_password:
                st.error("パスワードが一致しません")
                return False

            try:
                # 最初のユーザーを管理者として登録
                users_collection = get_users_collection()
                is_first_user = users_collection.count_documents({}) == 0

                success, message = register_user(new_username, new_password, is_admin=is_first_user)
                if success:
                    st.success(message)
                    if is_first_user:
                        st.info("あなたは最初のユーザーなので、管理者権限が付与されました")
                    return False
                else:
                    st.error(message)
                    return False
            except Exception as e:
                st.error(f"登録エラー: {str(e)}")
                return False

    return False


def logout():
    """ログアウト処理"""
    if "user" in st.session_state:
        st.session_state.user = None
        return True
    return False


def require_login():
    """ログインが必要なページの保護"""
    if "user" not in st.session_state or st.session_state.user is None:
        login_ui()
        return False
    return True


def get_current_user():
    """現在のログインユーザーを取得"""
    if "user" in st.session_state:
        return st.session_state.user
    return None


def is_admin():
    """現在のユーザーが管理者かどうかを確認"""
    user = get_current_user()
    if user:
        return user.get("is_admin", False)
    return False


def password_change_ui():
    """パスワード変更UI"""
    st.subheader("パスワード変更")

    user = get_current_user()
    if not user:
        st.error("ログインが必要です")
        return

    current_password = st.text_input("現在のパスワード", type="password", key="current_password")
    new_password = st.text_input("新しいパスワード", type="password", key="new_password")
    confirm_new_password = st.text_input("新しいパスワード（確認）", type="password", key="confirm_new_password")

    if st.button("パスワードを変更", key="change_password_button"):
        if not current_password or not new_password or not confirm_new_password:
            st.error("すべての項目を入力してください")
            return

        if new_password != confirm_new_password:
            st.error("新しいパスワードが一致しません")
            return

        try:
            success, message = change_password(user["username"], current_password, new_password)
            if success:
                st.success(message)
            else:
                st.error(message)
        except Exception as e:
            st.error(f"パスワード変更エラー: {str(e)}")
