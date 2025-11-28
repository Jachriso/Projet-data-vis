import streamlit as st
import seaborn as sns
from utils import load_data, definitions_pages

st.set_page_config(page_title="Dashboard Online Retail", layout="wide")
sns.set(style="whitegrid")


# ----------------------------
# LOAD DATA (depuis CSV compressés)
# ----------------------------
if "df_loaded" not in st.session_state:
    df, df_clients = load_data()
    st.session_state["df_loaded"] = True
    st.session_state["df"] = df
    st.session_state["df_clients"] = df_clients
else:
    df = st.session_state["df"]
    df_clients = st.session_state["df_clients"]


# ----------------------------
# NAVIGATION
# ----------------------------
accueil, kpis, cohortes, rfm, scenarios, plan_action = definitions_pages()


pg = st.navigation(
    {
        "": [accueil],
        "Reports": [kpis, cohortes, rfm],
        "Tools": [scenarios, plan_action]
    }
)

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filtres d'analyse")
date_range = st.sidebar.date_input("Période", [df['InvoiceDate'].min(), df['InvoiceDate'].max()])
countries = st.sidebar.multiselect("Pays", df['Country'].unique(), default=df['Country'].unique())
include_returns = True

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
st.session_state["include_returns"] = include_returns

pg.run()
