import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from utils import session_setup

# Récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

# =============================================================================
# HERO SECTION
# =============================================================================
st.markdown("""
<div style='text-align: center; padding: 40px 0 20px 0;'>
    <h1 style='font-size: 3.5em; margin-bottom: 0; color: #1f77b4;'>🛍️ Online Retail Analytics</h1>
    <p style='font-size: 1.5em; color: #666; margin-top: 10px;'>Pilotez vos décisions marketing avec data & intelligence</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# METRICS DASHBOARD - HERO NUMBERS
# =============================================================================
st.markdown("<h2 style='text-align: center; color: #333;'>📊 Vos chiffres en temps réel</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    n_clients = df_filtered['Customer ID'].nunique()
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 15px; text-align: center; color: white;'>
        <h1 style='margin: 0; font-size: 2.5em;'>{n_clients:,}</h1>
        <p style='margin: 5px 0 0 0; font-size: 1.1em;'>Clients Actifs</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    ca_total = df_clients_filtered['Revenue'].sum()
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 30px; border-radius: 15px; text-align: center; color: white;'>
        <h1 style='margin: 0; font-size: 2.5em;'>£{ca_total / 1e6:.1f}M</h1>
        <p style='margin: 5px 0 0 0; font-size: 1.1em;'>Chiffre d'Affaires</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    n_transactions = len(df_filtered)
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                padding: 30px; border-radius: 15px; text-align: center; color: white;'>
        <h1 style='margin: 0; font-size: 2.5em;'>{n_transactions / 1000:.0f}K</h1>
        <p style='margin: 5px 0 0 0; font-size: 1.1em;'>Transactions</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    panier_moyen = df_clients_filtered.groupby('Invoice')['Revenue'].sum().mean()
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                padding: 30px; border-radius: 15px; text-align: center; color: white;'>
        <h1 style='margin: 0; font-size: 2.5em;'>£{panier_moyen:.0f}</h1>
        <p style='margin: 5px 0 0 0; font-size: 1.1em;'>Panier Moyen</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# =============================================================================
# QUICK INSIGHTS - 3 GRAPHIQUES CÔTE À CÔTE
# =============================================================================
st.markdown("<h2 style='text-align: center; color: #333;'>📈 Insights Clés</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

insight_col1, insight_col2, insight_col3 = st.columns(3)

# Graph 1 : Évolution du CA mensuel
with insight_col1:
    st.markdown("<h4 style='text-align: center;'>💰 Tendance CA Mensuel</h4>", unsafe_allow_html=True)
    df_monthly = df_clients_filtered.copy()
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
    st.markdown("<h4 style='text-align: center;'>🌍 Top 5 Pays</h4>", unsafe_allow_html=True)
    top_countries = df_clients_filtered.groupby('Country')['Revenue'].sum().nlargest(5)

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
    st.markdown("<h4 style='text-align: center;'>📅 Activité Hebdomadaire</h4>", unsafe_allow_html=True)
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

# =============================================================================
# CALL TO ACTION CARDS
# =============================================================================
st.markdown("<h2 style='text-align: center; color: #333;'>🚀 Où voulez-vous aller ?</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

cta_col1, cta_col2, cta_col3 = st.columns(3)

with cta_col1:
    st.markdown("""
    <div style='background: white; border-left: 5px solid #667eea; padding: 25px; 
                border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 280px;'>
        <h3 style='color: #667eea; margin-top: 0;'>📊 Analyser</h3>
        <p style='color: #555; line-height: 1.6;'>
            Explorez vos <strong>KPIs</strong>, analysez la <strong>rétention par cohortes</strong> 
            et découvrez vos <strong>segments RFM</strong> les plus performants.
        </p>
        <p style='color: #888; font-size: 0.9em; margin-top: 20px;'>
            → Accédez aux Reports dans le menu
        </p>
    </div>
    """, unsafe_allow_html=True)

with cta_col2:
    st.markdown("""
    <div style='background: white; border-left: 5px solid #f5576c; padding: 25px; 
                border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 280px;'>
        <h3 style='color: #f5576c; margin-top: 0;'>🔮 Simuler</h3>
        <p style='color: #555; line-height: 1.6;'>
            Testez l'impact de vos décisions : <strong>remises</strong>, 
            <strong>variations de marge</strong>, <strong>gains de rétention</strong>. 
            Visualisez les résultats instantanément.
        </p>
        <p style='color: #888; font-size: 0.9em; margin-top: 20px;'>
            → Utilisez les Scénarios
        </p>
    </div>
    """, unsafe_allow_html=True)

with cta_col3:
    st.markdown("""
    <div style='background: white; border-left: 5px solid #43e97b; padding: 25px; 
                border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 280px;'>
        <h3 style='color: #43e97b; margin-top: 0;'>📋 Agir</h3>
        <p style='color: #555; line-height: 1.6;'>
            Exportez vos <strong>listes clients activables</strong>, téléchargez 
            vos <strong>graphiques</strong> et passez du constat à l'action.
        </p>
        <p style='color: #888; font-size: 0.9em; margin-top: 20px;'>
            → Créez votre Plan d'action
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# =============================================================================
# FEATURED PRODUCT
# =============================================================================
st.markdown("<h2 style='text-align: center; color: #333;'>🏆 Produit Star du Moment</h2>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

prod = df_clients_filtered.groupby(['StockCode', 'Description']).agg({
    'Revenue': 'sum',
    'Quantity': 'sum'
}).sort_values('Revenue', ascending=False).reset_index()

top_product = prod.iloc[0]

feat_col1, feat_col2 = st.columns([1, 2])

with feat_col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%); 
                padding: 40px; border-radius: 15px; text-align: center; color: white;'>
        <h1 style='font-size: 3em; margin: 0;'>🥇</h1>
        <h3 style='margin: 20px 0 10px 0;'>{top_product['Description'][:30]}...</h3>
        <p style='font-size: 0.9em; opacity: 0.9;'>Code: {top_product['StockCode']}</p>
        <h2 style='margin: 20px 0 0 0;'>£{top_product['Revenue']:,.0f}</h2>
        <p style='font-size: 0.9em; opacity: 0.9;'>de chiffre d'affaires</p>
    </div>
    """, unsafe_allow_html=True)

with feat_col2:
    st.markdown("<h4>🔥 Top 8 Produits par CA</h4>", unsafe_allow_html=True)
    top_8 = prod.head(8)

    fig4, ax4 = plt.subplots(figsize=(10, 5))
    colors_gradient = plt.cm.viridis(range(len(top_8)))
    bars = ax4.barh(range(len(top_8)), top_8['Revenue'].values, color=colors_gradient)
    ax4.set_yticks(range(len(top_8)))
    ax4.set_yticklabels([desc[:45] + '...' if len(desc) > 45 else desc
                         for desc in top_8['Description'].values], fontsize=10)
    ax4.set_xlabel('Chiffre d\'Affaires (£)', fontsize=11)
    ax4.invert_yaxis()
    ax4.grid(axis='x', alpha=0.3, linestyle='--')

    # Ajouter les valeurs sur les barres
    for i, (bar, value) in enumerate(zip(bars, top_8['Revenue'].values)):
        ax4.text(value, i, f'  £{value:,.0f}', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    st.pyplot(fig4)

st.markdown("<br><br>", unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; border-radius: 15px; text-align: center; color: white; margin-top: 50px;'>
    <h3 style='margin-top: 0;'>Prêt à optimiser votre stratégie marketing ?</h3>
    <p style='font-size: 1.1em; opacity: 0.95;'>
        Utilisez la barre latérale ⬅️ pour filtrer vos données et explorer les différentes sections
    </p>
    <p style='font-size: 0.9em; opacity: 0.8; margin-top: 20px;'>
        Online Retail Analytics Dashboard | Données 2009-2011 | UCI Dataset
    </p>
</div>
""", unsafe_allow_html=True)

