import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
import altair as alt
import io
import matplotlib.pyplot as plt
from utils import session_setup


st.set_page_config(page_title="Bienvenue sur la page des KPI !", layout="wide", page_icon="")

df, df_clients, df_filtered, df_clients_filtered = session_setup()

def apply_return_mode(df, mode):
    df = df.copy()
    if mode == 'inclure':
        return df
    if mode == 'exclure':
        return df[df['Quantity'] >= 0]
    if mode == 'neutraliser':
        df.loc[df['Quantity'] < 0, 'Revenue'] = 0
        return df
    return df

def compute_basic_kpis(df_filtered):
    clients_uniques = df_filtered['Customer ID'].dropna().nunique()
    factures = df_filtered['Invoice'].nunique()
    ca_total = df_filtered['Revenue'].sum()
    lignes = df_filtered.shape[0]
    return {
        'clients_actifs': clients_uniques,
        'factures': factures,
        'ca_total': ca_total,
        'lignes': lignes
    }

def clv_baseline_90d(df_filtered):
    df = df_filtered.copy()
    df = df.dropna(subset=['Customer ID'])
    if df.empty:
        return {'clv_90d_mean': 0.0, 'n_new': 0}
    
    first = df.groupby('Customer ID')['InvoiceDate'].min().rename('first_purchase')
    df = df.join(first, on='Customer ID')
    df['days_since_first'] = (df['InvoiceDate'] - df['first_purchase']).dt.days
    df_90 = df[(df['days_since_first'] >= 0) & (df['days_since_first'] <= 90)]
    
    ca_per_client = df_90.groupby('Customer ID')['Revenue'].sum()
    n_new = ca_per_client.shape[0]
    mean_clv = ca_per_client.mean() if n_new > 0 else 0.0
    median_clv = ca_per_client.median() if n_new > 0 else 0.0
    return {'clv_90d_mean': mean_clv, 'clv_90d_median': median_clv, 'n_new': n_new}

def compute_rfm(df_filtered, today=None):
    df = df_filtered.copy()
    df = df.dropna(subset=['Customer ID'])
    if df.empty:
        return pd.DataFrame(columns=['Customer ID', 'recency', 'frequency', 'monetary', 'r_score', 'f_score', 'm_score', 'rfm_score'])
    
    if today is None:
        today = df['InvoiceDate'].max() + pd.Timedelta(days=1)
    
    agg = df.groupby('Customer ID').agg({
        'InvoiceDate': lambda x: (today - x.max()).days,
        'Invoice': 'nunique',
        'Revenue': 'sum'
    }).rename(columns={'InvoiceDate': 'recency', 'Invoice': 'frequency', 'Revenue': 'monetary'}).reset_index()
    
    for col, score_name, asc in [('recency','r_score', True), ('frequency','f_score', False), ('monetary','m_score', False)]:
        try:
            if asc:
                agg[score_name] = pd.qcut(agg[col], q=5, labels=[5,4,3,2,1], duplicates='drop').astype(int)
            else:
                agg[score_name] = pd.qcut(agg[col], q=5, labels=[1,2,3,4,5], duplicates='drop').astype(int)
        except Exception:
            agg[score_name] = pd.cut(agg[col].rank(method='first'), bins=5, labels=[1,2,3,4,5]).astype(int)
    
    agg['rfm_score'] = agg['r_score'].astype(str) + agg['f_score'].astype(str) + agg['m_score'].astype(str)
    return agg.sort_values('monetary', ascending=False)

def rfm_segment_label(rfm_code):
    if pd.isna(rfm_code):
        return "Inconnu"
    r, f, m = rfm_code[0], rfm_code[1], rfm_code[2]
    if r=='5' and f=='5' and m=='5':
        return "Champion"
    if f in ['4','5'] and m in ['4','5']:
        return "Fidèles"
    if r in ['1','2'] and f in ['1','2']:
        return "À risque"
    return "Autres"


st.markdown("""


<style>
/* Fond de toute la page */
    body {
        background-color: #f5f5f5;  /* gris clair */
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }

    .metric-value {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
}

    
    .metric-card-secondary {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }
    
    .metric-card-success {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }
    
    .metric-card-warning {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }
    
    .metric-card-info {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }
    
    .metric-card-ca {
        background: linear-gradient(135deg, #fdbb2d 0%, #22c1c3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: none;
    }
    
    .metric-value {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .metric-label {
        font-size: 0.9rem !important;
        opacity: 0.9;
        margin-bottom: 0.5rem !important;
    }
    
    .progress-container {
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
        height: 8px;
        margin-top: 0.5rem;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 10px;
        background: white;
    }
    
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
    }
    
    .info-icon {
        display: inline-block;
        margin-left: 8px;
        cursor: pointer;
        color: rgba(255,255,255,0.8);
    }
    
    .kpi-help {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)


df_raw = df


with st.sidebar:
    st.markdown("###  Filtres Globaux")
    min_date = df_raw['InvoiceDate'].min().date()
    max_date = df_raw['InvoiceDate'].max().date()
    
    date_range = st.date_input(" Période d'analyse", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    country_opt = st.multiselect(" Pays", options=sorted(df_raw['Country'].unique()), default=[])
    mode_returns = st.radio(" Mode retours", options=["inclure", "exclure", "neutraliser"], index=1, 
                           format_func=lambda x: {"inclure":"Inclure les retours","exclure":"Exclure les retours","neutraliser":"Neutraliser l'impact"}[x])
    
    st.markdown("---")
    if st.button(" Réinitialiser filtres"):
        st.experimental_rerun()

# Appliquer filtres
start_date, end_date = date_range
df_filtered = df_raw[(df_raw['InvoiceDate'].dt.date >= start_date) & (df_raw['InvoiceDate'].dt.date <= end_date)]
if country_opt:
    df_filtered = df_filtered[df_filtered['Country'].isin(country_opt)]

df_filtered = apply_return_mode(df_filtered, mode_returns)

col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown("<h1 style='text-align: center;'></h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='margin-bottom: 0;'> Bienvenue sur la page des KPI ! </h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; margin-top: 0;'>Analyse des performances clients et revenue</p>", unsafe_allow_html=True)

# Calcul impact retours
if mode_returns in ['exclure', 'neutraliser']:
    total_ca_raw = df_raw['Revenue'].sum()
    lost_revenue = df_raw[df_raw['Quantity'] < 0]['Revenue'].sum()
    impact_retours_pct = (lost_revenue / total_ca_raw * 100) if total_ca_raw > 0 else 0
else:
    impact_retours_pct = 0


kpis = compute_basic_kpis(df_filtered)
clv_info = clv_baseline_90d(df_filtered)
rfm_df = compute_rfm(df_filtered)

# Calcul North Star
north_star = kpis['ca_total'] / (kpis['clients_actifs'] if kpis['clients_actifs']>0 else 1)

# Calcul CA par âge de cohorte (0-30 jours)
df_for_age = df_filtered.dropna(subset=['Customer ID']).copy()
if not df_for_age.empty:
    df_for_age['first_purchase'] = df_for_age.groupby('Customer ID')['InvoiceDate'].transform('min')
    df_for_age['age_days'] = (df_for_age['InvoiceDate'] - df_for_age['first_purchase']).dt.days
    df_age_0_30 = df_for_age[(df_for_age['age_days'] >= 0) & (df_for_age['age_days'] <= 30)]
    ca_cohort_0_30 = df_age_0_30['Revenue'].mean() if not df_age_0_30.empty else 0
else:
    ca_cohort_0_30 = 0


if not rfm_df.empty:
    rfm_df['segment_label'] = rfm_df['rfm_score'].apply(rfm_segment_label)
    champion_count = rfm_df[rfm_df['segment_label'] == 'Champion'].shape[0]
else:
    champion_count = 0



# Calcul période précédente
prev_start = start_date - (end_date - start_date) - timedelta(days=1)
prev_end = start_date - timedelta(days=1)
df_prev = df_raw[(df_raw['InvoiceDate'].dt.date >= prev_start) & (df_raw['InvoiceDate'].dt.date <= prev_end)]
if country_opt:
    df_prev = df_prev[df_prev['Country'].isin(country_opt)]
df_prev = apply_return_mode(df_prev, mode_returns)

# KPI période précédente
kpis_prev = compute_basic_kpis(df_prev)
clv_prev = clv_baseline_90d(df_prev)
north_star_prev = kpis_prev['ca_total'] / (kpis_prev['clients_actifs'] if kpis_prev['clients_actifs']>0 else 1)

# Calcul delta %
def calc_delta(current, previous):
    if previous == 0:
        return 0
    return (current - previous) / previous * 100

def compute_m3_retention(df):
    """
    Calcule la rétention M+3 pour chaque cohorte de clients.
    df doit contenir : Customer ID, InvoiceDate
    """
    df = df.dropna(subset=['Customer ID']).copy()
    if df.empty:
        return pd.DataFrame()

    # Définir le mois de première commande pour chaque client
    df['cohort_month'] = df.groupby('Customer ID')['InvoiceDate'].transform('min').dt.to_period('M').dt.to_timestamp()
    df['purchase_month'] = df['InvoiceDate'].dt.to_period('M').dt.to_timestamp()

    # Taille de la cohorte
    cohort_sizes = df.groupby('cohort_month')['Customer ID'].nunique().rename('cohort_size')

    # Calcul M+3
    retention_records = []
    for cohort, size in cohort_sizes.items():
        cohort_df = df[df['cohort_month'] == cohort]
        month_3 = cohort + pd.DateOffset(months=3)
        retained = cohort_df[cohort_df['purchase_month'] == month_3]['Customer ID'].nunique()
        retention_pct = (retained / size * 100) if size > 0 else 0
        retention_records.append({'cohort_month': cohort, 'M+3_retention_pct': retention_pct})

    return pd.DataFrame(retention_records)

df_retention = compute_m3_retention(df_filtered)



st.markdown("---")

st.markdown("###  Métriques Clés")

# Première ligne - 3 colonnes
col1, col2, col3 = st.columns(3)

with col1:
    # Clients Actifs
    st.markdown("""
    <div class='metric-card' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             Clients Actifs 
            <span class='info-icon' title=' '></span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>{:,}</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: 85%'></div>
        </div>
    </div>
    """.format(kpis['clients_actifs']), unsafe_allow_html=True)
    
    with st.expander(" Définition - Clients Actifs", expanded=False):
        st.markdown("""
        **Définition:** Nombre de clients uniques ayant effectué au moins une commande dans la période sélectionnée.
        **Utilité:** Suivre la taille de votre base client engagée
        """)

with col2:
    # CA Total
    ca_clients = df_filtered['Customer ID'].dropna().nunique()
    ca_delta = calc_delta(kpis['ca_total'], kpis_prev['ca_total'])
    
    st.markdown(f"""
    <div class='metric-card-ca' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             Chiffre d'Affaires
            <span class='info-icon' title=' '> </span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>£{kpis['ca_total']:,.0f}</div>
        <div style='font-size:0.8rem; color:#000000 !important;'>Clients inclus: {ca_clients:,}</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: 75%'></div>
        </div>
        <div style='font-size:0.8rem; color:#000000 !important; margin-top:0.3rem;'>{ca_delta:+.1f}% vs période précédente</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(" Définition - Chiffre d'Affaires", expanded=False):
        st.markdown("""
        **Définition:** Somme totale des revenus générés par les ventes.
        **Utilité:** Mesurer la performance commerciale globale
        """)

with col3:
    # CLV Baseline
    clv_clients = clv_info['n_new']
    clv_delta = calc_delta(clv_info['clv_90d_mean'], clv_prev['clv_90d_mean'])
    
    st.markdown(f"""
    <div class='metric-card-secondary' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             CLV Baseline
            <span class='info-icon' title=' '> </span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>£{clv_info['clv_90d_mean']:,.0f}</div>
        <div style='font-size:0.8rem; color:#000000 !important;'>Nouveaux clients: {clv_clients:,}</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: 68%'></div>
        </div>
        <div style='font-size:0.8rem; color:#000000 !important; margin-top:0.3rem;'>{clv_delta:+.1f}% vs période précédente</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(" Définition - CLV Baseline", expanded=False):
        st.markdown("""
        **Définition:** CA moyen généré par un nouveau client durant ses 90 premiers jours.
        **Utilité:** Estimer la valeur d'acquisition client à court terme
        """)

# Deuxième ligne - 3 colonnes  
col4, col5, col6 = st.columns(3)

with col4:
    # North Star
    ns_clients = kpis['clients_actifs']
    ns_delta = calc_delta(north_star, north_star_prev)
    
    st.markdown(f"""
    <div class='metric-card-success' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             North Star
            <span class='info-icon' title=' '> </span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>£{north_star:,.0f}</div>
        <div style='font-size:0.8rem; color:#000000 !important;'>Clients inclus: {ns_clients:,}</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: 78%'></div>
        </div>
        <div style='font-size:0.8rem; color:#000000 !important; margin-top:0.3rem;'>{ns_delta:+.1f}% vs période précédente</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(" Définition - North Star", expanded=False):
        st.markdown("""
        **Définition:** CA moyen par client actif.
        **Utilité:** Indicateur global de performance et de valeur client
        """)

with col5:
    # CA / Âge Cohorte
    st.markdown("""
    <div class='metric-card-warning' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             CA / Âge Cohorte 
            <span class='info-icon' title=' '> </span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>£{:,.0f}</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: 65%'></div>
        </div>
    </div>
    """.format(ca_cohort_0_30), unsafe_allow_html=True)
    
    with st.expander(" Définition - CA / Âge Cohorte", expanded=False):
        st.markdown("""
        **Définition:** CA moyen des clients dans leurs 30 premiers jours.
        **Utilité:** Comprendre la valeur immédiate des nouveaux clients
        """)

with col6:
    # Segments RFM
    st.markdown("""
    <div class='metric-card-info' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             Segments RFM 
            <span class='info-icon' title=' '> </span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>{:,}</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: 72%'></div>
        </div>
    </div>
    """.format(champion_count), unsafe_allow_html=True)
    
    with st.expander(" Définition - Segments RFM", expanded=False):
        st.markdown("""
        **Définition:** Nombre de clients dans le segment RFM "Champion".
        **Utilité:** Identifier et fidéliser vos meilleurs clients
        """)

# Troisième ligne - 3 colonnes (dernière métrique centrée)
col7, col8, col9 = st.columns(3)

with col8:  # Centrer l'impact retours au milieu
    # Impact Retours
    st.markdown(f"""
    <div class='metric-card-warning' style='height: 200px; display: flex; flex-direction: column; justify-content: center;'>
        <div class='metric-label'>
             Impact Retours
            <span class='info-icon' title=' '> </span>
        </div>
        <div class='metric-value' style='color: #000000 !important;'>{impact_retours_pct:.1f}%</div>
        <div class='progress-container'>
            <div class='progress-bar' style='width: {min(impact_retours_pct,100)}%'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(" Définition - Impact des Retours", expanded=False):
        st.markdown("""
        **Définition:** Part du CA perdu à cause des retours.
        **Utilité:** Mesurer l'impact des retours sur la performance
        """)


st.markdown("---")
st.markdown("<h2 style='text-align: center; color: #333;'> Insights Clés</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

insight_col1, insight_col2, insight_col3 = st.columns(3)

# Graph 1 : Évolution du CA mensuel
with insight_col1:
    st.markdown("<h4 style='text-align: center;'> Tendance CA Mensuel</h4>", unsafe_allow_html=True)
    df_monthly = df_filtered.copy()
    df_monthly['YearMonth'] = df_monthly['InvoiceDate'].dt.to_period('M')
    monthly_revenue = df_monthly.groupby('YearMonth')['Revenue'].sum().reset_index()
    monthly_revenue['YearMonth'] = monthly_revenue['YearMonth'].astype(str)

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(range(len(monthly_revenue)), monthly_revenue['Revenue'],
             linewidth=3, color='#667eea', marker='o', markersize=6)
    ax1.fill_between(range(len(monthly_revenue)), monthly_revenue['Revenue'],
                     alpha=0.3, color='#667eea')
    ax1.set_xlabel('Mois', fontsize=10)
    ax1.set_ylabel('CA (£)', fontsize=10)
    ax1.grid(alpha=0.3, linestyle='--')
    ax1.set_xticks([])
    plt.tight_layout()
    st.pyplot(fig1)

# Graph 2 : Top 5 Pays
with insight_col2:
    st.markdown("<h4 style='text-align: center;'> Top 5 Pays</h4>", unsafe_allow_html=True)
    top_countries = df_filtered.groupby('Country')['Revenue'].sum().nlargest(5)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    colors = ['#f5576c', '#f093fb', '#4facfe', '#43e97b', '#feca57']
    ax2.barh(range(len(top_countries)), top_countries.values, color=colors)
    ax2.set_yticks(range(len(top_countries)))
    ax2.set_yticklabels(top_countries.index, fontsize=10)
    ax2.set_xlabel('CA (£)', fontsize=10)
    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig2)

# Graph 3 : Distribution des transactions par jour de semaine
with insight_col3:
    st.markdown("<h4 style='text-align: center;'> Activité Hebdomadaire</h4>", unsafe_allow_html=True)
    df_weekly = df_filtered.copy()
    df_weekly['DayOfWeek'] = df_weekly['InvoiceDate'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_counts = df_weekly['DayOfWeek'].value_counts().reindex(day_order, fill_value=0)

    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.bar(range(len(weekly_counts)), weekly_counts.values,
            color='#38f9d7', edgecolor='#43e97b', linewidth=2)
    ax3.set_xticks(range(len(weekly_counts)))
    ax3.set_xticklabels(['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'], fontsize=10)
    ax3.set_ylabel('Nb Transactions', fontsize=10)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig3)

st.markdown("<br><br>", unsafe_allow_html=True)


st.markdown("---")
st.markdown("###  Analytics Visuels")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    
    st.markdown("**North Star — Tendance Journalière**")
    
    if not df_filtered.empty:
        daily = df_filtered.groupby(df_filtered['InvoiceDate'].dt.date).agg({
            'Revenue': 'sum',
            'Customer ID': lambda x: x.nunique()
        }).reset_index()
        daily.columns = ['Date', 'ca_daily', 'clients_daily']
        
        daily['northstar'] = daily.apply(
            lambda row: row['ca_daily'] / row['clients_daily'] if row['clients_daily'] > 0 else 0, 
            axis=1
        )
        
        daily_valid = daily[daily['clients_daily'] > 0].copy()
        
        if len(daily_valid) > 0:
            chart = alt.Chart(daily_valid).mark_area(
                opacity=0.6,
                line={'color': '#667eea', 'size': 2}
            ).encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('northstar:Q', title='CA / Client Actif (£)'),
                tooltip=['Date:T', 'northstar:Q']
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("ℹ️ Pas assez de données pour afficher la tendance North Star")
    else:
        st.info("ℹ️ Aucune donnée disponible après filtrage")
    st.markdown("</div>", unsafe_allow_html=True)

with col_chart2:
  
    st.markdown("**Distribution des Segments RFM**")
    
    if not rfm_df.empty:
        rfm_df['segment_label'] = rfm_df['rfm_score'].apply(rfm_segment_label)
        rfm_count = rfm_df.groupby('segment_label').agg(n_clients=('Customer ID','count')).reset_index()
        
        chart = alt.Chart(rfm_count).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="n_clients", type="quantitative"),
            color=alt.Color(field="segment_label", type="nominal", 
                          scale=alt.Scale(range=['#667eea', '#764ba2', '#f093fb', '#f5576c'])),
            tooltip=['segment_label', 'n_clients']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("ℹ️ Pas assez de données pour calculer les segments RFM")
    st.markdown("</div>", unsafe_allow_html=True)



st.markdown("**CA moyen par âge de cohorte (jours)**")

if not df_for_age.empty:
    df_age_agg = df_for_age[df_for_age['age_days'] <= 365].groupby('age_days')['Revenue'].mean().reset_index().rename(columns={'Revenue':'CA_moyen'})
    
    if not df_age_agg.empty:
        chart_age = alt.Chart(df_age_agg).mark_line(point=True, color='#ff9a9e').encode(
            x=alt.X('age_days:Q', title='Âge de cohorte (jours)'),
            y=alt.Y('CA_moyen:Q', title='CA moyen (£)'),
            tooltip=[alt.Tooltip('age_days:Q', title='Age (jours)'), alt.Tooltip('CA_moyen:Q', title='CA moyen (£)')]
        ).properties(height=300)
        st.altair_chart(chart_age, use_container_width=True)
    else:
        st.info("ℹ️ Pas assez de données pour afficher le CA par âge de cohorte")
else:
    st.info("ℹ️ Pas de données clients pour afficher le CA par âge de cohorte")
st.markdown("</div>", unsafe_allow_html=True)


st.markdown("---")
st.markdown("###  Performance par Catégorie")


col_top1, col_top2 = st.columns(2)

with col_top1:
   
    st.markdown("**Top Produits**")
    
    if not df_filtered.empty:
        df_products = df_filtered[df_filtered['Description'].notna() & (df_filtered['Description'] != '')]
        
        if not df_products.empty:
            top_products = df_products.groupby('Description')['Revenue'].sum().nlargest(5).reset_index()
            
            for idx, row in top_products.iterrows():
                product_name = row['Description']
                if len(product_name) > 30:
                    product_name = product_name[:30] + "..."
                
                st.markdown(f"""
                <div style='padding: 0.8rem 0; border-bottom: 1px solid #f0f0f0;'>
                    <div style='font-weight: 600; font-size: 0.9rem; margin-bottom: 0.3rem;'>{product_name}</div>
                    <div style='color: #667eea; font-size: 1rem; font-weight: 700;'>£{row['Revenue']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Aucun produit avec description trouvé")
    else:
        st.info("ℹ️ Aucune donnée disponible")
    st.markdown("</div>", unsafe_allow_html=True)

with col_top2:

    st.markdown("**Performance par Pays**")
    
    if not df_filtered.empty:
        country_perf = df_filtered.groupby('Country')['Revenue'].sum().nlargest(5).reset_index()
        
        if not country_perf.empty:
            total_all_countries = country_perf['Revenue'].sum()
            
            # Dictionnaire des icônes par pays
            country_icons = {
                'United Kingdom': '🇬🇧',
                'EIRE': '🇮🇪',  # Irlande
                'Netherlands': '🇳🇱',
                'Germany': '🇩🇪', 
                'France': '🇫🇷',
                'Spain': '🇪🇸',
                'Switzerland': '🇨🇭',
                'Portugal': '🇵🇹',
                'Belgium': '🇧🇪',
                'Norway': '🇳🇴',
                'Australia': '🇦🇺',
                'Sweden': '🇸🇪',
                'Japan': '🇯🇵',
                'Italy': '🇮🇹',
                'Denmark': '🇩🇰',
                'Finland': '🇫🇮',
                'Austria': '🇦🇹',
                'Israel': '🇮🇱',
                'Poland': '🇵🇱',
                'USA': '🇺🇸',
                'United States': '🇺🇸',
                'Canada': '🇨🇦',
                'Singapore': '🇸🇬',
                'Hong Kong': '🇭🇰',
                'Greece': '🇬🇷',
                'Cyprus': '🇨🇾',
                'Czech Republic': '🇨🇿',
                'Lithuania': '🇱🇹',
                'Brazil': '🇧🇷',
                'Malta': '🇲🇹',
                'Iceland': '🇮🇸'
            }
            
            for idx, row in country_perf.iterrows():
                pct = (row['Revenue'] / total_all_countries * 100) if total_all_countries > 0 else 0
                country_name = row['Country']
                icon = country_icons.get(country_name, '🌐')  # Icône par défaut si pays non trouvé
                
                st.markdown(f"""
                <div style='padding: 0.8rem 0; border-bottom: 1px solid #f0f0f0;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span style='font-weight: 600; font-size: 0.9rem;'>
                            {icon} {country_name}
                        </span>
                        <span style='color: #667eea; font-weight: 700;'>£{row['Revenue']:,.0f}</span>
                    </div>
                    <div style='background: #ecf0f1; height: 6px; border-radius: 3px;'>
                        <div style='background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: {pct}%; border-radius: 3px;'></div>
                    </div>
                    <div style='font-size: 0.7rem; color: #95a5a6; text-align: right; margin-top: 0.2rem;'>{pct:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Aucune donnée par pays")
    else:
        st.info("ℹ️ Aucune donnée disponible")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)
col_bottom = st.columns(1)[0]

with col_bottom:
    st.markdown("**Activité Mensuelle**")
    
    if not df_filtered.empty:
        monthly = df_filtered.groupby(df_filtered['InvoiceDate'].dt.to_period('M').dt.to_timestamp())['Revenue'].sum().reset_index()
        monthly.columns = ['Mois', 'CA']
        
        if not monthly.empty:
            chart = alt.Chart(monthly).mark_bar(
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3,
                color='#f5576c' 
            ).encode(
                x=alt.X('Mois:T', title='Mois', axis=alt.Axis(format='%b %Y')),
                y=alt.Y('CA:Q', title='CA (£)'),
                tooltip=[
                    alt.Tooltip('Mois:T', title='Mois', format='%B %Y'),
                    alt.Tooltip('CA:Q', title='Chiffre d\'Affaires', format='$.0f')
                ]
            ).properties(height=300)  
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("ℹ️ Aucune donnée mensuelle disponible")
    else:
        st.info("ℹ️ Aucune donnée disponible")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("---")
st.markdown("###   Analyse de Cohorte de Rétention")

def compute_cohort_retention(df):
    """
    Calcule la rétention par cohorte mois par mois
    """
    df = df.dropna(subset=['Customer ID']).copy()
    if df.empty:
        return pd.DataFrame()
    
    # Définir la cohorte (mois de première commande)
    df['cohort_month'] = df.groupby('Customer ID')['InvoiceDate'].transform('min').dt.to_period('M')
    df['order_month'] = df['InvoiceDate'].dt.to_period('M')
    
    # Créer la matrice de cohorte
    cohort_data = df.groupby(['cohort_month', 'order_month']).agg({
        'Customer ID': 'nunique'
    }).reset_index()
    
    # Calculer le numéro du mois depuis la cohorte
    cohort_data['period_number'] = (cohort_data['order_month'] - cohort_data['cohort_month']).apply(lambda x: x.n)
    
    # Pivoter pour avoir la matrice
    cohort_pivot = cohort_data.pivot_table(
        index='cohort_month',
        columns='period_number',
        values='Customer ID',
        aggfunc='sum'
    )
    
    # Calculer les pourcentages de rétention
    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100
    
    return retention_matrix.round(1)

# Calculer la matrice de rétention
retention_matrix = compute_cohort_retention(df_filtered)

if not retention_matrix.empty:
    # Afficher la matrice de cohorte
    st.markdown("**Rétention Mensuelle par Cohorte (%)**")
    
    # Préparer les données pour l'affichage
    display_df = retention_matrix.copy()
    display_df.index = display_df.index.astype(str)
    
    # Remplacer les NaN par None pour éviter les problèmes de formatage
    display_df = display_df.where(pd.notnull(display_df), None)
    
    # Créer un heatmap avec Altair
    heatmap_data = display_df.reset_index().melt(
        id_vars='cohort_month', 
        var_name='month_since_cohort', 
        value_name='retention'
    )
    # Filtrer les valeurs None
    heatmap_data = heatmap_data[heatmap_data['retention'].notna()]
    
    if not heatmap_data.empty:
        heatmap = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X('month_since_cohort:O', title='Mois depuis acquisition'),
            y=alt.Y('cohort_month:O', title='Cohorte (Mois)'),
            color=alt.Color('retention:Q', 
                          title='Rétention (%)',
                          scale=alt.Scale(scheme='blues'),
                          legend=alt.Legend(format='.0f')),
            tooltip=[
                alt.Tooltip('cohort_month:O', title='Cohorte'),
                alt.Tooltip('month_since_cohort:O', title='Mois depuis'),
                alt.Tooltip('retention:Q', title='Rétention (%)', format='.1f')
            ]
        ).properties(
            height=400,
            width=600
        )
        
        # Ajouter le texte dans les cases
        text = heatmap.mark_text(baseline='middle').encode(
            text=alt.Text('retention:Q', format='.0f'),
            color=alt.condition(
                alt.datum.retention > 50,
                alt.value('white'),
                alt.value('black')
            )
        )
        
        st.altair_chart(heatmap + text, use_container_width=True)
    else:
        st.info("ℹ️ Pas assez de données pour l'analyse de cohorte")

    with st.expander("Appuyez pour voir le tableau détaillé des rétentions", expanded=False):
        # Créer une copie pour l'affichage avec le symbole %
        display_table = display_df.copy()
        for col in display_table.columns:
            display_table[col] = display_table[col].apply(
                lambda x: f"{x:.1f}%" if x is not None else ""
            )
        
        st.dataframe(display_table, use_container_width=True)
    
    
    st.markdown("**Rétentions :**")
    
  
    insights_data = []
    
    if 1 in retention_matrix.columns:
        m1_retention = retention_matrix[1].mean()
        insights_data.append(f"- **Rétention M+1 :** {m1_retention:.1f}% en moyenne")
    
    if 3 in retention_matrix.columns:
        m3_retention = retention_matrix[3].mean()
        insights_data.append(f"- **Rétention M+3 :** {m3_retention:.1f}% en moyenne")
    
    if 6 in retention_matrix.columns:
        m6_retention = retention_matrix[6].mean()
        insights_data.append(f"- **Rétention M+6 :** {m6_retention:.1f}% en moyenne")
    
    for insight in insights_data:
        st.write(insight)

else:
    st.info("ℹ️ Pas assez de données pour calculer l'analyse de cohorte")



st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p> Dashboard Marketing - Données mises à jour en temps réel</p>
    <p style='font-size: 0.8rem;'>Utilisez les filtres dans la sidebar pour explorer les données</p>
</div>
""", unsafe_allow_html=True)

