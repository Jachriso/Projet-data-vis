import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from app.utils import load_data

st.set_page_config(page_title="Dashboard Online Retail", layout="wide")
sns.set(style="whitegrid")


# ----------------------------
# LOAD DATA (depuis CSV compressés)
# ----------------------------
df, df_clients = load_data()


# ----------------------------
# NAVIGATION
# ----------------------------
st.sidebar.header("Navigation")

accueil = st.Page("pages/accueil.py", title="Accueil", icon=":material/home:", default=True)
kpis = st.Page("pages/01_KPIs.py", title="KPIs", icon=":material/analytics:")
cohortes = st.Page("pages/02_Cohortes.py", title="Cohortes", icon=":material/diversity_3:")
rfm = st.Page("pages/03_Segments_RFM.py", title="Segments RFM", icon=":material/trending_up:")
scenarios = st.Page("pages/04_Scenarios.py", title="Scenarios", icon=":material/psychology:")
plan_action = st.Page("pages/05_Plan_action.py", title="Plan d'action", icon=":material/checklist:")

pg = st.navigation(
    {
        "": [accueil],
        "Reports": [kpis, cohortes, rfm],
        "Tools": [scenarios, plan_action]
    }
)

pg.run()


# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filtres d'analyse")
date_range = st.sidebar.date_input("Période", [df['InvoiceDate'].min(), df['InvoiceDate'].max()])
countries = st.sidebar.multiselect("Pays", df['Country'].unique(), default=df['Country'].unique())
include_returns = st.sidebar.checkbox("Inclure retours", True)

# Badge Retours exclus
if not include_returns:
    st.sidebar.markdown('<span style="color:red;font-weight:bold">⚠️ Retours exclus</span>', unsafe_allow_html=True)

# Apply filters
df_filtered = df[(df['InvoiceDate'].dt.date >= date_range[0]) &
                 (df['InvoiceDate'].dt.date <= date_range[1]) &
                 (df['Country'].isin(countries))]
if not include_returns:
    df_filtered = df_filtered[~df_filtered['is_return']]
df_clients_filtered = df_filtered[~df_filtered['Annulation']].copy()

#on les stocke dans session_state pour qu'ils soient accessibles dans les autres pages
st.session_state["df"] = df
st.session_state["df_clients"] = df_clients
st.session_state["df_filtered"] = df_filtered
st.session_state["df_clients_filtered"] = df_clients_filtered
