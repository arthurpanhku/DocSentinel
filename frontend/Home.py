import pandas as pd
import plotly.express as px
import streamlit as st
from utils import ApiClient

# Page Config
st.set_page_config(
    page_title="Arthor Agent Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
st.sidebar.image("frontend/assets/arthor-architect.png", width=180)
st.sidebar.title("Arthor Agent")
st.sidebar.markdown("---")

# API Configuration
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

with st.sidebar.expander("⚙️ Configuration", expanded=True):
    api_url = st.text_input("API Base URL", value=st.session_state.api_url)
    if api_url != st.session_state.api_url:
        st.session_state.api_url = api_url
        st.rerun()

    client = ApiClient(st.session_state.api_url)
    if client.health_check():
        st.success("API Connected ✅")
    else:
        st.error("API Disconnected ❌")

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **Arthor Agent**
    Automated Security Assessment Platform.

    [GitHub Repo](https://github.com/arthurpanhku/Arthor-Agent)
    """
)

# Main Content
c1, c2 = st.columns([1, 4])
with c1:
    st.image("frontend/assets/arthor-architect.png", width=150)
with c2:
    st.title("Security Operations Dashboard")
    st.caption("Powered by Arthor Architect - Your AI Security Partner")

st.markdown("---")

# Mock Data for Dashboard (Since we don't have persistent history DB yet)
# Ideally, this would come from GET /api/v1/stats or similar
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Assessments", value="12", delta="2 today")
with col2:
    st.metric(label="High Risks Found", value="45", delta="-5", delta_color="inverse")
with col3:
    st.metric(label="Knowledge Base Docs", value="8", delta="1 new")
with col4:
    st.metric(label="Avg. Processing Time", value="1.2m", delta="-10s")

st.markdown("### 📊 Recent Activity")

# Mock Chart
data = pd.DataFrame(
    {
        "Date": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Assessments": [4, 5, 8, 3, 7, 2, 4],
        "Risks": [10, 12, 15, 5, 18, 4, 8],
    }
)

fig = px.bar(
    data,
    x="Date",
    y=["Assessments", "Risks"],
    title="Weekly Assessment Volume & Risks",
    barmode="group",
    color_discrete_map={"Assessments": "#3b82f6", "Risks": "#ef4444"},
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🚀 Quick Actions")
c1, c2 = st.columns(2)
with c1:
    st.info("To start a new security review, go to **Assessment Workbench**.")
with c2:
    st.info("To update policies or standards, go to **Knowledge Base**.")

# Custom CSS - Removed to ensure compatibility with both Light and Dark modes
# st.markdown("""
# <style>
#     .stMetric {
#         background-color: #1e293b;
#         padding: 15px;
#         border-radius: 10px;
#         border: 1px solid #334155;
#     }
#     [data-testid="stSidebar"] {
#         background-color: #0f172a;
#     }
# </style>
# """, unsafe_allow_html=True)
