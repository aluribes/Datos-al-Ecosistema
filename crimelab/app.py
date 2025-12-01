"""
CrimeLab: Seguridad Ciudadana - Santander
==========================================

Main entrypoint for the Streamlit multipage application.
Uses st.Page and st.navigation for proper URL routing.

Routes:
- /           : Home page (presentation)
- /dashboard  : Analytical dashboard with maps and charts
- /chatbot    : ALBA chatbot assistant
- /about      : Project information
"""

import streamlit as st
import os
from PIL import Image

# ============================
# PAGE CONFIGURATION
# ============================
st.set_page_config(
    page_title="CrimeLab: Seguridad Ciudadana – Santander",
    page_icon="🛡️",
    layout="wide",
)

# ============================
# LOAD STYLES
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
styles_path = os.path.join(BASE_DIR, "assets", "styles.css")

if os.path.exists(styles_path):
    with open(styles_path, "r", encoding="utf-8", errors="ignore") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ============================
# LOGO IN SIDEBAR
# ============================
logo_path = os.path.join(BASE_DIR, "assets", "logo_crimelab.png")

if os.path.exists(logo_path):
    try:
        logo = Image.open(logo_path)
        st.sidebar.markdown("<div class='logo-container'>", unsafe_allow_html=True)
        st.sidebar.image(logo, use_container_width=False, width=150)
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
    except Exception:
        pass

# ============================
# DEFINE PAGES
# ============================
# Import page render functions
from pages.home import render as home_render
from pages.dashboard import render as dashboard_render
from pages.chatbot import render as chatbot_render
from pages.about import render as about_render

# Define pages with st.Page
home_page = st.Page(
    home_render,
    title="Inicio",
    icon="🏠",
    url_path="",  # Root path
    default=True
)

dashboard_page = st.Page(
    dashboard_render,
    title="Visor Analítico",
    icon="📊",
    url_path="dashboard"
)

chatbot_page = st.Page(
    chatbot_render,
    title="ALBA Chatbot",
    icon="🤖",
    url_path="chatbot"
)

about_page = st.Page(
    about_render,
    title="Información",
    icon="ℹ️",
    url_path="about"
)

# ============================
# NAVIGATION
# ============================
pg = st.navigation(
    {
        "Principal": [home_page],
        "Herramientas": [dashboard_page, chatbot_page],
        "Documentación": [about_page],
    }
)

# ============================
# RUN SELECTED PAGE
# ============================
pg.run()
