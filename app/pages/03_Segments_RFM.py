import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import session_setup, download_chart
import io

st.title("Segments RFM - Priorisation")

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

# Afficher les filtres actifs
st.info(
    f"**Filtres actifs :**\n"
    f"- **Période :** {st.session_state.get('date_range', ['N/A'])[0]} → {st.session_state.get('date_range', ['N/A'])[1]}\n"
    f"- **Pays :** {', '.join(st.session_state.get('countries', ['Tous']))}\n"
    f"- **Retours :** {'Inclus' if st.session_state.get('include_returns', True) else '❌ Exclus'}"
)



# --- Page RFM ---
snapshot_date = df_clients_filtered["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df_clients_filtered.groupby("Customer ID").agg({
    "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
    "Invoice": "count",
    "Revenue": "sum"
}).reset_index()

rfm.columns = ["CustomerID","Recency","Frequency","Monetary"]

# --- Scores ---
rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1], duplicates='drop')
rfm['F_Score'] = pd.qcut(rfm['Frequency'], 5, labels=[1,2,3,4,5], duplicates='drop')
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5], duplicates='drop')

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
        "En perte d'activité, à relancer",
        "Inactifs et faible contribution"
    ]
})

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

# --- Ajouter Volume (total articles achetés par client) ---
volume_df = df_clients_filtered.groupby("Customer ID")["Quantity"].sum().reset_index()
volume_df.rename(columns={"Quantity": "Volume"}, inplace=True)
rfm = rfm.merge(volume_df, left_on="CustomerID", right_on="Customer ID", how="left")
rfm.drop(columns=["Customer ID"], inplace=True)

# --- Ajouter Marge (Revenue - Cost) si tu as une colonne Cost ---
if "Cost" in df_clients_filtered.columns:
    df_clients_filtered["Margin"] = df_clients_filtered["Revenue"] - df_clients_filtered["Cost"]
    margin_df = df_clients_filtered.groupby("Customer ID")["Margin"].sum().reset_index()
    rfm = rfm.merge(margin_df, left_on="CustomerID", right_on="Customer ID", how="left")
    rfm.drop(columns=["Customer ID"], inplace=True)
else:
    rfm["Margin"] = rfm["Monetary"]

# --- Graphiques avec téléchargement ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Marge totale par segment")
    margin_segment = rfm.groupby("Segment")["Margin"].sum()
    fig_margin, ax_margin = plt.subplots(figsize=(5,5))
    fig_margin.patch.set_facecolor('none')
    ax_margin.set_facecolor('none')
    ax_margin.pie(
        margin_segment,
        labels=margin_segment.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=plt.cm.Pastel1.colors[:len(margin_segment)]
    )
    ax_margin.set_title("Marge totale par segment")
    st.pyplot(fig_margin)

with col2:
    st.subheader("Distribution des segments")
    fig_dist, ax_dist = plt.subplots(figsize=(5,5))
    fig_dist.patch.set_facecolor('none')
    ax_dist.set_facecolor('none')
    rfm_filtered["Segment"].value_counts().plot(kind="bar", color="darkred", ax=ax_dist)
    ax_dist.set_ylabel("Nombre de clients")
    ax_dist.set_xlabel("")
    ax_dist.set_title("Distribution des segments RFM")
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig_dist)

# Boutons de téléchargement au même niveau
col1_btn, col2_btn = st.columns(2)

with col1_btn:
    download_chart(fig_margin, "marge_par_segment.png")

with col2_btn:
    download_chart(fig_dist, "distribution_segments.png")

# --- Volume total par segment (graphique en aires) ---
st.subheader("Volume total d'articles par segment")
volume_segment = rfm.groupby("Segment")["Volume"].sum().sort_values(ascending=False)
fig_volume, ax_volume = plt.subplots(figsize=(7,3.5))
fig_volume.patch.set_facecolor('none')
ax_volume.set_facecolor('none')
ax_volume.fill_between(range(len(volume_segment)), volume_segment.values, color="plum", alpha=0.6)
ax_volume.plot(range(len(volume_segment)), volume_segment.values, color="purple", marker="o")
ax_volume.set_xticks(range(len(volume_segment)))
ax_volume.set_xticklabels(volume_segment.index, rotation=45, ha='right')
ax_volume.set_ylabel("Volume total")
ax_volume.set_xlabel("")
ax_volume.set_title("Volume total par segment")
ax_volume.grid(True, alpha=0.3)
st.pyplot(fig_volume)

# Téléchargement
download_chart(fig_volume, "volume_par_segment.png")

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
segment_metrics = df_clients_filtered.groupby("Customer ID").agg({
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
st.subheader("Priorités d'activation CRM")
st.markdown("""
### Priorités recommandées

- **Champion** → Fidélisation + early-access + VIP  
- **Fidèle** → Récompenses + programme de points  
- **À potentiel** → Promotions ciblées  
- **À réactiver** → Emails de relance + codes de réduction  
- **Perdu** → Campagnes agressives (peu de ROI attendu)
""")

# --- AVANTAGES ---
st.markdown("---")
st.subheader("💡 Avantages de la segmentation RFM")

col_av1, col_av2, col_av3 = st.columns(3)

with col_av1:
    st.markdown("""
    **🎯 Ciblage précis**
    - Actions marketing personnalisées
    - Budget optimisé par segment
    - Meilleur ROI des campagnes
    """)

with col_av2:
    st.markdown("""
    **📈 Augmentation des ventes**
    - Réactivation des clients inactifs
    - Fidélisation des meilleurs clients
    - Développement du panier moyen
    """)

with col_av3:
    st.markdown("""
    **🔍 Vision stratégique**
    - Identification rapide des priorités
    - Suivi de l'évolution des segments
    - Aide à la décision CRM
    """)

st.markdown("---")

# --- Export ---
if st.button("📥 Exporter CSV"):
    rfm_filtered.to_csv("export_rfm_segments.csv", index=False)
    st.success("✅ Exporté : export_rfm_segments.csv")