import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Segments RFM - Priorisation")

#récupère les data depuis app.py
df = st.session_state["df"]
df_clients = st.session_state["df_clients"]


# --- Page RFM ---
snapshot_date = df_clients["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df_clients.groupby("Customer ID").agg({
    "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
    "Invoice": "count",
    "Revenue": "sum"
}).reset_index()

rfm.columns = ["CustomerID","Recency","Frequency","Monetary"]

# --- Scores ---
rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1])
rfm['F_Score'] = pd.qcut(rfm['Frequency'], 5, labels=[1,2,3,4,5])
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5])

rfm['RFM_Score'] = (
    rfm['R_Score'].astype(str) +
    rfm['F_Score'].astype(str) +
    rfm['M_Score'].astype(str)
)

# --- Labels ---
def rfm_label(row):
    r, f = int(row['R_Score']), int(row['F_Score'])
    if r == 5 and f == 5:
        return "Champion"
    elif r >= 4 and f >= 4:
        return "Fidèle"
    elif r >= 4 and f <= 2:
        return "À réactiver"
    elif r <= 2 and f >= 4:
        return "À potentiel"
    elif r <= 2 and f <= 2:
        return "Perdu"
    return "Autre"

rfm['Segment'] = rfm.apply(rfm_label, axis=1)

# --- EXPLICATION DES SCORES ---
st.subheader("Qu'est ce qu'un score RFM ?")

st.markdown("Le score RFM est une méthode simple pour analyser le comportement de nos clients !")
st.markdown("""
**RFM** = Recency (R) + Frequency (F) + Monetary (M)  
Chaque score va de **1 à 5**.

- **R (Récence)** : 5 = très récent, 1 = ancien  
- **F (Fréquence)** : 5 = très fréquent, 1 = rare  
- **M (Montant)** : 5 = gros panier, 1 = faible panier  

<u>Exemples :</u>  
- **554** → Client récent, très fidèle, gros acheteur  
- **311** → Client ancien, peu fidèle, faible panier
""", unsafe_allow_html=True)

# --- SEGMENTS ---
st.subheader("Classement des segments RFM")

labels_df = pd.DataFrame({
    "Segment": ["Champion", "Fidèle", "À potentiel", "À réactiver", "Perdu"],
    "Description": [
        "Achètent souvent, récemment, gros panier",
        "Clients réguliers et actifs",
        "Peu récents mais gros potentiel",
        "En perte d’activité, à relancer",
        "Inactifs et faible contribution"
    ]
})

# Ajouter un index pour le numéro du segment (1 = Champion, etc.)
labels_df.index = range(1, len(labels_df) + 1)
st.dataframe(labels_df, use_container_width=True)


# --- Filtres ---
segments_list = sorted(rfm["Segment"].unique())
select_segments = st.multiselect(
    "Filtrer par segment RFM",
    options=segments_list,
    default=segments_list
)

rfm_filtered = rfm[rfm["Segment"].isin(select_segments)]

st.markdown(f"### Effectif : {len(rfm_filtered)} clients")

# --- Tableau principal ---
st.subheader("Tableau RFM complet")
st.dataframe(rfm_filtered, use_container_width=True)

# --- Graphique --- 
#st.subheader("Distribution des segments")
#st.bar_chart(rfm_filtered["Segment"].value_counts())
st.subheader("Distribution des segments")
fig, ax = plt.subplots(figsize=(8,4))
rfm_filtered["Segment"].value_counts().plot(kind="bar", color="darkred", ax=ax)
ax.set_ylabel("Nombre de clients")
ax.set_xlabel("Segments")
ax.set_title("Distribution des segments RFM")
st.pyplot(fig)

# --- Top 3 segments par CA ---
st.subheader("Top 3 segments par CA total")
top_segments = (
    rfm.groupby("Segment")["Monetary"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
top_segments.index += 1
st.table(top_segments.head(3))

# --- Metrics segment : CA / Marge / Panier moyen ---
st.subheader("Synthèse par segment")
segment_metrics = df_clients.groupby("Customer ID").agg({
    "Revenue": "sum",
    "Quantity": "sum"
}).reset_index()

segment_metrics.rename(columns={"Customer ID": "CustomerID"}, inplace=True)

rfm_metrics = rfm.merge(segment_metrics, on="CustomerID", how="left")
rfm_metrics = rfm_metrics.groupby("Segment").agg({
    "CustomerID": "count",
    "Monetary": "sum",
    "Quantity": "sum"
})

rfm_metrics["Panier_moyen"] = rfm_metrics["Monetary"] / rfm_metrics["CustomerID"]
st.dataframe(rfm_metrics, use_container_width=True)

# --- Priorités CRM ---
st.subheader("Priorités d’activation CRM")
st.markdown("""
### Priorités recommandées

- **Champion** → Fidélisation + early-access + VIP  
- **Fidèle** → Récompenses + programme de points  
- **À potentiel** → Promotions ciblées  
- **À réactiver** → Emails de relance + codes de réduction  
- **Perdu** → Campagnes agressives (peu de ROI attendu)
""")

# --- Export ---
if st.button("Exporter CSV"):
    rfm_filtered.to_csv("export_rfm_segments.csv", index=False)
    st.success("Exporté : export_rfm_segments.csv")
