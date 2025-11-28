import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Cohortes - Diagnostic", layout="wide")

# Style matplotlib
plt.style.use('seaborn-v0_8-whitegrid')


# ============================================================================
# FONCTIONS DE PRÉPARATION DES DONNÉES
# ============================================================================

def prepare_cohort_data(df):
    """
    Prépare les données pour l'analyse de cohortes

    Retourne un DataFrame avec les colonnes supplémentaires :
    - InvoiceMonth : mois de la transaction
    - CohortMonth : mois de première commande du client (= sa cohorte)
    - CohortAge : âge en mois depuis la première commande
    """
    # Filtrer uniquement les ventes (Quantity > 0) et clients valides
    df_cohort = df[(df['Quantity'] > 0) & (df['Customer ID'].notna())].copy()

    # Créer la colonne du mois de transaction
    df_cohort['InvoiceMonth'] = df_cohort['InvoiceDate'].dt.to_period('M')

    # Identifier le mois de première commande pour chaque client (= cohorte)
    df_cohort['CohortMonth'] = df_cohort.groupby('Customer ID')['InvoiceDate'].transform('min').dt.to_period('M')

    # Calculer l'âge de la cohorte (en mois depuis la première commande)
    df_cohort['CohortAge'] = (
            (df_cohort['InvoiceMonth'].dt.year - df_cohort['CohortMonth'].dt.year) * 12 +
            (df_cohort['InvoiceMonth'].dt.month - df_cohort['CohortMonth'].dt.month)
    )

    return df_cohort


def calculate_retention_rate(df_cohort):
    """
    Calcule la matrice de rétention (en %)

    Retourne :
    - retention_rate : matrice avec taux de rétention en %
    - cohort_counts : matrice avec nombre de clients actifs
    """
    # Nombre de clients uniques par cohorte et âge
    cohort_counts = df_cohort.groupby(['CohortMonth', 'CohortAge'])['Customer ID'].nunique().unstack(fill_value=0)

    # Taille initiale de chaque cohorte (âge 0)
    cohort_sizes = cohort_counts.iloc[:, 0]

    # Calcul du taux de rétention (en %)
    retention_rate = cohort_counts.divide(cohort_sizes, axis=0) * 100

    return retention_rate, cohort_counts


# ============================================================================
# FONCTIONS DE VISUALISATION MATPLOTLIB
# ============================================================================

def plot_retention_heatmap(retention_rate):
    """
    Affiche une heatmap du taux de rétention par cohorte
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Convertir l'index Period en string pour l'affichage
    retention_display = retention_rate.copy()
    retention_display.index = retention_display.index.astype(str)

    # Créer la heatmap
    sns.heatmap(
        retention_display,
        annot=True,
        fmt='.1f',
        cmap='Blues',
        cbar_kws={'label': 'Taux de rétention (%)'},
        linewidths=0.5,
        linecolor='white',
        ax=ax
    )

    ax.set_title("Taux de rétention par cohorte d'acquisition (%)",
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Âge de la cohorte (mois)", fontsize=12)
    ax.set_ylabel("Cohorte d'acquisition (mois)", fontsize=12)

    plt.tight_layout()
    return fig


def calculate_revenue_by_age(df_cohort):
    """
    Calcule le CA total par âge de cohorte
    """
    revenue_by_age = df_cohort.groupby(['CohortMonth', 'CohortAge'])['Revenue'].sum().reset_index()
    return revenue_by_age


def plot_revenue_density_curves(revenue_by_age, selected_cohorts=None):
    """
    Affiche les courbes de CA par âge de cohorte
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    if selected_cohorts and len(selected_cohorts) > 0:
        # Filtrer les cohortes sélectionnées
        revenue_by_age = revenue_by_age[revenue_by_age['CohortMonth'].isin(selected_cohorts)]

    # Utiliser une palette de couleurs variées
    colors = plt.cm.tab20.colors

    # Tracer une ligne par cohorte
    for idx, cohort in enumerate(revenue_by_age['CohortMonth'].unique()):
        cohort_data = revenue_by_age[revenue_by_age['CohortMonth'] == cohort]
        ax.plot(cohort_data['CohortAge'], cohort_data['Revenue'],
                marker='o', label=str(cohort), linewidth=2, markersize=5,
                color=colors[idx % len(colors)])

    ax.set_title("Évolution du CA par âge de cohorte",
                 fontsize=14, fontweight='bold')
    ax.set_xlabel("Âge de la cohorte (mois)", fontsize=12)
    ax.set_ylabel("Chiffre d'affaires (£)", fontsize=12)
    ax.legend(title="Cohorte d'acquisition", bbox_to_anchor=(1.05, 1),
              loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Formater l'axe Y avec des séparateurs de milliers
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

    plt.tight_layout()
    return fig


def cohort_deep_dive(df_cohort, selected_cohort):
    """
    Analyse détaillée d'une cohorte spécifique
    """
    cohort_data = df_cohort[df_cohort['CohortMonth'] == selected_cohort]

    # Métriques clés
    total_clients = cohort_data['Customer ID'].nunique()
    total_revenue = cohort_data['Revenue'].sum()
    avg_revenue_per_client = total_revenue / total_clients if total_clients > 0 else 0
    total_transactions = cohort_data['Invoice'].nunique()

    # Évolution mensuelle
    monthly_stats = cohort_data.groupby('CohortAge').agg({
        'Customer ID': 'nunique',
        'Revenue': 'sum',
        'Invoice': 'nunique'
    }).reset_index()
    monthly_stats.columns = ['CohortAge', 'ActiveClients', 'Revenue', 'Transactions']
    monthly_stats['AvgRevenuePerClient'] = monthly_stats['Revenue'] / monthly_stats['ActiveClients']

    return {
        'total_clients': total_clients,
        'total_revenue': total_revenue,
        'avg_revenue_per_client': avg_revenue_per_client,
        'total_transactions': total_transactions,
        'monthly_stats': monthly_stats
    }


def plot_cohort_evolution(monthly_stats, cohort_name):
    """
    Graphique d'évolution avec double axe pour une cohorte
    """
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # Premier axe : CA mensuel (barres)
    ax1.bar(monthly_stats['CohortAge'], monthly_stats['Revenue'],
            color='lightblue', alpha=0.7, label='CA mensuel (£)')
    ax1.set_xlabel("Âge de la cohorte (mois)", fontsize=12)
    ax1.set_ylabel("Chiffre d'affaires (£)", fontsize=12, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

    # Deuxième axe : Clients actifs (ligne)
    ax2 = ax1.twinx()
    ax2.plot(monthly_stats['CohortAge'], monthly_stats['ActiveClients'],
             color='red', marker='o', linewidth=3, markersize=8, label='Clients actifs')
    ax2.set_ylabel("Nombre de clients actifs", fontsize=12, color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Titre
    ax1.set_title(f"Évolution de la cohorte {cohort_name}",
                  fontsize=14, fontweight='bold')

    # Légendes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def fig_to_bytes(fig):
    """Convertit une figure matplotlib en bytes pour le téléchargement"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    return buf


# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

# En-tête de la page
st.title("Analyse des Cohortes - Diagnostic")
st.markdown("""
Cette page permet d'analyser la **rétention** et le **comportement d'achat** des clients groupés par **cohorte d'acquisition**.

**Une cohorte** = ensemble de clients ayant effectué leur première commande le même mois.
""")
st.markdown("---")

# ============================================================================
# RÉCUPÉRATION DES DONNÉES FILTRÉES DEPUIS SESSION_STATE
# ============================================================================

# Vérifier que les données filtrées existent
if "df_filtered" not in st.session_state:
    st.error("Les données filtrées ne sont pas disponibles. Veuillez retourner à la page d'accueil.")
    st.stop()

# Récupérer les données et filtres depuis session_state
df_filtered = st.session_state["df_filtered"]
include_returns = st.session_state.get("include_returns", True)
date_range = st.session_state.get("date_range", None)
countries = st.session_state.get("countries", [])

# Affichage des filtres actifs dans la sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Filtres actifs")
st.sidebar.info(f"""
- **Pays** : {', '.join(countries) if countries else 'Tous'}
- **Période** : {date_range[0] if date_range else 'N/A'} → {date_range[1] if date_range and len(date_range) == 2 else 'N/A'}
- **Retours** : {'Inclus' if include_returns else 'Exclus'}
""")

# ============================================================================
# PRÉPARATION DES DONNÉES DE COHORTES
# ============================================================================

df_cohort = prepare_cohort_data(df_filtered)

if df_cohort.empty:
    st.error("Aucune donnée disponible avec les filtres appliqués.")
    st.stop()

retention_rate, cohort_counts = calculate_retention_rate(df_cohort)

# ============================================================================
# SECTION 1 : HEATMAP DE RÉTENTION
# ============================================================================

st.header("1. Heatmap de rétention par cohortes")

with st.expander("ℹ️ **Qu'est-ce que la rétention ?**"):
    st.markdown("""
    **Définition** : Le **taux de rétention** mesure le pourcentage de clients d'une cohorte qui reviennent acheter à chaque mois suivant leur première commande.

    **Formule** :
    ```
    Rétention (%) = (Clients actifs à M+n / Clients à M+0) × 100
    ```

    **Exemple** : Si une cohorte de 100 clients (M+0) compte 30 clients actifs à M+3, alors la rétention à M+3 = 30%.

    **Interprétation** :
    - **Bleu foncé** = forte rétention (clients fidèles)
    - **Blanc/bleu clair** = faible rétention (clients perdus)
    - **Ligne horizontale** : suivi d'une cohorte dans le temps
    - **Colonne verticale** : comparaison entre cohortes au même âge
    """)

fig_heatmap = plot_retention_heatmap(retention_rate)
st.pyplot(fig_heatmap)
plt.close()

# KPIs clés de rétention
st.subheader("Indicateurs clés de rétention")
col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_retention_m1 = retention_rate[1].mean() if 1 in retention_rate.columns else 0
    st.metric(
        "Rétention M+1",
        f"{avg_retention_m1:.1f}%",
        help="Taux de rétention moyen à 1 mois"
    )

with col2:
    avg_retention_m3 = retention_rate[3].mean() if 3 in retention_rate.columns else 0
    st.metric(
        "Rétention M+3",
        f"{avg_retention_m3:.1f}%",
        help="Taux de rétention moyen à 3 mois"
    )

with col3:
    avg_retention_m6 = retention_rate[6].mean() if 6 in retention_rate.columns else 0
    st.metric(
        "Rétention M+6",
        f"{avg_retention_m6:.1f}%",
        help="Taux de rétention moyen à 6 mois"
    )

with col4:
    best_cohort = retention_rate[3].idxmax() if 3 in retention_rate.columns else "N/A"
    st.metric(
        "Meilleure cohorte (M+3)",
        str(best_cohort),
        help="Cohorte avec le meilleur taux de rétention à 3 mois"
    )

st.markdown("---")

# ============================================================================
# SECTION 2 : COURBES DE DENSITÉ DE CA
# ============================================================================

st.header("2. Courbes de densité de CA par âge")

with st.expander("ℹ️ **Comment interpréter ces courbes ?**"):
    st.markdown("""
    **Définition** : Ces courbes montrent l'évolution du **chiffre d'affaires total** généré par chaque cohorte au fil des mois suivant leur première commande.

    **Interprétation** :
    - **Pic initial** : Les premiers mois montrent généralement une forte activité d'achat
    - **Décroissance** : La baisse indique une réduction de l'activité avec l'âge de la cohorte
    - **Courbes plates** : Signe d'une bonne fidélisation dans le temps
    - **Comparaison entre cohortes** : Permet d'identifier les cohortes les plus rentables

    **Exemple** : Si la cohorte 2010-01 génère 50 000£ à M+3 et 20 000£ à M+6, cela indique une baisse d'activité qu'il faut investiguer.
    """)

# Option de filtre pour sélectionner des cohortes spécifiques
revenue_by_age = calculate_revenue_by_age(df_cohort)
available_cohorts = sorted(revenue_by_age['CohortMonth'].unique(), reverse=True)

col1, col2 = st.columns([3, 1])
with col1:
    filter_cohorts = st.checkbox(
        "Filtrer certaines cohortes",
        value=False,
        help="Cochez pour sélectionner manuellement les cohortes à afficher"
    )

with col2:
    top_n = st.number_input(
        "Nombre de cohortes",
        min_value=1,
        max_value=len(available_cohorts),
        value=min(10, len(available_cohorts)),
        help="Nombre de cohortes les plus récentes à afficher"
    )

if filter_cohorts:
    selected_cohorts_display = st.multiselect(
        "Sélectionnez les cohortes à afficher",
        options=[str(c) for c in available_cohorts],
        default=[str(c) for c in available_cohorts[:top_n]],
        help="Choisissez les cohortes à comparer"
    )
    selected_cohorts_periods = [pd.Period(c, freq='M') for c in selected_cohorts_display]
else:
    selected_cohorts_periods = available_cohorts[:top_n]

fig_revenue = plot_revenue_density_curves(revenue_by_age, selected_cohorts_periods)
st.pyplot(fig_revenue)
plt.close()

st.markdown("---")

# ============================================================================
# SECTION 3 : FOCUS SUR UNE COHORTE
# ============================================================================

st.header("3. Focus sur une cohorte spécifique")

with st.expander("ℹ️ **Pourquoi analyser une cohorte en détail ?**"):
    st.markdown("""
    L'analyse détaillée d'une cohorte permet de :
    - Comprendre son **comportement d'achat** dans le temps
    - Estimer sa **valeur future** (CLV)
    - Identifier les **moments critiques** où les clients décrochent
    - Adapter les **actions marketing** en fonction de l'âge de la cohorte
    """)

# Sélecteur de cohorte
available_cohorts_str = [str(c) for c in available_cohorts]

col1, col2 = st.columns([2, 1])
with col1:
    selected_cohort_str = st.selectbox(
        "Sélectionnez une cohorte à analyser",
        available_cohorts_str,
        help="Choisissez le mois de première acquisition des clients"
    )

# Convertir back en Period
selected_cohort = pd.Period(selected_cohort_str, freq='M')

# Analyse détaillée
cohort_analysis = cohort_deep_dive(df_cohort, selected_cohort)

# Affichage des KPIs
st.markdown(f"### Cohorte : **{selected_cohort_str}**")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        "Clients totaux",
        f"{cohort_analysis['total_clients']:,}",
        help="Nombre de clients uniques dans cette cohorte"
    )
with col2:
    st.metric(
        "CA total",
        f"{cohort_analysis['total_revenue']:,.0f} £",
        help="Chiffre d'affaires total généré par cette cohorte"
    )
with col3:
    st.metric(
        "CA moyen/client",
        f"{cohort_analysis['avg_revenue_per_client']:,.0f} £",
        help="Revenu moyen par client de la cohorte"
    )
with col4:
    st.metric(
        "Transactions",
        f"{cohort_analysis['total_transactions']:,}",
        help="Nombre total de transactions effectuées"
    )

st.markdown("#### Évolution mensuelle de la cohorte")

# Graphique d'évolution avec double axe
monthly_stats = cohort_analysis['monthly_stats']
fig_evolution = plot_cohort_evolution(monthly_stats, selected_cohort_str)
st.pyplot(fig_evolution)
plt.close()

st.markdown("---")

# ============================================================================
# SECTION 4 : EXPORTS
# ============================================================================

st.header("4. Exports")

col1, col2 = st.columns(2)

with col1:
    # Export CSV rétention
    csv_retention = retention_rate.to_csv()
    st.download_button(
        label="Télécharger matrice de rétention (CSV)",
        data=csv_retention,
        file_name=f"retention_matrix_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        help="Télécharge la matrice de rétention au format CSV"
    )

with col2:
    # Export CSV revenue
    csv_revenue = revenue_by_age.to_csv(index=False)
    st.download_button(
        label="Télécharger CA par âge (CSV)",
        data=csv_revenue,
        file_name=f"revenue_by_age_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        help="Télécharge les données de CA par âge de cohorte"
    )

st.markdown("---")

# Section export PNG
st.subheader("Export graphiques (PNG)")

col1, col2 = st.columns(2)

with col1:
    # Régénérer heatmap pour export
    fig_hm_export = plot_retention_heatmap(retention_rate)
    png_heatmap = fig_to_bytes(fig_hm_export)
    plt.close()

    st.download_button(
        label="Télécharger Heatmap (PNG)",
        data=png_heatmap,
        file_name=f"heatmap_retention_{datetime.now().strftime('%Y%m%d')}.png",
        mime="image/png",
        help="Télécharge la heatmap de rétention"
    )

with col2:
    # Régénérer courbes revenue pour export
    fig_rev_export = plot_revenue_density_curves(revenue_by_age, selected_cohorts_periods)
    png_revenue = fig_to_bytes(fig_rev_export)
    plt.close()

    st.download_button(
        label="Télécharger Courbes CA (PNG)",
        data=png_revenue,
        file_name=f"courbes_ca_{datetime.now().strftime('%Y%m%d')}.png",
        mime="image/png",
        help="Télécharge les courbes de CA par âge"
    )

st.markdown("---")


