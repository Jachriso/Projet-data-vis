import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from utils import session_setup, compute_rfm

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

st.title("Export des données filtrées et graphiques")
st.markdown("Téléchargez ici les données filtrées et les graphiques générés")


rfm = compute_rfm(df_clients_filtered)

# Définition des segments activables
rfm['Segment'] = "Autres"
rfm.loc[(rfm['Recency'] >= 3) & (rfm['Frequency'] >= 3) & (rfm['Monetary'] >= 3), 'Segment'] = "VIP"
rfm.loc[rfm['Recency'] > 90, 'Segment'] = "À réactiver"
rfm.loc[(rfm['Frequency'] == 1) & (rfm['Monetary'] > rfm['Monetary'].median()),
        'Segment'] = "Nouveaux à potentiel"




# ------------------------------------------------------
# 1) Export CSV des données filtrées
# ------------------------------------------------------

st.subheader(" Export CSV des données filtrées")


if "df_filtered" not in st.session_state:
    st.warning(" Aucune donnée filtrée trouvée. Veuillez d’abord valider les filtres.")
else:
    df_clients_filtered = st.session_state["df_filtered"]

    st.write(f"{len(df_clients_filtered):,} lignes filtrées")

    csv = df_clients_filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        " Télécharger CSV filtré",
        data=csv,
        file_name="donnees_clients_filtrees.csv",
        mime="text/csv"
    )

# ------------------------------------------------------
# 2) Export CSV – Liste activable RFM
# ------------------------------------------------------

st.subheader(" Export liste activable (RFM)")

csv_segments = rfm[['Customer ID','Recency','Frequency','Monetary','Segment']]\
                .sort_values("Segment")\
                .to_csv(index=False).encode('utf-8')

st.download_button("Télécharger liste activable (CSV)",
                   data=csv_segments,
                   file_name="activation_list.csv")

