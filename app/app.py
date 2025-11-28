import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from utils import load_data

st.set_page_config(page_title="Dashboard Online Retail", layout="wide")
sns.set(style="whitegrid")


# ----------------------------
# LOAD DATA (depuis CSV compressés)
# ----------------------------
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
    '''
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
'''
    st.title("Simulation de scénarios - Paramètres avancés")

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