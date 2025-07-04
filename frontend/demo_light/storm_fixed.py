#!/usr/bin/env python3

# CRITICAL: Set these before ANY imports that might trigger torch
import os
import sys
import warnings

# Set environment variables to suppress torch issues
os.environ["TORCH_LOGS"] = ""
os.environ["PYTORCH_DISABLE_TORCH_FUNCTION_MODE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Suppress all torch-related warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*torch.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.*")
warnings.filterwarnings("ignore", message=".*torch.classes.*")

# Now safe to import streamlit and other packages
import streamlit as st

script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))

# Add the parent directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(script_dir)))

import demo_util
from pages_util import MyArticles, CreateNewArticle
from streamlit_float import *
from streamlit_option_menu import option_menu


def main():
    global database
    st.set_page_config(
        layout="wide",
        page_title="STORM - Enhanced Article Generator",
        page_icon="⚡",
        initial_sidebar_state="collapsed"
    )

    if "first_run" not in st.session_state:
        st.session_state["first_run"] = True

    # set api keys from secrets
    if st.session_state["first_run"]:
        try:
            for key, value in st.secrets.items():
                if type(value) == str:
                    os.environ[key] = value
        except Exception as e:
            st.error(f"Failed to load secrets: {e}")
            st.stop()

    # initialize session_state
    if "selected_article_index" not in st.session_state:
        st.session_state["selected_article_index"] = 0
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = 0
    if st.session_state.get("rerun_requested", False):
        st.session_state["rerun_requested"] = False
        st.rerun()

    pages = ["My Articles", "Create New Article"]

    with st.container():
        st.markdown("# ⚡ STORM - Enhanced Article Generator")
        st.markdown("*Powered by Enhanced Outline Generation & Multi-Perspective AI Research*")
        
        styles = {
            "container": {"padding": "0.2rem 0", "background-color": "#22222200"},
        }
        
        try:
            menu_selection = option_menu(
                None,
                pages,
                icons=["house", "search"],
                menu_icon="cast",
                default_index=0,
                orientation="horizontal",
                manual_select=st.session_state.selected_page,
                styles=styles,
                key="menu_selection",
            )
            if st.session_state.get("manual_selection_override", False):
                menu_selection = pages[st.session_state["selected_page"]]
                st.session_state["manual_selection_override"] = False
                st.session_state["selected_page"] = None

            if menu_selection == "My Articles":
                demo_util.clear_other_page_session_state(page_index=2)
                MyArticles.my_articles_page()
            elif menu_selection == "Create New Article":
                demo_util.clear_other_page_session_state(page_index=3)
                CreateNewArticle.create_new_article_page()
                
        except Exception as e:
            st.error(f"Application error: {e}")
            st.markdown("### Debug Information:")
            st.code(f"Error type: {type(e).__name__}")
            st.code(f"Error message: {str(e)}")


if __name__ == "__main__":
    main()