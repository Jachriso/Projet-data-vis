import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import session_setup, download_chart


st.title("Segments RFM - Priorisation")

# récupère les dataframes
df, df_clients, df_filtered, df_clients_filtered = session_setup()

# --- Page RFM ---
snapshot_date = df_clients_filtered["InvoiceDate"].max() + pd.Timedelta(days=1)


@st.cache_data
def compute_rfm(df_clients_filtered):
    snapshot_date = df_clients_filtered["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df_clients_filtered.groupby("Customer ID").agg({
        "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
        "Invoice": "count",
        "Revenue": "sum"
    }).reset_index()

    rfm.columns = ["CustomerID", "Recency", "Frequency", "Monetary"]

    # Scores
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'], 5, labels=[1,2,3,4,5], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5], duplicates='drop')

    rfm['RFM_Score'] = (
        rfm['R_Score'].astype(str) +
        rfm['F_Score'].astype(str) +
        rfm['M_Score'].astype(str)
    )

    # Labels
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

    return rfm

rfm = compute_rfm(df_clients_filtered)


#PRE-CALCUL DES STATISTIQUES PAR SEGMENT
@st.cache_data
def compute_segment_stats(rfm):
    stats = rfm.groupby("Segment").agg(
        nb_clients=("CustomerID", "count"),
        ca_total=("Monetary", "sum"),
        panier_moyen=("Monetary", "mean"),
        recence_moy=("Recency", "mean"),
        frequence_moy=("Frequency", "mean"),
    )
    ca_global = rfm["Monetary"].sum()
    return stats, ca_global

segment_stats, ca_global = compute_segment_stats(rfm)

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

# --- RECOMMANDATIONS INTERACTIVES ---
st.markdown("---")
st.subheader("Recommandations d'actions par segment")

# Sélection du segment pour les recommandations
segment_selected = st.selectbox(
    "Sélectionnez un segment pour voir les recommandations détaillées :",
    options=["Champion", "Fidèle", "À potentiel", "À réactiver", "Perdu", "Autre"]
)

# Dictionnaire des recommandations basées sur RFM
recommendations = {
    "Champion": {
        "priorite": "CRITIQUE",
        "objectif": "Maximiser la rétention et la valeur client",
        "analyse_rfm": "Récence élevée (R=5) + Fréquence élevée (F=5) + Montant élevé (M=4-5)",
        "comportement": "Clients les plus précieux : achètent régulièrement, récemment et dépensent beaucoup",
        "actions": [
            "Mettre en place un programme de fidélité premium avec récompenses exclusives",
            "Proposer un accès anticipé aux nouveaux produits et collections",
            "Personnaliser la communication avec un gestionnaire de compte dédié",
            "Solliciter leur avis pour améliorer l'offre (enquêtes qualitatives)"
        ],
        "budget": "35-45% du budget marketing",
        "roi": "ROI très élevé : 300 à 500%"
    },
    "Fidèle": {
        "priorite": "HAUTE",
        "objectif": "Faire évoluer vers le segment Champion",
        "analyse_rfm": "Récence élevée (R=4-5) + Fréquence élevée (F=4-5) + Montant variable (M=2-4)",
        "comportement": "Clients réguliers et actifs, potentiel d'augmentation du panier moyen",
        "actions": [
            "Mettre en place un système de points pour encourager les achats répétés",
            "Proposer des offres groupées pour augmenter la valeur du panier",
            "Envoyer des recommandations personnalisées basées sur l'historique d'achat",
            "Créer des paliers de fidélité avec avantages progressifs"
        ],
        "budget": "25-30% du budget marketing",
        "roi": "ROI élevé : 200 à 400%"
    },
    "À potentiel": {
        "priorite": "MOYENNE-HAUTE",
        "objectif": "Augmenter la fréquence d'achat",
        "analyse_rfm": "Récence faible (R=1-2) + Fréquence élevée (F=4-5) + Montant élevé (M=4-5)",
        "comportement": "Clients à fort potentiel mais inactifs récemment, risque de perte",
        "actions": [
            "Lancer des campagnes de réactivation ciblées sur leurs catégories favorites",
            "Proposer des promotions limitées dans le temps pour créer l'urgence",
            "Envoyer des rappels personnalisés sur les produits consultés",
            "Offrir des avantages exclusifs pour les inciter à revenir"
        ],
        "budget": "20-25% du budget marketing",
        "roi": "ROI bon : 150 à 300%"
    },
    "À réactiver": {
        "priorite": "MOYENNE",
        "objectif": "Réengager les clients en perte d'activité",
        "analyse_rfm": "Récence élevée (R=4-5) + Fréquence faible (F=1-2) + Montant variable (M=2-4)",
        "comportement": "Clients récents mais peu engagés, besoin de stimulation",
        "actions": [
            "Envoyer des emails de relance avec messages personnalisés",
            "Proposer des codes de réduction significatifs (15-25%) pour motiver le retour",
            "Mettre en avant les nouveautés et best-sellers depuis leur dernier achat",
            "Réaliser une enquête pour comprendre les freins à l'achat répété"
        ],
        "budget": "15-20% du budget marketing",
        "roi": "ROI modéré : 100 à 200%"
    },
    "Perdu": {
        "priorite": "BASSE",
        "objectif": "Récupération sélective ou abandon",
        "analyse_rfm": "Récence très faible (R=1-2) + Fréquence faible (F=1-2) + Montant faible (M=1-2)",
        "comportement": "Clients inactifs depuis longtemps avec faible historique de valeur",
        "actions": [
            "Lancer une campagne de dernière chance avec offre exceptionnelle",
            "Mettre en place du retargeting publicitaire à faible coût",
            "Nettoyer la base de données après période définie (6-12 mois)",
            "Analyser les raisons de départ pour éviter la perte future"
        ],
        "budget": "5-10% du budget marketing",
        "roi": "ROI faible : 50 à 100%"
    },
    "Autre": {
        "priorite": "À ÉVALUER",
        "objectif": "Qualification et orientation stratégique",
        "analyse_rfm": "Scores mixtes ne correspondant pas aux segments principaux",
        "comportement": "Profils atypiques nécessitant une analyse approfondie",
        "actions": [
            "Analyser en détail les patterns d'achat de ce segment",
            "Identifier les sous-segments potentiels pour affiner la stratégie",
            "Tester différentes approches marketing pour comprendre les leviers",
            "Reclasser progressivement dans les segments principaux"
        ],
        "budget": "5-10% du budget marketing",
        "roi": "Variable selon analyse"
    }
}

# Affichage des recommandations pour le segment sélectionné
reco = recommendations[segment_selected]

# Métriques du segment sélectionné
segment_data = rfm[rfm["Segment"] == segment_selected]
nb_clients = len(segment_data)
ca_total = segment_data["Monetary"].sum()
panier_moyen = segment_data["Monetary"].mean() if nb_clients > 0 else 0
recence_moy = segment_data["Recency"].mean() if nb_clients > 0 else 0
frequence_moy = segment_data["Frequency"].mean() if nb_clients > 0 else 0

# Header
st.markdown(f"### Analyse du segment : {segment_selected}")
st.markdown(f"**Priorité d'action :** `{reco['priorite']}`")

# Métriques clés
col1, col2, col3, col4 = st.columns(4)
col1.metric("Clients", nb_clients)
col2.metric("CA total", f"{ca_total:,.0f} £")
col3.metric("Panier moyen", f"{panier_moyen:,.0f} £")
col4.metric("Part du CA", f"{(ca_total / rfm['Monetary'].sum() * 100):.1f}%")

st.markdown("---")
col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Récence moy.", f"{recence_moy:.0f}")
col_r2.metric("Fréquence moy.", f"{frequence_moy:.1f}")
col_r3.metric("Montant moy.", f"{panier_moyen:,.0f} £")

st.markdown("---")

# Analyse RFM du segment
st.markdown("#### Analyse des scores RFM")
st.info(f"**Profil RFM :** {reco['analyse_rfm']}")
st.markdown(f"**Comportement observé :** {reco['comportement']}")

st.markdown("---")

# Détails des recommandations
col_r1, col_r2 = st.columns([3, 2])

with col_r1:
    
    st.markdown("#### Actions recommandées")
    for i, action in enumerate(reco["actions"], 1):
        st.markdown(f"{i}. {action}")

with col_r2:
    st.markdown("#### Budget alloué recommandé")
    st.info(reco["budget"])
    
    st.markdown("#### ROI attendu")
    st.success(reco["roi"])
    

# Simulateur d'impact
st.markdown("---")
st.markdown("### Simulateur d'impact de campagne")

col_sim1, col_sim2 = st.columns(2)

with col_sim1:
    taux_conversion = st.slider(
        "Taux de conversion (%)",
        1, 50, 10
    )


with col_sim2:
    budget_campagne = st.number_input(
        "Budget campagne (£)",
        min_value=100,
        max_value=100000,
        value=5000,
        step=100
    )


# Calcul d'impact estimé
clients_touches = nb_clients
clients_convertis = int(clients_touches * (taux_conversion / 100))
revenu_estime = clients_convertis * panier_moyen
roi_estime = ((revenu_estime - budget_campagne) / budget_campagne) * 100 if budget_campagne > 0 else 0

st.markdown("### Résultats estimés")
col_res1, col_res2, col_res3 = st.columns(3)
col_res1.metric("Clients potentiels touchés", clients_touches)
col_res2.metric("Conversions estimées", clients_convertis)
col_res3.metric("Revenu généré", f"{revenu_estime:,.0f} £")

st.metric("ROI estimé", f"{roi_estime:.1f}%")

# Analyse de rentabilité
st.markdown("#### Analyse de rentabilité")
if roi_estime > 200:
    st.success(f"**Excellent potentiel** - ROI estimé à {roi_estime:.0f}%. Campagne hautement recommandée pour ce segment.")
elif roi_estime > 100:
    st.success(f"**Bon potentiel** - ROI estimé à {roi_estime:.0f}%. Campagne rentable, à lancer avec confiance.")
elif roi_estime > 0:
    st.warning(f"**Rentabilité modérée** - ROI estimé à {roi_estime:.0f}%. Évaluer si d'autres segments seraient plus performants.")
else:
    st.error(f"**Attention** - ROI négatif estimé à {roi_estime:.0f}%. Revoir la stratégie ou réallouer le budget.")

# Coût par acquisition
st.markdown(f"**Valeur moyenne récupérée par client :** {panier_moyen:.2f} £")

st.markdown("---")

# --- Export ---
if st.button(" Exporter CSV"):
    rfm_filtered.to_csv("export_rfm_segments.csv", index=False)
    st.success("✅ Exporté : export_rfm_segments.csv")