import datetime
import os

import pandas as pd
import streamlit as st

from utils.auth import login_ui, require_login, logout, get_current_user, password_change_ui, can_edit_prompts, check_ip_access
from utils.config import get_config, GEMINI_CREDENTIALS, GEMINI_MODEL, GEMINI_FLASH_MODEL, CLAUDE_API_KEY, CLAUDE_MODEL, SELECTED_AI_MODEL, REQUIRE_LOGIN, IP_CHECK_ENABLED, IP_WHITELIST
from utils.claude_api import generate_discharge_summary as claude_generate_discharge_summary
from utils.constants import MESSAGES
from utils.db import get_usage_collection
from utils.env_loader import load_environment_variables
from utils.error_handlers import handle_error
from utils.exceptions import AppError, AuthError, APIError, DatabaseError
from utils.gemini_api import generate_discharge_summary as gemini_generate_discharge_summary
from utils.prompt_manager import (
    initialize_database, get_all_departments, get_all_prompts,
    create_or_update_prompt, delete_prompt, get_prompt_by_department,
    create_department, delete_department, update_department_order
)
from utils.text_processor import format_discharge_summary, parse_discharge_summary


load_environment_variables()
initialize_database()

require_login_setting = REQUIRE_LOGIN

st.set_page_config(
    page_title="退院時サマリ作成アプリ",
    page_icon="📋",
    layout="wide"
)

if "discharge_summary" not in st.session_state:
    st.session_state.discharge_summary = ""
if "parsed_summary" not in st.session_state:
    st.session_state.parsed_summary = {}
if "show_password_change" not in st.session_state:
    st.session_state.show_password_change = False
if "selected_department" not in st.session_state:
    st.session_state.selected_department = "default"
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"
if "success_message" not in st.session_state:
    st.session_state.success_message = None


def toggle_password_change():
    st.session_state.show_password_change = not st.session_state.show_password_change


def change_page(page):
    st.session_state.current_page = page


@handle_error
def department_management_ui():
    if st.button("メイン画面に戻る", key="back_to_main_from_dept"):
        change_page("main")
        st.rerun()

    if "show_move_options" not in st.session_state:
        st.session_state.show_move_options = {}

    departments = get_all_departments()

    # 診療科一覧とその順序変更ボタンを表示
    for i, dept in enumerate(departments):
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(dept)

        with col2:
            # 移動ボタン - 上下をまとめる
            if dept not in st.session_state.show_move_options:
                if st.button("⇅", key=f"move_{dept}"):
                    st.session_state.show_move_options[dept] = True
                    st.rerun()
            else:
                # 移動オプションを表示
                move_options_container = st.container()
                with move_options_container:
                    move_col1, move_col2, move_col3 = st.columns(3)

                    with move_col1:
                        if i > 0 and st.button("↑", key=f"up_action_{dept}"):
                            success, message = update_department_order(dept, i - 1)
                            if success:
                                st.success(message)
                                # 移動後はUIを閉じる
                                del st.session_state.show_move_options[dept]
                            else:
                                raise AppError(message)
                            st.rerun()

                    with move_col2:
                        if i < len(departments) - 1 and st.button("↓", key=f"down_action_{dept}"):
                            success, message = update_department_order(dept, i + 1)
                            if success:
                                st.success(message)
                                del st.session_state.show_move_options[dept]
                            else:
                                raise AppError(message)
                            st.rerun()

                    with move_col3:
                        if st.button("✕", key=f"cancel_move_{dept}"):
                            del st.session_state.show_move_options[dept]
                            st.rerun()

        with col3:
            if dept not in ["内科"]:
                if st.button("削除", key=f"delete_{dept}"):
                    success, message = delete_department(dept)
                    if success:
                        st.success(message)
                    else:
                        raise AppError(message)
                    st.rerun()

    with st.form(key="add_department_form_unique"):
        new_dept = st.text_input("診療科名")
        submit = st.form_submit_button("診療科を追加")

        if submit and new_dept:
            success, message = create_department(new_dept)
            if success:
                st.success(message)
            else:
                raise AppError(message)
            st.rerun()


@handle_error
def prompt_management_ui():
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    if st.button("メイン画面に戻る", key="back_to_main"):
        change_page("main")
        st.rerun()

    if "selected_dept_for_prompt" not in st.session_state:
        st.session_state.selected_dept_for_prompt = "default"

    departments = ["default"] + get_all_departments()
    selected_dept = st.selectbox(
        "診療科を選択",
        departments,
        index=departments.index(
            st.session_state.selected_dept_for_prompt) if st.session_state.selected_dept_for_prompt in departments else 0,
        format_func=lambda x: "全科共通" if x == "default" else x,
        key="prompt_department_selector"
    )

    st.session_state.selected_dept_for_prompt = selected_dept

    prompt_data = get_prompt_by_department(selected_dept)

    with st.form(key=f"edit_prompt_form_{selected_dept}"):
        prompt_name = st.text_input(
            "プロンプト名",
            value=prompt_data.get("name", "") if prompt_data else "退院時サマリ",
            key=f"prompt_name_{selected_dept}"
        )
        prompt_content = st.text_area(
            "内容",
            value=prompt_data.get("content", "") if prompt_data else "",
            height=200,
            key=f"prompt_content_{selected_dept}"
        )

        submit = st.form_submit_button("プロンプトを保存")

        if submit:
            success, message = create_or_update_prompt(selected_dept, prompt_name, prompt_content)
            if success:
                st.success(message)
            else:
                raise AppError(message)

    if selected_dept != "default":
        if st.button("プロンプトを削除", key=f"delete_prompt_{selected_dept}", type="primary"):
            success, message = delete_prompt(selected_dept)
            if success:
                st.session_state.success_message = message
                st.session_state.selected_dept_for_prompt = "default"
                st.rerun()
            else:
                raise AppError(message)


def clear_inputs():
    st.session_state.input_text = ""
    st.session_state.discharge_summary = ""
    st.session_state.parsed_summary = {}
    st.session_state.clear_input = True

    for key in list(st.session_state.keys()):
        if key.startswith("input_text"):
            st.session_state[key] = ""


@handle_error
def render_sidebar():
    user = get_current_user()
    if user:
        st.sidebar.success(f"ログイン中: {user['username']}")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("パスワード変更", key="show_password_change_button"):
                toggle_password_change()
        with col2:
            if st.button("ログアウト"):
                logout()
                st.rerun()

        if st.session_state.show_password_change:
            with st.sidebar:
                password_change_ui()
                if st.button("キャンセル"):
                    st.session_state.show_password_change = False
                    st.rerun()

    departments = ["default"] + get_all_departments()
    selected_dept = st.sidebar.selectbox(
        "診療科",
        departments,
        index=departments.index(st.session_state.selected_department),
        format_func=lambda x: "全科共通" if x == "default" else x,
        key="department_selector"
    )
    st.session_state.selected_department = selected_dept

    available_models = []
    if GEMINI_MODEL and GEMINI_CREDENTIALS:
        available_models.append("Gemini_Pro")
    if GEMINI_FLASH_MODEL and GEMINI_CREDENTIALS:
        available_models.append("Gemini_Flash")
    if CLAUDE_API_KEY:
        available_models.append("Claude")

    if len(available_models) > 1:
        if "selected_model" not in st.session_state:
            default_model = SELECTED_AI_MODEL
            if default_model not in available_models and available_models:
                default_model = available_models[0]
            st.session_state.selected_model = default_model

        selected_model = st.sidebar.selectbox(
            "AIモデル",
            available_models,
            index=available_models.index(
                st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
            key="model_selector"
        )
        st.session_state.selected_model = selected_model

    elif len(available_models) == 1:
        st.session_state.selected_model = available_models[0]

    st.sidebar.markdown("・入力および出力テキストは保存されません")
    st.sidebar.markdown("・出力内容は必ず確認してください")

    if can_edit_prompts():
        if st.sidebar.button("診療科管理", key="department_management"):
            change_page("department_edit")
            st.rerun()
        if st.sidebar.button("プロンプト管理", key="prompt_management"):
            change_page("prompt_edit")
            st.rerun()

        if st.sidebar.button("統計情報", key="usage_statistics"):
            change_page("statistics")
            st.rerun()


def render_input_section():
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False

    input_text = st.text_area(
        "カルテ情報入力",
        height=100,
        placeholder="ここを右クリックしてテキストを貼り付けてください...",
        key="input_text"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("退院時サマリ作成", type="primary"):
            process_discharge_summary(input_text)

    with col2:
        if st.button("テキストをクリア", on_click=clear_inputs):
            pass


@handle_error
def process_discharge_summary(input_text):
    if not GEMINI_CREDENTIALS and not CLAUDE_API_KEY:
        raise APIError(MESSAGES["NO_API_CREDENTIALS"])

    if not input_text or len(input_text.strip()) < 100:
        st.warning(MESSAGES["INPUT_TOO_SHORT"])
        return

    try:
        with st.spinner("退院時サマリを作成中..."):
            selected_model = getattr(st.session_state, "selected_model",
                                     available_models[0] if available_models else None)

            if selected_model == "Claude" and CLAUDE_API_KEY:
                discharge_summary, input_tokens, output_tokens = claude_generate_discharge_summary(
                    input_text,
                    st.session_state.selected_department,
                )
                model_detail = selected_model
            elif selected_model == "Gemini_Pro" and GEMINI_MODEL and GEMINI_CREDENTIALS:
                discharge_summary, input_tokens, output_tokens = gemini_generate_discharge_summary(
                    input_text,
                    st.session_state.selected_department,
                    GEMINI_MODEL,
                )
                model_detail = GEMINI_MODEL
            elif selected_model == "Gemini_Flash" and GEMINI_FLASH_MODEL and GEMINI_CREDENTIALS:
                discharge_summary, input_tokens, output_tokens = gemini_generate_discharge_summary(
                    input_text,
                    st.session_state.selected_department,
                    GEMINI_FLASH_MODEL,
                )
                model_detail = GEMINI_FLASH_MODEL
            else:
                raise APIError(MESSAGES["NO_API_CREDENTIALS"])

            discharge_summary = format_discharge_summary(discharge_summary)
            st.session_state.discharge_summary = discharge_summary

            parsed_summary = parse_discharge_summary(discharge_summary)
            st.session_state.parsed_summary = parsed_summary

            usage_collection = get_usage_collection()
            usage_data = {
                "date": datetime.datetime.now(),
                "model": selected_model,
                "model_detail": model_detail,
                "department": st.session_state.selected_department,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
            usage_collection.insert_one(usage_data)

    except Exception as e:
        raise APIError(f"退院時サマリの作成中にエラーが発生しました: {str(e)}")


def render_summary_results():
    if st.session_state.discharge_summary:
        if st.session_state.parsed_summary:
            tabs = st.tabs([
                "全文", "入院期間", "現病歴", "入院時検査",
                "入院中の治療経過", "退院申し送り", "禁忌/アレルギー"
            ])

            with tabs[0]:
                st.subheader("全文")
                st.code(st.session_state.discharge_summary,
                        language=None,
                        height=150
                        )

            sections = ["入院期間", "現病歴", "入院時検査", "入院中の治療経過", "退院申し送り", "禁忌/アレルギー"]
            for i, section in enumerate(sections, 1):
                with tabs[i]:
                    section_content = st.session_state.parsed_summary.get(section, "")
                    st.subheader(section)
                    st.code(section_content,
                            language=None,
                            height=150
                            )

        st.info("💡 テキストエリアの右上にマウスを合わせ、左クリックでコピーできます")


@handle_error
def usage_statistics_ui():
    if st.button("メイン画面に戻る", key="back_to_main_from_stats"):
        change_page("main")
        st.rerun()

    usage_collection = get_usage_collection()

    col1, col2 = st.columns(2)

    with col1:
        today = datetime.datetime.now().date()
        start_date = st.date_input("開始日", today - datetime.timedelta(days=30))
        end_date = st.date_input("終了日", today)

    with col2:
        models = ["すべて", "Claude", "Gemini_Pro", "Gemini_Flash"]
        selected_model = st.selectbox("AIモデル", models, index=0)

    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

    query = {
        "date": {
            "$gte": start_datetime,
            "$lte": end_datetime
        }
    }

    if selected_model != "すべて":
        if selected_model == "Gemini_Pro":
            query["model"] = "Gemini"
            query["model_detail"] = {"$not": {"$regex": "flash", "$options": "i"}}
        elif selected_model == "Gemini_Flash":
            query["model"] = "Gemini"
            query["model_detail"] = {"$regex": "flash", "$options": "i"}
        else:  # Claude
            query["model"] = selected_model

    total_summary = usage_collection.aggregate([
        {"$match": query},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "total_input_tokens": {"$sum": "$input_tokens"},
            "total_output_tokens": {"$sum": "$output_tokens"},
            "total_tokens": {"$sum": "$total_tokens"}
        }}
    ])

    total_summary = list(total_summary)

    if not total_summary:
        st.info("指定した期間のデータがありません")
        return

    dept_summary = usage_collection.aggregate([
        {"$match": query},
        {"$group": {
            "_id": "$department",
            "count": {"$sum": 1},
            "input_tokens": {"$sum": "$input_tokens"},
            "output_tokens": {"$sum": "$output_tokens"},
            "total_tokens": {"$sum": "$total_tokens"}
        }},
        {"$sort": {"count": -1}}
    ])

    dept_summary = list(dept_summary)

    records = usage_collection.find(
        query,
        {
            "date": 1,
            "model": 1,
            "model_detail": 1,
            "input_tokens": 1,
            "output_tokens": 1,
            "total_tokens": 1,
            "_id": 0
        }
    ).sort("date", -1)  # 日付の降順で取得

    data = []
    for stat in dept_summary:
        dept_name = "全科共通" if stat["_id"] == "default" else stat["_id"]
        data.append({
            "診療科": dept_name,
            "作成件数": stat["count"],
            "入力トークン": stat["input_tokens"],
            "出力トークン": stat["output_tokens"],
            "合計トークン": stat["total_tokens"]
        })

    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True)

    detail_data = []
    for record in records:
        model = record.get("model", "")
        model_detail = record.get("model_detail", "")

        if model == "Gemini":
            if "flash" in str(model_detail).lower():
                model_info = "Gemini_Flash"
            else:
                model_info = "Gemini_Pro"
        else:
            model_info = model

        detail_data.append({
            "作成日": record["date"].strftime("%Y-%m-%d"),
            "AIモデル": model_info,
            "入力トークン": record["input_tokens"],
            "出力トークン": record["output_tokens"],
            "合計トークン": record["total_tokens"]
        })

    detail_df = pd.DataFrame(detail_data)
    st.dataframe(detail_df, hide_index=True)


@handle_error
def main_app():
    if st.session_state.current_page == "prompt_edit":
        prompt_management_ui()
        return
    elif st.session_state.current_page == "department_edit":
        department_management_ui()
        return
    elif st.session_state.current_page == "statistics":
        usage_statistics_ui()
        return

    render_sidebar()
    render_input_section()
    render_summary_results()


@handle_error
def main():
    if IP_CHECK_ENABLED:
        if not check_ip_access(IP_WHITELIST):
            st.stop()

    if require_login_setting:
        if require_login():
            main_app()
    else:
        main_app()


if __name__ == "__main__":
    main()
