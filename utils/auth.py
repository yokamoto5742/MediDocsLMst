import os
import json
import bcrypt
import streamlit as st
from pathlib import Path

def get_user_db_path():
    """ユーザーデータベースファイルのパスを取得"""
    base_dir = Path(__file__).parent.parent
    data_dir = os.path.join(base_dir, 'data')
    
    # データディレクトリが存在しない場合は作成
    os.makedirs(data_dir, exist_ok=True)
    
    return os.path.join(data_dir, 'users.json')

def load_users():
    """ユーザーデータの読み込み"""
    user_db_path = get_user_db_path()
    
    if os.path.exists(user_db_path):
        with open(user_db_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_users(users):
    """ユーザーデータの保存"""
    user_db_path = get_user_db_path()
    
    with open(user_db_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def hash_password(password):
    """パスワードをハッシュ化"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """パスワードの検証"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(username, password, is_admin=False):
    """ユーザー登録"""
    users = load_users()
    
    if username in users:
        return False, "このユーザー名は既に使用されています"
    
    users[username] = {
        "password": hash_password(password),
        "is_admin": is_admin
    }
    
    save_users(users)
    return True, "ユーザー登録が完了しました"

def authenticate_user(username, password):
    """ユーザー認証"""
    users = load_users()
    
    if username not in users:
        return False, "ユーザー名またはパスワードが正しくありません"
    
    user_data = users[username]
    if verify_password(password, user_data["password"]):
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
            
            success, result = authenticate_user(username, password)
            if success:
                st.session_state.user = {
                    "username": username,
                    "is_admin": result.get("is_admin", False)
                }
                st.success(f"ようこそ、{username}さん！")
                st.rerun()
                return True
            else:
                st.error(result)
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
            
            # 最初のユーザーを管理者として登録
            users = load_users()
            is_first_user = len(users) == 0
            
            success, message = register_user(new_username, new_password, is_admin=is_first_user)
            if success:
                st.success(message)
                if is_first_user:
                    st.info("あなたは最初のユーザーなので、管理者権限が付与されました")
                return False
            else:
                st.error(message)
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
