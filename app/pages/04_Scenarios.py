import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from app.utils import session_setup


st.title("Simulation de scénarios - Paramètres avancés")

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

# Préparer les données baseline
df_scenario = df_filtered.copy()

# ----------------------------
# Section 1: Paramètres de simulation
# ----------------------------
st.header("🎯 Paramètres de simulation")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Paramètres financiers")
    marge_change = st.slider("Changement de marge (%)", -50, 100, 0, 5,
                             help="Impact sur la marge bénéficiaire")
    taux_actualisation = st.slider("Taux d'actualisation (d) (%)", 0.0, 20.0, 1.0, 0.5,
                                   help="Taux pour calcul CLV actualisée")

with col2:
    st.subheader("Paramètres clients")
    retention_change = st.slider("Changement rétention (r) (%)", -50, 100, 0, 5,
                                 help="Impact sur le taux de rétention client")

# ----------------------------
# Section 2: Remise et application
# ----------------------------
st.header("💰 Politique de remise")

col3, col4 = st.columns(2)
with col3:
    remise_moyenne = st.slider("Remise moyenne (%)", 0, 50, 0, 5,
                               help="Remise à appliquer")
with col4:
    application_remise = st.radio("Application de la remise",
                                  ["Globale", "Par segment RFM"],
                                  help="Appliquer la remise à tous les clients ou par segment")

# ----------------------------
# Section 3: Filtres de ciblage
# ----------------------------
st.header("🎯 Ciblage")

col5, col6 = st.columns(2)
with col5:
    inclure_retours_scenario = st.checkbox("Inclure les retours dans la simulation",
                                           value=include_returns,
                                           help="Inclure ou exclure les retours/annulations")

with col6:
    # Préparer la liste des cohortes
    df_scenario['CohortMonth'] = df_scenario.groupby('Customer ID')['InvoiceDate'].transform('min').dt.to_period(
        'M')
    cohortes_disponibles = ['Toutes'] + sorted(df_scenario['CohortMonth'].dropna().astype(str).unique().tolist())
    cohorte_cible = st.selectbox("Cohorte cible", cohortes_disponibles,
                                 help="Sélectionner une cohorte spécifique ou toutes")

# ----------------------------
# Section 4: Calculs baseline
# ----------------------------
st.header("📊 Résultats de la simulation")

# Filtrer selon les paramètres
if not inclure_retours_scenario:
    df_scenario = df_scenario[~df_scenario['is_return']]

if cohorte_cible != 'Toutes':
    df_scenario = df_scenario[df_scenario['CohortMonth'].astype(str) == cohorte_cible]

df_scenario = df_scenario[~df_scenario['Annulation']].copy()
df_scenario = df_scenario.rename(columns={'Customer ID': 'CustomerID'})

# Calculs baseline
baseline_ca = df_scenario['Revenue'].sum()
baseline_nb_clients = df_scenario['CustomerID'].nunique()
baseline_retention = df_scenario.groupby('CustomerID').agg({'Invoice': 'count'}).apply(
    lambda x: 1 if x['Invoice'] > 1 else 0, axis=1).mean()

# CLV baseline
revenue_per_client_baseline = df_scenario.groupby('CustomerID')['Revenue'].sum().mean()
discount_rate_baseline = taux_actualisation / 100
clv_baseline = revenue_per_client_baseline * baseline_retention / (
            1 + discount_rate_baseline - baseline_retention) if (
                                                                            1 + discount_rate_baseline - baseline_retention) > 0 else 0

# ----------------------------
# Section 5: Calculs scénario
# ----------------------------

# Impact marge
scenario_marge_multiplier = 1 + (marge_change / 100)

# Impact rétention
scenario_retention = baseline_retention * (1 + retention_change / 100)
scenario_retention = max(0, min(1, scenario_retention))  # Limiter entre 0 et 1

# Impact remise par segment ou global
if application_remise == "Par segment RFM":
    # Calculer RFM pour application différenciée
    snapshot = df_scenario['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm_scenario = df_scenario.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (snapshot - x.max()).days,
        'Invoice': 'count',
        'Revenue': 'sum'
    }).reset_index()
    rfm_scenario.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']

    r_labels = range(4, 0, -1)
    f_labels = m_labels = range(1, 5)
    rfm_scenario['R'] = pd.qcut(rfm_scenario['Recency'], 4, labels=r_labels, duplicates='drop')
    rfm_scenario['F'] = pd.qcut(rfm_scenario['Frequency'], 4, labels=f_labels, duplicates='drop')
    rfm_scenario['M'] = pd.qcut(rfm_scenario['Monetary'], 4, labels=m_labels, duplicates='drop')
    rfm_scenario['RFM_Score'] = rfm_scenario['R'].astype(str) + rfm_scenario['F'].astype(str) + rfm_scenario[
        'M'].astype(str)

    # Appliquer remise variable selon segment (exemple: plus de remise pour segments premium)
    rfm_scenario['remise_segment'] = rfm_scenario['RFM_Score'].apply(
        lambda x: remise_moyenne * 1.5 if x.startswith('4') or x.startswith('3')
        else remise_moyenne
    )
    rfm_scenario['remise_segment'] = rfm_scenario['remise_segment'].clip(0, 50)

    df_scenario = df_scenario.merge(rfm_scenario[['CustomerID', 'remise_segment']], on='CustomerID', how='left')
    df_scenario['remise_segment'] = df_scenario['remise_segment'].fillna(remise_moyenne)
    remise_multiplier = 1 - (df_scenario['remise_segment'] / 100)
    scenario_ca = (df_scenario['Revenue'] * scenario_marge_multiplier * remise_multiplier).sum()
else:
    # Remise globale
    remise_multiplier = 1 - (remise_moyenne / 100)
    scenario_ca = baseline_ca * scenario_marge_multiplier * remise_multiplier

# CLV scénario
revenue_per_client_scenario = scenario_ca / baseline_nb_clients
discount_rate_scenario = taux_actualisation / 100
clv_scenario = revenue_per_client_scenario * scenario_retention / (
            1 + discount_rate_scenario - scenario_retention) if (
                                                                            1 + discount_rate_scenario - scenario_retention) > 0 else 0

# Calcul des deltas
delta_ca = scenario_ca - baseline_ca
delta_ca_pct = (delta_ca / baseline_ca * 100) if baseline_ca > 0 else 0
delta_clv = clv_scenario - clv_baseline
delta_clv_pct = (delta_clv / clv_baseline * 100) if clv_baseline > 0 else 0
delta_retention = scenario_retention - baseline_retention
delta_retention_pct = (delta_retention / baseline_retention * 100) if baseline_retention > 0 else 0

# ----------------------------
# Section 6: Affichage des résultats
# ----------------------------

st.subheader("📈 Comparaison Baseline vs Scénario")

col_metric1, col_metric2, col_metric3 = st.columns(3)

with col_metric1:
    st.metric(
        "Chiffre d'affaires (£)",
        f"{scenario_ca:,.2f}",
        f"{delta_ca:+,.2f} ({delta_ca_pct:+.1f}%)",
        help=f"Baseline: £{baseline_ca:,.2f}"
    )

with col_metric2:
    st.metric(
        "CLV moyen (£)",
        f"{clv_scenario:,.2f}",
        f"{delta_clv:+,.2f} ({delta_clv_pct:+.1f}%)",
        help=f"Baseline: £{clv_baseline:,.2f}"
    )

with col_metric3:
    st.metric(
        "Taux de rétention",
        f"{scenario_retention:.2%}",
        f"{delta_retention:+.2%} ({delta_retention_pct:+.1f}%)",
        help=f"Baseline: {baseline_retention:.2%}"
    )

# ----------------------------
# Section 7: Visualisations
# ----------------------------

st.subheader("📊 Visualisation des impacts")

# Graphique 1: Comparaison CA
col_viz1, col_viz2 = st.columns(2)

with col_viz1:
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    categories = ['Baseline', 'Scénario']
    values = [baseline_ca, scenario_ca]
    colors = ['#1f77b4', '#ff7f0e' if delta_ca >= 0 else '#d62728']
    ax1.bar(categories, values, color=colors)
    ax1.set_ylabel("CA (£)")
    ax1.set_title("Comparaison du Chiffre d'affaires")
    ax1.ticklabel_format(style='plain', axis='y')
    for i, v in enumerate(values):
        ax1.text(i, v, f'£{v:,.0f}', ha='center', va='bottom')
    st.pyplot(fig1)

with col_viz2:
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    values_clv = [clv_baseline, clv_scenario]
    colors_clv = ['#1f77b4', '#ff7f0e' if delta_clv >= 0 else '#d62728']
    ax2.bar(categories, values_clv, color=colors_clv)
    ax2.set_ylabel("CLV (£)")
    ax2.set_title("Comparaison de la CLV moyenne")
    for i, v in enumerate(values_clv):
        ax2.text(i, v, f'£{v:,.0f}', ha='center', va='bottom')
    st.pyplot(fig2)

# Graphique 2: Waterfall des impacts
st.subheader("🌊 Analyse en cascade des impacts")

fig3, ax3 = plt.subplots(figsize=(12, 5))

impacts = {
    'CA Baseline': baseline_ca,
    'Impact Marge': baseline_ca * (scenario_marge_multiplier - 1),
    'Impact Remise': baseline_ca * scenario_marge_multiplier * (
                remise_multiplier - 1) if application_remise == "Globale" else (scenario_ca / remise_multiplier) * (
                remise_multiplier - 1),
    'Impact Rétention': scenario_ca - baseline_ca - baseline_ca * (scenario_marge_multiplier - 1),
    'CA Scénario': scenario_ca
}

x_pos = np.arange(len(impacts))
colors_waterfall = ['#1f77b4', '#2ca02c' if impacts['Impact Marge'] >= 0 else '#d62728',
                    '#d62728', '#2ca02c' if impacts['Impact Rétention'] >= 0 else '#d62728',
                    '#ff7f0e' if delta_ca >= 0 else '#d62728']

ax3.bar(x_pos, list(impacts.values()), color=colors_waterfall)
ax3.set_xticks(x_pos)
ax3.set_xticklabels(list(impacts.keys()), rotation=15, ha='right')
ax3.set_ylabel("Montant (£)")
ax3.set_title("Décomposition des impacts sur le CA")
ax3.ticklabel_format(style='plain', axis='y')
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

for i, (k, v) in enumerate(impacts.items()):
    ax3.text(i, v, f'£{v:,.0f}', ha='center', va='bottom' if v >= 0 else 'top', fontsize=9)

st.pyplot(fig3)

# ----------------------------
# Section 8: Tableau récapitulatif
# ----------------------------

st.subheader("📋 Tableau récapitulatif")

recap_data = {
    'Métrique': ['Chiffre d\'affaires (£)', 'CLV moyen (£)', 'Taux de rétention (%)',
                 'Nombre de clients', 'CA par client (£)'],
    'Baseline': [f"{baseline_ca:,.2f}", f"{clv_baseline:,.2f}", f"{baseline_retention * 100:.2f}",
                 f"{baseline_nb_clients}", f"{revenue_per_client_baseline:,.2f}"],
    'Scénario': [f"{scenario_ca:,.2f}", f"{clv_scenario:,.2f}", f"{scenario_retention * 100:.2f}",
                 f"{baseline_nb_clients}", f"{revenue_per_client_scenario:,.2f}"],
    'Delta (£ ou %)': [f"{delta_ca:+,.2f} ({delta_ca_pct:+.1f}%)",
                       f"{delta_clv:+,.2f} ({delta_clv_pct:+.1f}%)",
                       f"{delta_retention * 100:+.2f} ({delta_retention_pct:+.1f}%)",
                       "0 (0.0%)",
                       f"{revenue_per_client_scenario - revenue_per_client_baseline:+,.2f}"]
}

df_recap = pd.DataFrame(recap_data)
st.dataframe(df_recap, use_container_width=True)
