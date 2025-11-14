# Projet data visualisation

## Présentation :
Le projet vise à construire une application d’aide à la décision pour le marketing basée sur les cohortes d’acquisition, la segmentation RFM et la valeur vie client (CLV).

**Données :** le jeu de données à utiliser est le Online Retail II (UCI) , il contient les transactions e‑commerce d’un détaillant UK entre 01/12/2009 et le  09/12/2011(~1,07M lignes). 

## Objectifs :
- Mesurer la rétention par cohortes (M+1, M+2, …) et la dynamique de revenu.
- Construire des segments RFM (Recency–Frequency–Monetary) pour prioriser les actions.
- Estimer la CLV via (1) une approche empirique basée sur les cohortes et (2) une formule avec paramètres (r) (rétention) et (d) (taux d’actualisation).
- Tester des scénarios (ex. +5% de rétention, −10% de marge) et évaluer l’impact business.

## Intérêts business :
- Pilotage budget d’acquisition par LTV et définition de CPA cibles.
- Priorisation CRM : où investir (segments/cohortes qui répondent), où réduire les dépenses.
- Politiques de remise/retours : quantifier effet sur marge et rétention.
- Prévision court terme : revenus par âge de cohorte, densité de valeur.

## I. Partie 1 : Notebook d’exploration visuelle complète
L'objectif de cette partie est d'utiliser les connaissances acquises sur l'exploration visuelle dans le cours et de l'appliquer afin d'acquérir une compréhension exhaustive du jeu de données, ce qui vous permettra également par la suite de cadrer la conception de l’application streamlit et orientera vos analyses, transformations et visualisations de l'app streamlit.

### Résultats attendus dans le notebook
1. Fiche synthétique des données : source, période couverte, volume, colonnes importantes.
2. Dictionnaire des variables : nom, type, sémantique, unités/valeurs.
3. Qualité des données : valeurs manquantes, doublons, outliers, règles d’annulation (factures InvoiceNo commençant par "C"), granularité temporelle.
4. Graphiques visuels (6-8 graphes) :distributions; saisonnalités/tendances des ventes; répartition pays; mix grossiste/détaillant; premier aperçu des cohortes; premier profil RFM
5. Questions d'analyses pour mieux pour cadrer l’appli : exemples. quelles cohortes décrochent ? quels segments RFM sont à forte valeur ? quel impact des retours ?

**Contrainte forte sur le rendu :** Définir clairement toutes les métriques et interpreter/expliquer les visuels affichées dans le notebook.

## II. Partie 2 : Application Streamlit
L'objectif de cette partie est de créer une application streamlit qui va permettre à l’équipe marketing de diagnostiquer, prioriser et simuler en temps réel :
1. rétention par cohorte d’acquisition
2. CLV par segment et au global
3. Segments RFM à activer
4. Scénarios (remise, marge, +rétention) avec calcul immédiat de l’impact (CLV, CA et rétention)

### Périmètre fonctionnel
Chaque élément ci‑dessous précise ce que l'application doit permettre de faire et pourquoi c’est utile pour l’utilisateur final de votre application.
- **Filtres possibles :**
Sélecteurs période d’analyse (glissante), Unités de temps (mois/trimestre), pays, type client, seuil de commande, mode retours (inclure / exclure / neutraliser). Pourquoi : isoler un périmètre homogène, comparer des fenêtres temporelles et évaluer l’effet des retours sur les métriques.

- **Vues / Pages streamlit (structure conseillée)**
KPIs (Overview) — À livrer : cartes chiffres (clients actifs, CA/âge de cohorte, taille segments RFM, CLV baseline, North Star). Pourquoi : donner un état instantané partagé. Cohortes (Diagnostiquer) — À livrer : heatmap rétention par cohortes, courbes de densité de CA par âge, possibilité de focus sur une cohorte. Pourquoi : repérer les âges qui décrochent et estimer la valeur future. Segments (Prioriser) — À livrer : table RFM (codes, labels, volumes, CA, marge, panier moyen) + priorités d’activation (ex. Champions, À risque). Pourquoi : orienter les actions CRM. Scénarios (Simuler) — À livrer : comparaison baseline vs scénario (barres/deltas) + sensibilités (courbe). Pourquoi : chiffrer l’impact d’une remise, d’un gain de rétention ou d’une variation de marge. Plan d’action (Exporter) — À livrer : export CSV “liste activable” (CustomerID, segment RFM, métriques clés) et PNGs des vues. Pourquoi : passer du constat à l’exécution.

- Scénarios (paramètres de simulation) À livrer : sliders marge %, rétention (r), taux d’actualisation (d), remise moyenne % (avec choix d’application globale ou par segment RFM), commutateur inclure retours, sélecteur cohorte cible (ou toutes). Pourquoi : quantifier Δ CLV / Δ CA / Δ rétention pour aider à décider.

- Exports À livrer : CSV des données filtrées et des listes activables, PNG des graphiques (avec titre, date, filtres actifs). Pourquoi : traçabilité, partage, passage à l’action.

### Important :
La conception techniques et l'architecture du code sont des tâches qui doivent être effectués par vos soins afin d'atteindre les objectifs et le péromètre fonctionnel spécifiés. Comme chaque projet en entreprise, le descriptif présenté dans ce projet représent les besoin exprimés par votre client. C'est à vous de trouver le chemin technique pour construire l'application.

### KPIs (définitions à afficher dans l’app)
Chaque KPI doit afficher une aide montrant sa définition et son unité (infobulle ou autre), l'ajout d'un exemple numérique illustratif dans l’aide est un plus
Exemples de KPIs à définir, expliquer et illustrer : CLV moyenne (ou CA à 90 jours par nouveau client); Rétention à t; rétention M+3; RFM score; CLV (empirique); CLV (formule fermée);

**Cohérences visuelle et applicative conseillées** 
- Toujours afficher les filtres actifs
- Toujours donner les effectifs (n) à côté des pourcentages.
- Quand un retour est exclu, afficher un badge « retours exclus ».
- Les comparaisons baseline vs scénario doivent toujours préciser la période et l’échantillon.
- Une idée par graphique
- Labels directs sur les lignes/barres
- Ordre de lecture dans l'app : KPIs → tendances → segments → scénarios → export.
- Soigner l'accessibilité : tailles de police, unités, contrastes...
- Gestion des valeurs manquantes/outliers explicitée
- Aide intégrée (icône ℹ️) : définitions + mini‑exemples numériques.
