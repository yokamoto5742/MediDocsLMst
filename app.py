import streamlit as st

from ui_components.navigation import load_user_settings
from utils.env_loader import load_environment_variables
from utils.error_handlers import handle_error
from utils.prompt_manager import initialize_database
from views.department_management_page import department_management_ui
from views.main_page import main_page_app
from views.statistics_page import usage_statistics_ui
from views.prompt_management_page import prompt_management_ui

load_environment_variables()
initialize_database()

st.set_page_config(
    page_title="退院時サマリ作成アプリ",
    page_icon="📋",
    layout="wide"
)

if "discharge_summary" not in st.session_state:
    st.session_state.discharge_summary = ""
if "parsed_summary" not in st.session_state:
    st.session_state.parsed_summary = {}
if "selected_department" not in st.session_state:
    saved_dept, saved_model = load_user_settings()
    st.session_state.selected_department = saved_dept if saved_dept else "default"
    if saved_model:
        st.session_state.selected_model = saved_model
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"
if "success_message" not in st.session_state:
    st.session_state.success_message = None
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "summary_generation_time" not in st.session_state:
    st.session_state.summary_generation_time = None


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

    main_page_app()


@handle_error
def main():
    main_app()

if __name__ == "__main__":
    main()
