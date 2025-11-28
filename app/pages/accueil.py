import streamlit as st
from utils import session_setup, definitions_pages

# Récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

accueil, kpis, cohortes, rfm, scenarios, plan_action = definitions_pages()

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
    st.subheader("📊 Analyser")
    st.write(
        "Explorez vos **KPIs**, analysez la **rétention par cohortes** "
        "et découvrez vos **segments RFM** les plus performants."
    )
    if st.button("→ Accéder aux KPIs", key="btn_kpis"):
        st.switch_page(kpis)
    if st.button("→ Accéder aux Cohortes", key="btn_cohortes"):
        st.switch_page(cohortes)
    if st.button("→ Accéder aux Segments RFM", key="btn_segments"):
        st.switch_page(rfm)

with col2:
    st.subheader("🛠️ Simuler")
    st.write(
        "Testez l'impact de vos décisions : **remises**, **variations de marge**, "
        "**gains de rétention**. Visualisez les résultats instantanément."
    )
    if st.button("→ Utilisez les Scénarios", key="btn_scenarios"):
        st.switch_page(scenarios)

with col3:
    st.subheader("📋 Agir")
    st.write(
        "Exportez vos **listes clients activables**, téléchargez vos **graphiques** " 
        "et passez du constat à l'action."
    )
    if st.button("→ Créez votre Plan d'action", key="btn_plan"):
        st.switch_page(plan_action)

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

