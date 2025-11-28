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
    <h1 style='font-size: 3.5em; margin-bottom: 0; color: #1f77b4;'> Analyse en ligne personnalisée </h1>
    <p style='font-size: 1.5em; color: #999; margin-top: 10px;'>Pilotez vos décisions marketing avec data & intelligence</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# CALL TO ACTION CARDS
# =============================================================================
col1, col2, col3 = st.columns(3)

with col1:
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

with col2:
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

with col3:
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

