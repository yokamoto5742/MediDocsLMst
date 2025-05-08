import datetime

import streamlit as st

from database.db import get_settings_collection
from utils.config import GEMINI_MODEL, GEMINI_CREDENTIALS, GEMINI_FLASH_MODEL, CLAUDE_API_KEY, OPENAI_API_KEY, OPENAI_MODEL, SELECTED_AI_MODEL
from utils.prompt_manager import get_all_departments, get_department_by_name

def change_page(page):
    st.session_state.current_page = page


def render_sidebar():
    departments = ["default"] + get_all_departments()

    previous_dept = st.session_state.selected_department
    previous_model = getattr(st.session_state, "selected_model", None)

    try:
        index = departments.index(st.session_state.selected_department)
    except ValueError:
        index = 0
        st.session_state.selected_department = departments[0]  # "default" に設定

    selected_dept = st.sidebar.selectbox(
        "診療科",
        departments,
        index=index,
        format_func=lambda x: "全科共通" if x == "default" else x,
        key="department_selector"
    )

    st.session_state.available_models = []
    if GEMINI_MODEL and GEMINI_CREDENTIALS:
        st.session_state.available_models.append("Gemini_Pro")
    if GEMINI_FLASH_MODEL and GEMINI_CREDENTIALS:
        st.session_state.available_models.append("Gemini_Flash")
    if CLAUDE_API_KEY:
        st.session_state.available_models.append("Claude")
    if OPENAI_API_KEY:
        st.session_state.available_models.append("GPT4.1")

    st.session_state.selected_department = selected_dept

    if selected_dept != previous_dept:
        if selected_dept == "default":
            if "Gemini_Pro" in st.session_state.available_models:
                st.session_state.selected_model = "Gemini_Pro"
            elif st.session_state.available_models:
                st.session_state.selected_model = st.session_state.available_models[0]
        else:
            dept_data = get_department_by_name(selected_dept)
            if dept_data and "default_model" in dept_data and dept_data["default_model"]:
                if dept_data["default_model"] in st.session_state.available_models:
                    st.session_state.selected_model = dept_data["default_model"]

        save_user_settings(selected_dept, st.session_state.selected_model)
        st.rerun()

    if len(st.session_state.available_models) > 1:
        if "selected_model" not in st.session_state:
            if "Gemini_Pro" in st.session_state.available_models:
                default_model = "Gemini_Pro"
            else:
                default_model = st.session_state.available_models[0]
            st.session_state.selected_model = default_model

        try:
            model_index = st.session_state.available_models.index(st.session_state.selected_model)
        except (ValueError, AttributeError):
            model_index = 0
            if st.session_state.available_models:
                st.session_state.selected_model = st.session_state.available_models[0]

        selected_model = st.sidebar.selectbox(
            "AIモデル",
            st.session_state.available_models,
            index=model_index,
            key="model_selector"
        )

        if selected_model != previous_model:
            st.session_state.selected_model = selected_model
            save_user_settings(st.session_state.selected_department, st.session_state.selected_model)

    elif len(st.session_state.available_models) == 1:
        st.session_state.selected_model = st.session_state.available_models[0]

    st.sidebar.markdown("・入力および出力テキストは保存されません")
    st.sidebar.markdown("・出力結果は必ず確認してください")

    if st.sidebar.button("診療科管理", key="sidebar_department_management"):
        change_page("department_edit")
        st.rerun()

    if st.sidebar.button("プロンプト管理", key="sidebar_prompt_management"):
        change_page("prompt_edit")
        st.rerun()

    if st.sidebar.button("統計情報", key="sidebar_usage_statistics"):
        change_page("statistics")
        st.rerun()


def save_user_settings(department, model):
    try:
        settings_collection = get_settings_collection()
        settings_collection.update_one(
            {"setting_id": "user_preferences"},
            {"$set": {
                "selected_department": department,
                "selected_model": model,
                "updated_at": datetime.datetime.now()
            }},
            upsert=True
        )
    except Exception as e:
        print(f"設定の保存に失敗しました: {str(e)}")

def load_user_settings():
    try:
        settings_collection = get_settings_collection()
        settings = settings_collection.find_one({"setting_id": "user_preferences"})
        if settings:
            return settings.get("selected_department"), settings.get("selected_model")
        return None, None
    except Exception as e:
        print(f"設定の読み込みに失敗しました: {str(e)}")
        return None, None
