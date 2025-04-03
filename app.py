import os
import streamlit as st

from utils.auth import login_ui, require_login, logout, get_current_user, password_change_ui, can_edit_prompts, check_ip_access
from utils.config import get_config, GEMINI_CREDENTIALS, REQUIRE_LOGIN, IP_CHECK_ENABLED, IP_WHITELIST
from utils.env_loader import load_environment_variables
from utils.gemini_api import generate_discharge_summary
from utils.prompt_manager import (
    initialize_database, get_all_departments, get_all_prompts,
    create_or_update_prompt, delete_prompt, get_prompt_by_department,
    create_department, delete_department
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

# セッション状態の初期化
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




def toggle_password_change():
    st.session_state.show_password_change = not st.session_state.show_password_change


def change_page(page):
    st.session_state.current_page = page


def department_management_ui():
    st.title("診療科管理")

    if st.button("メイン画面に戻る", key="back_to_main_from_dept"):
        change_page("main")
        st.rerun()

    departments = get_all_departments()
    for dept in departments:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(dept)
        with col2:
            if dept not in ["内科"]:  # 内科は削除不可
                if st.button("削除", key=f"delete_{dept}"):
                    success, message = delete_department(dept)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()


    with st.form("add_department_form"):
        new_dept = st.text_input("診療科名")
        submit = st.form_submit_button("診療科を追加")

        if submit and new_dept:
            success, message = create_department(new_dept)
            if success:
                st.success(message)
            else:
                st.error(message)
            st.rerun()


def prompt_management_ui():
    st.title("プロンプト管理")

    if st.button("メイン画面に戻る", key="back_to_main"):
        change_page("main")
        st.rerun()

    departments = ["default"] + get_all_departments()
    selected_dept = st.selectbox(
        "診療科を選択",
        departments,
        format_func=lambda x: "全科共通" if x == "default" else x
    )

    prompt_data = get_prompt_by_department(selected_dept)

    with st.form("edit_prompt_form"):
        prompt_name = st.text_input(
            "プロンプト名",
            value=prompt_data.get("name", "") if prompt_data else "退院時サマリ"
        )
        prompt_content = st.text_area(
            "内容",
            value=prompt_data.get("content", "") if prompt_data else "",
            height=300
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("保存")
        with col2:
            if selected_dept != "default":
                delete_button = st.form_submit_button("削除")
            else:
                delete_button = False

        if submit:
            success, message = create_or_update_prompt(selected_dept, prompt_name, prompt_content)
            if success:
                st.success(message)
            else:
                st.error(message)

        if delete_button:
            success, message = delete_prompt(selected_dept)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

if "input_text" not in st.session_state:
    st.session_state.input_text = ""


def clear_inputs():
    st.session_state.input_text = ""
    st.session_state.discharge_summary = ""
    st.session_state.parsed_summary = {}
    st.session_state.clear_input = True

    for key in list(st.session_state.keys()):
        if key.startswith("input_text"):
            st.session_state[key] = ""


def main_app():
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

    if st.session_state.current_page == "prompt_edit":
        prompt_management_ui()
        return
    elif st.session_state.current_page == "department_edit":
        department_management_ui()
        return

    st.sidebar.markdown("・入力および出力テキストは保存されません")
    st.sidebar.markdown("・出力内容は必ず確認してください")

    if can_edit_prompts():
        if st.sidebar.button("診療科管理", key="department_management"):
            change_page("department_edit")
            st.rerun()
        if st.sidebar.button("プロンプト管理", key="prompt_management"):
            change_page("prompt_edit")
            st.rerun()

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
            if not GEMINI_CREDENTIALS:
                st.error("⚠️ Gemini APIの認証情報が設定されていません。環境変数を確認してください。")
                return

            if not input_text or len(input_text.strip()) < 10:
                st.warning("⚠️ カルテ情報を入力してください")
                return

            try:
                with st.spinner("退院時サマリを作成中..."):
                    discharge_summary = generate_discharge_summary(input_text, st.session_state.selected_department)

                    discharge_summary = format_discharge_summary(discharge_summary)

                    st.session_state.discharge_summary = discharge_summary

                    parsed_summary = parse_discharge_summary(discharge_summary)
                    st.session_state.parsed_summary = parsed_summary

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

    with col2:
        if st.button("テキストをクリア", on_click=clear_inputs):
            pass

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
