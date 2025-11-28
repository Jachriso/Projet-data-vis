import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from app.utils import session_setup

st.title("KPIs - Vue d'ensemble")

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

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