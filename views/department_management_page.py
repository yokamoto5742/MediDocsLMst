import streamlit as st

from utils.config import GEMINI_MODEL, GEMINI_CREDENTIALS, GEMINI_FLASH_MODEL, CLAUDE_API_KEY, OPENAI_API_KEY, OPENAI_MODEL
from utils.error_handlers import handle_error
from utils.exceptions import AppError
from utils.prompt_manager import get_all_departments, create_department, delete_department, update_department_order, get_department_by_name, update_department
from ui_components.navigation import change_page


@handle_error
def department_management_ui():
    if st.button("作成画面に戻る", key="back_to_main_from_dept"):
        change_page("main")
        st.rerun()

    available_models = []
    if GEMINI_MODEL and GEMINI_CREDENTIALS:
        available_models.append("Gemini_Pro")
    if GEMINI_FLASH_MODEL and GEMINI_CREDENTIALS:
        available_models.append("Gemini_Flash")
    if CLAUDE_API_KEY:
        available_models.append("Claude")
    if OPENAI_API_KEY:
        available_models.append("GPT4.1")

    with st.form(key="add_department_form_unique"):
        new_dept = st.text_input("診療科", placeholder="追加する診療科を入力してください", label_visibility="collapsed")
        default_model = st.selectbox("デフォルトAIモデル", available_models) if available_models else None
        submit = st.form_submit_button("追加")

        if submit and new_dept:
            success, message = create_department(new_dept, default_model)
            if success:
                st.success(message)
            else:
                raise AppError(message)
            st.rerun()

    if "show_move_options" not in st.session_state:
        st.session_state.show_move_options = {}

    if "edit_dept" not in st.session_state:
        st.session_state.edit_dept = None

    departments = get_all_departments()

    for i, dept in enumerate(departments):
        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
        with col1:
            st.write(dept)

        with col2:
            if dept not in st.session_state.show_move_options:
                if st.button("⇅", key=f"move_{dept}"):
                    st.session_state.show_move_options[dept] = True
                    st.rerun()
            else:
                move_options_container = st.container()
                with move_options_container:
                    move_col1, move_col2, move_col3 = st.columns(3)

                    with move_col1:
                        if i > 0 and st.button("↑", key=f"up_action_{dept}"):
                            success, message = update_department_order(dept, i - 1)
                            if success:
                                st.success(message)
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
            if st.button("編集", key=f"edit_{dept}"):
                st.session_state.edit_dept = dept
                st.rerun()

        with col4:
            if st.button("削除", key=f"delete_{dept}"):
                success, message = delete_department(dept)
                if success:
                    st.success(message)
                else:
                    raise AppError(message)
                st.rerun()

    if st.session_state.edit_dept:
        dept = st.session_state.edit_dept
        department_data = get_department_by_name(dept)

        st.subheader(f"{dept}の設定")
        with st.form(key=f"edit_department_form_{dept}"):
            current_model = department_data.get("default_model")
            default_model = st.selectbox(
                "デフォルトAIモデル",
                available_models,
                index=available_models.index(current_model) if current_model in available_models else 0
            ) if available_models else None

            submit = st.form_submit_button("保存")

            if submit:
                success, message = update_department(dept, default_model)
                if success:
                    st.success(message)
                    st.session_state.edit_dept = None
                else:
                    raise AppError(message)
                st.rerun()

        if st.button("キャンセル", key="cancel_edit"):
            st.session_state.edit_dept = None
            st.rerun()
