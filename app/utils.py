import streamlit as st
import pandas as pd
import io

@st.cache_data
def load_data():
    # Lecture des CSV compressés
    df = pd.read_csv("../data/processed/retail_clean_full.csv.gz", compression="gzip")
    df_clients = pd.read_csv("../data/processed/retail_clean_clients.csv.gz", compression="gzip")

    # S'assurer que les dates sont bien au format datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df_clients['InvoiceDate'] = pd.to_datetime(df_clients['InvoiceDate'])
    df['Revenue'] = df['Quantity'] * df['Price']
    df['Annulation'] = df['Invoice'].astype(str).str.startswith('C')
    df.loc[df['Annulation'], 'Revenue'] *= -1
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['Day'] = df['InvoiceDate'].dt.date
    df['Month'] = df['InvoiceDate'].dt.to_period('M')

    df_clients = df[~df['Annulation']].copy()
    df_clients['is_return'] = df_clients['Quantity'] < 0
    df_clients['is_damage'] = (df_clients['Quantity'] < 0) & (df_clients['Price'] == 0)

# jeznbdpiéjê

    return df, df_clients

def definitions_pages():
    accueil = st.Page("pages/accueil.py", title="Accueil", icon=":material/home:", default=True)
    kpis = st.Page("pages/01_KPIs.py", title="KPIs", icon=":material/analytics:")
    cohortes = st.Page("pages/02_Cohortes.py", title="Cohortes", icon=":material/diversity_3:")
    rfm = st.Page("pages/03_Segments_RFM.py", title="Segments RFM", icon=":material/trending_up:")
    scenarios = st.Page("pages/04_Scenarios.py", title="Scenarios", icon=":material/psychology:")
    plan_action = st.Page("pages/05_Plan_action.py", title="Plan d'action", icon=":material/checklist:")

    return accueil, kpis, cohortes, rfm, scenarios, plan_action

def session_setup():
    df = st.session_state["df"]
    df_clients = st.session_state["df_clients"]
    df_filtered = st.session_state["df_filtered"]
    df_clients_filtered = st.session_state["df_clients_filtered"]

    return df, df_clients, df_filtered, df_clients_filtered


def download_chart(fig, file_name, label=" Télécharger le graphique"):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=300)
    buf.seek(0)
    
    st.download_button(
        label=label,
        data=buf,
        file_name=file_name,
        mime="image/png"
    )