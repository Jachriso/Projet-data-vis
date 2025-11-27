
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

st.set_page_config(page_title="Dashboard Online Retail", layout="wide")
sns.set(style="whitegrid")

# ----------------------------
# LOAD DATA
# ----------------------------
'''@st.cache_data
def load_data():
    file_path = "../data/online_retail_II.xlsx"
    df_sheets = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    df = pd.concat(df_sheets.values(), ignore_index=True)
    
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Revenue'] = df['Quantity'] * df['Price']
    df['Annulation'] = df['Invoice'].astype(str).str.startswith('C')
    df.loc[df['Annulation'], 'Revenue'] *= -1
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['Day'] = df['InvoiceDate'].dt.date
    df['Month'] = df['InvoiceDate'].dt.to_period('M')
    
    df_clients = df[~df['Annulation']].copy()
    df_clients['is_return'] = df_clients['Quantity'] < 0
    df_clients['is_damage'] = (df_clients['Quantity'] < 0) & (df_clients['Price']==0)
    
    return df, df_clients

df, df_clients = load_data()'''
# ----------------------------
# LOAD DATA (depuis CSV compressés)
# ----------------------------
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
    df_clients['is_damage'] = (df_clients['Quantity'] < 0) & (df_clients['Price']==0)
    
    return df, df_clients

# Chargement
df, df_clients = load_data()


#on les stocke dans session_state pour qu'ils soient accessibles dans les autres pages
st.session_state["df"] = df
st.session_state["df_clients"] = df_clients


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

# ----------------------------
# NAVIGATION
# ----------------------------
page = st.sidebar.radio("Navigation", ["KPIs","Cohortes","Segments RFM","Scénarios","Produits","Plan d'action"])
# ----------------------------
# ----------------------------
# ----------------------------
# PAGE 1 : KPIs
# ----------------------------
# PAGE 1 : KPIs
# ----------------------------
# ----------------------------
# PAGE 1 : KPIs
# ----------------------------
if page == "KPIs":
    st.title("KPIs - Vue d'ensemble")

    # ----------------------------
    # Filtres actifs
    # ----------------------------
    st.subheader("Filtres actifs")
    st.write(f"Période : {df_filtered['InvoiceDate'].min().date()} → {df_filtered['InvoiceDate'].max().date()}")
    exclude_returns = st.checkbox("Exclure les retours/annulations", value=True)
    st.write(f"Exclure retours/annulations : {exclude_returns}")

    # ----------------------------
    # Filtrage des données
    # ----------------------------
    df_clients_filtered = df_filtered.copy()
    if exclude_returns:
        df_clients_filtered = df_clients_filtered[~df_clients_filtered['Annulation']]
        st.success("Retours exclus")

    # Renommer Customer ID pour uniformité
    df_clients_filtered = df_clients_filtered.rename(columns={'Customer ID':'CustomerID'})

    # ----------------------------
    # CLV moyen (empirique)
    # ----------------------------
    clv_empirique = df_clients_filtered.groupby('CustomerID')['Revenue'].sum().mean()

    # ----------------------------
    # CLV formule fermée (simplifiée)
    # ----------------------------
    retention_rate = df_clients_filtered.groupby('CustomerID').agg({'Invoice':'count'}).apply(lambda x: 1 if x['Invoice']>1 else 0, axis=1).mean()
    discount_rate = 0.01
    revenue_per_client = df_clients_filtered.groupby('CustomerID')['Revenue'].sum().mean()
    clv_formule = revenue_per_client * retention_rate / (1 + discount_rate - retention_rate)

    # ----------------------------
    # Rétention et RFM
    # ----------------------------
    snapshot = df_clients_filtered['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm = df_clients_filtered.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (snapshot - x.max()).days,
        'Invoice':'count',
        'Revenue':'sum'
    }).reset_index()
    rfm.columns = ['CustomerID','Recency','Frequency','Monetary']

    retained_clients = rfm[rfm['Frequency']>1]['CustomerID'].nunique()
    retention_pct = (retained_clients / rfm['CustomerID'].nunique())*100

    # ----------------------------
    # Cohorte et CA moyen par âge
    # ----------------------------
    df_clients_filtered['InvoiceMonth'] = df_clients_filtered['InvoiceDate'].dt.to_period('M').dt.to_timestamp()
    cohort = df_clients_filtered.groupby('CustomerID')['InvoiceMonth'].min().reset_index()
    cohort.columns = ['CustomerID','CohortMonth']

    df_merged = pd.merge(df_clients_filtered, cohort, on='CustomerID')
    df_merged['CohortAge'] = (df_merged['InvoiceMonth'].dt.year - df_merged['CohortMonth'].dt.year)*12 + \
                              (df_merged['InvoiceMonth'].dt.month - df_merged['CohortMonth'].dt.month)
    df_merged = df_merged[df_merged['CohortAge'] >= 0]

    # Rétention M+3
    retained_m3 = df_merged[df_merged['CohortAge'] >= 3]['CustomerID'].nunique()
    retention_m3_pct = (retained_m3 / rfm['CustomerID'].nunique())*100

    # CA moyen par âge de cohorte 0-24 mois
    ca_by_cohort_age = df_merged.groupby('CohortAge')['Revenue'].mean().reset_index()
    all_ages = pd.DataFrame({'CohortAge': range(0,25)})
    ca_by_cohort_age = all_ages.merge(ca_by_cohort_age, on='CohortAge', how='left').fillna(0)

    # ----------------------------
    # Segments RFM
    # ----------------------------
    r_labels = range(4,0,-1)
    f_labels = m_labels = range(1,5)
    rfm['R'] = pd.qcut(rfm['Recency'],4,labels=r_labels)
    rfm['F'] = pd.qcut(rfm['Frequency'],4,labels=f_labels)
    rfm['M'] = pd.qcut(rfm['Monetary'],4,labels=m_labels)
    rfm['RFM_Score'] = rfm['R'].astype(str)+rfm['F'].astype(str)+rfm['M'].astype(str)

    top_segments = rfm.groupby('RFM_Score').agg({'CustomerID':'nunique','Monetary':'sum'}).sort_values('Monetary', ascending=False).head(3)

    # ----------------------------
    # North Star Metric
    # ----------------------------
    north_star = df_clients_filtered['Revenue'].sum()/df_clients_filtered['CustomerID'].nunique()

    # ----------------------------
    # Affichage KPIs
    # ----------------------------
    cols = st.columns(8)
    cols[0].metric("Clients actifs", rfm['CustomerID'].nunique(),
                   help=f"Nombre de clients distincts (n={rfm['CustomerID'].nunique()})")
    cols[1].metric("Chiffres d'affaires (£)", f"{df_clients_filtered['Revenue'].sum():,.2f}",
                   help=f"Total des revenus (n={len(df_clients_filtered)})")
    cols[2].metric("Factures uniques", df_clients_filtered['Invoice'].nunique(),
                   help=f"Nombre de factures uniques (n={df_clients_filtered['Invoice'].nunique()})")
    cols[3].metric("CLV moyen (empirique) (£)", f"{clv_empirique:,.2f}",
                   help=f"Revenue cumulé / n clients (ex: £{clv_empirique:,.2f})")
    cols[4].metric("CLV formule fermée (£)", f"{clv_formule:,.2f}",
                   help=f"CLV théorique (ex: £{clv_formule:,.2f})")
    cols[5].metric("Rétention (>1 commande)", f"{retention_pct:.1f}%",
                   help=f"% clients >1 commande (n={retained_clients})")
    cols[6].metric("Rétention M+3 (%)", f"{retention_m3_pct:.1f}%",
                   help=f"% clients actifs après 3 mois (n={retained_m3})")
    cols[7].metric("North Star Metric (£)", f"{north_star:,.2f}",
                   help=f"CA moyen par client = £{north_star:,.2f}")

    # ----------------------------
    # Graphique CA moyen par âge de cohorte
    # ----------------------------
    st.markdown("### CA moyen par âge de cohorte (mois)")
    st.bar_chart(ca_by_cohort_age.rename(columns={'CohortAge':'Âge de cohorte (mois)','Revenue':'CA moyen (£)'}).set_index('Âge de cohorte (mois)'))

    # ----------------------------
    # Top 3 segments RFM
    # ----------------------------
    st.markdown("### Top 3 segments RFM par CA")
    st.dataframe(top_segments.rename(columns={'CustomerID':'Nb clients','Monetary':'CA (£)'}), use_container_width=True)

    # ----------------------------
    # Tous les segments RFM
    # ----------------------------
    st.markdown("### Tous les segments RFM")
    rfm_scores = rfm.groupby('RFM_Score').agg({'CustomerID':'nunique','Monetary':'sum'}).sort_values('Monetary', ascending=False)
    st.dataframe(rfm_scores.rename(columns={'CustomerID':'Nb clients','Monetary':'CA (£)'}), use_container_width=True)

    # ----------------------------
    # Aide / définitions
    # ----------------------------
    st.info(
        "Définitions :\n"
        "- **Clients actifs** : nombre de clients distincts.\n"
        "- **CLV moyen (empirique)** : valeur moyenne par client.\n"
        "- **CLV formule fermée** : estimation théorique basée sur revenu moyen, rétention et discount.\n"
        "- **Rétention (>1 commande)** : % de clients ayant passé >1 commande.\n"
        "- **Rétention M+3** : % clients actifs 3 mois après la première commande.\n"
        "- **North Star Metric** : CA moyen par client.\n"
        "- **CA moyen par âge de cohorte** : CA moyen selon l’âge de la cohorte en mois.\n"
        "- **Top segments RFM** : segments les plus rentables par CA.\n"
        "- **RFM Score global** : répartition complète des scores RFM."
    )


# ----------------------------
# PAGE 2 : Cohortes
# ----------------------------
elif page=="Cohortes":
    st.title("Analyse des cohortes")
    
    df_sales = df_clients_filtered[df_clients_filtered['Quantity']>0].copy()
    df_sales["CohortMonth"] = df_sales.groupby("Customer ID")["InvoiceDate"].transform("min").dt.to_period("M")
    df_sales["InvoiceMonth"] = df_sales["InvoiceDate"].dt.to_period("M")
    df_sales["CohortAge"] = ((df_sales["InvoiceMonth"].dt.year - df_sales["CohortMonth"].dt.year)*12 +
                             (df_sales["InvoiceMonth"].dt.month - df_sales["CohortMonth"].dt.month))
    
    cohort_counts = df_sales.groupby(["CohortMonth","CohortAge"])["Customer ID"].nunique().unstack(fill_value=0)
    
    st.subheader("Heatmap de rétention")
    fig, ax = plt.subplots(figsize=(12,6))
    sns.heatmap(cohort_counts, annot=True, fmt="d", cmap="Blues", cbar_kws={'label':'Clients actifs'})
    plt.ylabel("Cohorte d'acquisition")
    plt.xlabel("Âge de la cohorte (mois)")
    st.pyplot(fig)
    
    st.subheader("Courbe de densité du CA par âge de cohorte")
    ca_age = df_sales.groupby('CohortAge')['Revenue'].sum().reset_index()
    fig2, ax2 = plt.subplots(figsize=(12,4))
    sns.kdeplot(ca_age['Revenue'], fill=True, ax=ax2)
    ax2.set_xlabel("CA")
    ax2.set_title("Densité du chiffre d'affaires par âge de cohorte")
    st.pyplot(fig2)

# ----------------------------
# PAGE 3 : Segments RFM
# ----------------------------
elif page=="Segments RFM":
    st.title("Segmentation RFM")
    
    snapshot = df_clients_filtered['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm = df_clients_filtered.groupby('Customer ID').agg({
        'InvoiceDate': lambda x: (snapshot - x.max()).days,
        'Invoice':'count',
        'Revenue':'sum'
    }).reset_index()
    rfm.columns = ['CustomerID','Recency','Frequency','Monetary']
    
    # Scores RFM
    r_labels = range(4,0,-1)
    f_labels = m_labels = range(1,5)
    rfm['R'] = pd.qcut(rfm['Recency'],4,labels=r_labels)
    rfm['F'] = pd.qcut(rfm['Frequency'],4,labels=f_labels)
    rfm['M'] = pd.qcut(rfm['Monetary'],4,labels=m_labels)
    rfm['RFM_Score'] = rfm['R'].astype(str)+rfm['F'].astype(str)+rfm['M'].astype(str)
    
    st.subheader("Table RFM")
    st.dataframe(rfm.sort_values('RFM_Score',ascending=False))
    
    st.subheader("Distribution des segments RFM")
    fig, ax = plt.subplots(figsize=(10,4))
    rfm['RFM_Score'].value_counts().sort_index().plot(kind='bar', ax=ax, color='brown')
    ax.set_ylabel("Nombre de clients (n)")
    ax.set_xlabel("Segment RFM")
    st.pyplot(fig)

# ----------------------------
# PAGE 4 : Scénarios
# ----------------------------
elif page=="Scénarios":
    st.title("Simulation de scénarios")
    col1,col2,col3 = st.columns(3)
    with col1:
        retention_change = st.slider("Changement rétention (%)",-20,20,0)
    with col2:
        margin_change = st.slider("Changement marge (%)",-20,20,0)
    with col3:
        discount = st.slider("Remise (%)",0,50,0)
    
    baseline_revenue = df_clients_filtered['Revenue'].sum()
    scenario_revenue = baseline_revenue*(1+retention_change/100)*(1+margin_change/100)*(1-discount/100)
    
    st.metric("CA baseline (£)", f"{baseline_revenue:,.2f}")
    st.metric("CA scénario (£)", f"{scenario_revenue:,.2f}")
    
    # Barres/deltas
    fig, ax = plt.subplots(figsize=(6,4))
    ax.bar(['Baseline','Scénario'], [baseline_revenue, scenario_revenue], color=['blue','orange'])
    ax.set_ylabel("CA (£)")
    ax.set_title("Comparaison Baseline vs Scénario")
    st.pyplot(fig)

# ----------------------------
# PAGE 5 : Produits
# ----------------------------
elif page=="Produits":
    st.title("Produits les plus rentables")
    prod = df_clients_filtered.groupby(['StockCode','Description']).agg({'Revenue':'sum','Quantity':'sum'}).sort_values('Revenue',ascending=False).reset_index()
    st.dataframe(prod.head(20))
    
    st.subheader("Top 10 produits par CA")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.barh(prod['Description'].head(10)[::-1], prod['Revenue'].head(10)[::-1], color='green')
    ax.set_xlabel("CA (£)")
    ax.set_title("Top 10 produits")
    st.pyplot(fig)

# ----------------------------
# PAGE 6 : Plan d'action / Export
# ----------------------------
elif page=="Plan d'action":
    st.title("Export des données filtrées et graphiques")
    st.markdown("Télécharger CSV filtré ou PNG des graphiques")
    
    csv = df_clients_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("Télécharger CSV", data=csv, file_name="filtered_data.csv", mime='text/csv')
    
    # Export dynamique PNG : heatmap cohortes
    if st.button("Exporter heatmap cohortes PNG"):
        fig_bytes = BytesIO()
        fig.savefig(fig_bytes, format='png')
        fig_bytes.seek(0)
        st.download_button("Télécharger PNG", data=fig_bytes, file_name="cohort_heatmap.png", mime="image/png")
