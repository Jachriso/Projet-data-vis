import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from app.utils import session_setup

st.title("Plan d'action")

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

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