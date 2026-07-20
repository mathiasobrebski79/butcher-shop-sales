import os

import streamlit as st
import pandas as pd
import plotly.express as px

from butcher_shop_sales.settings import DATA_DIR

st.set_page_config(page_title="Ventes Boucherie", layout="wide")

# ----------------------------------------------------------------------
# Chargement des données
# ----------------------------------------------------------------------
st.sidebar.header("📂 Données")

# uploaded_file = st.sidebar.file_uploader("Charger le fichier Excel", type=["xlsx", "xls"])
uploaded_file = os.path.join(DATA_DIR,"processed_summer_2025.xlsx" )

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df["date"] = pd.to_datetime(df["date"])
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    st.info("Chargez un fichier Excel pour commencer (colonnes attendues : "
            "libelle, animal, preparation, morceau, annee, semaine, date, valeur_prix_vente, produit).")
    st.stop()

# ----------------------------------------------------------------------
# Filtres (sidebar)
# ----------------------------------------------------------------------
st.sidebar.header("🔍 Filtres")

if "reset_counter" not in st.session_state:
    st.session_state["reset_counter"] = 0
 
if st.sidebar.button("🔄 Réinitialiser les filtres"):
    st.session_state["reset_counter"] += 1
    st.rerun()
 
suffix = st.session_state["reset_counter"]


libelles = sorted(df["libelle"].dropna().unique())
animaux = sorted(df["animal"].dropna().unique())
preparations = sorted(df["preparation"].dropna().unique())
produits = sorted(df["produit"].dropna().unique())

selected_libelles = st.sidebar.multiselect("Libelle", options=libelles, default=libelles, key=f"filtre_libelles_{suffix}")
selected_animaux = st.sidebar.multiselect("Animal", options=animaux, default=animaux, key=f"filtre_animaux_{suffix}")
selected_preparations = st.sidebar.multiselect("Préparation", options=preparations, default=preparations, key=f"filtre_preparations_{suffix}")
selected_produits = st.sidebar.multiselect("Produit", options=produits, default=produits, key=f"filtre_produits_{suffix}")

date_min = df["date"].min().date()
date_max = df["date"].max().date()

selected_dates = st.sidebar.slider(
    "Période",
    min_value=date_min,
    max_value=date_max,
    value=(date_min, date_max),
    format="DD/MM/YYYY",
    key=f"filtre_dates_{suffix}"
)

annees_toutes = sorted(df["annee"].dropna().astype(int).unique())
st.sidebar.write("Années")
cols_annees_sidebar = st.sidebar.columns(len(annees_toutes))
selected_annees = []
for col, annee in zip(cols_annees_sidebar, annees_toutes):
    if col.checkbox(str(annee), value=True, key=f"filtre_annee_{annee}_{suffix}"):
        selected_annees.append(annee)

semaine_min_all = int(df["semaine"].min())
semaine_max_all = int(df["semaine"].max())
selected_semaines = st.sidebar.slider(
    "Semaines",
    min_value=semaine_min_all,
    max_value=semaine_max_all,
    value=(semaine_min_all, semaine_max_all),
    key=f"filtre_semaines_{suffix}",
)

# ----------------------------------------------------------------------
# Application des filtres
# ----------------------------------------------------------------------
mask = (
    df["libelle"].isin(selected_libelles)
    & df["animal"].isin(selected_animaux)
    & df["preparation"].isin(selected_preparations)
    & df['produit'].isin(selected_produits)
    & (df["date"].dt.date >= selected_dates[0])
    & (df["date"].dt.date <= selected_dates[1])
    & df["annee"].astype(int).isin(selected_annees)
    & df["semaine"].astype(int).between(selected_semaines[0], selected_semaines[1])
)

df_filtered = df.loc[mask]

# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------
st.title("🥩 Dashboard Ventes Boucherie")

col1, col2, col3 = st.columns(3)
col1.metric("Chiffre d'affaires total", f"{df_filtered['valeur_prix_vente'].sum():,.0f} €")
col2.metric("Nombre de produits", df_filtered["libelle"].nunique())
col3.metric("Nombre de lignes", len(df_filtered))

if df_filtered.empty:
    st.warning("⚠️ Sélection vide : aucune donnée ne correspond aux filtres actuels. "
               "Modifiez votre sélection ou cliquez sur « Réinitialiser les filtres ».")
    st.stop()


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 CA par libellé", 
    "📈 Évolution hebdomadaire libellé",
    "📊 CA par produit", 
    "📈 Évolution hebdomadaire produit",
    "📈 Évolution hebdomadaire produit par année",
    ])
 
# ----------------------------------------------------------------------
# Onglet 1 : CA cumulé par libellé
# ----------------------------------------------------------------------
with tab1:
    st.subheader("Chiffre d'affaires cumulé par libellé")
 
    df_grouped_libelle = (
        df_filtered.groupby(["libelle", "animal"], as_index=False)["valeur_prix_vente"]
        .sum()
        .sort_values("valeur_prix_vente", ascending=False)
    )
 
    max_libelle = len(df_grouped_libelle)
    if max_libelle <= 1:
        nb_libelle = max_libelle
    else:
        nb_libelle = st.slider(
            "Nombre de libellés à afficher",
            min_value=1,
            max_value=min(100, max_libelle),
            value=min(20, max_libelle),
        )

    df_top_libelle = df_grouped_libelle.head(nb_libelle)
 
    fig_libelle = px.bar(
        df_top_libelle,
        x="valeur_prix_vente",
        y="libelle",
        orientation="h",
        color="animal",
        labels={"valeur_prix_vente": "Chiffre d'affaires (€)", "libelle": "Libellé", "animal": "Animal"},
    )
    # Trie les barres par CA décroissant (indépendamment de la couleur)
    fig_libelle.update_layout(
        yaxis={"categoryorder": "array", "categoryarray": df_top_libelle.sort_values("valeur_prix_vente")["libelle"]},
        height=600,
    )
 
    st.plotly_chart(fig_libelle, use_container_width=True)
 
    with st.expander("Voir les données filtrées"):
        st.dataframe(df_grouped_libelle, use_container_width=True)
 
# ----------------------------------------------------------------------
# Onglet 2 : Évolution hebdomadaire (stacked bar par libelle)
# ----------------------------------------------------------------------
with tab2:
    st.subheader("Chiffre d'affaires par libellé et par semaine")
 
    df_weekly = df_filtered.copy()
    # Clé année-semaine triable chronologiquement (ex: 2025-S03)
    df_weekly["annee_semaine"] = (
        df_weekly["annee"].astype(int).astype(str)
        + "-S"
        + df_weekly["semaine"].astype(int).astype(str).str.zfill(2)
    )
 
    df_weekly_grouped = (
        df_weekly.groupby(["annee_semaine", "libelle"], as_index=False)["valeur_prix_vente"]
        .sum()
    )
 
    ordre_semaines = sorted(df_weekly_grouped["annee_semaine"].unique())
 
    fig_libelle_weekly = px.bar(
        df_weekly_grouped,
        x="annee_semaine",
        y="valeur_prix_vente",
        color="libelle",
        category_orders={"annee_semaine": ordre_semaines},
        labels={"annee_semaine": "Semaine", "valeur_prix_vente": "Chiffre d'affaires (€)", "libelle": "Libelle"},
    )
    fig_libelle_weekly.update_layout(barmode="stack", height=600, showlegend=True)
 
    st.plotly_chart(fig_libelle_weekly, use_container_width=True)
 
    with st.expander("Voir les données filtrées"):
        st.dataframe(df_weekly_grouped, use_container_width=True)
 
# ----------------------------------------------------------------------
# Onglet 3 : CA cumulé par produit
# ----------------------------------------------------------------------
with tab3:
    st.subheader("Chiffre d'affaires cumulé par produit")
 
    df_grouped_produit = (
        df_filtered.groupby(["produit", "animal"], as_index=False)["valeur_prix_vente"]
        .sum()
        .sort_values("valeur_prix_vente", ascending=False)
    )
 
    max_produits = len(df_grouped_produit)
    if max_produits <= 1:
        nb_produits = max_produits
    else:
        nb_produits = st.slider(
            "Nombre de produits à afficher",
            min_value=1,
            max_value=min(100, max_produits),
            value=min(20, max_produits),
        )

    df_top_produit = df_grouped_produit.head(nb_produits)
 
    fig_produit = px.bar(
        df_top_produit,
        x="valeur_prix_vente",
        y="produit",
        orientation="h",
        color="animal",
        labels={"valeur_prix_vente": "Chiffre d'affaires (€)", "produit": "Produit", "animal": "Animal"},
    )
    # Trie les barres par CA décroissant (indépendamment de la couleur)
    fig_produit.update_layout(
        yaxis={"categoryorder": "array", "categoryarray": df_top_produit.sort_values("valeur_prix_vente")["produit"]},
        height=600,
    )
 
    st.plotly_chart(fig_produit, use_container_width=True)
 
    with st.expander("Voir les données filtrées"):
        st.dataframe(df_grouped_produit, use_container_width=True)
 
# ----------------------------------------------------------------------
# Onglet 4 : Évolution hebdomadaire (stacked bar par libelle)
# ----------------------------------------------------------------------
with tab4:
    st.subheader("Chiffre d'affaires par produit par semaine")
 
    df_weekly = df_filtered.copy()
    # Clé année-semaine triable chronologiquement (ex: 2025-S03)
    df_weekly["annee_semaine"] = (
        df_weekly["annee"].astype(int).astype(str)
        + "-S"
        + df_weekly["semaine"].astype(int).astype(str).str.zfill(2)
    )
 
    df_weekly_grouped = (
        df_weekly.groupby(["annee_semaine", "produit"], as_index=False)["valeur_prix_vente"]
        .sum()
    )
 
    ordre_semaines = sorted(df_weekly_grouped["annee_semaine"].unique())
 
    fig_produit_weekly = px.bar(
        df_weekly_grouped,
        x="annee_semaine",
        y="valeur_prix_vente",
        color="produit",
        category_orders={"annee_semaine": ordre_semaines},
        labels={"annee_semaine": "Semaine", "valeur_prix_vente": "Chiffre d'affaires (€)", "produit": "Produit"},
    )
    fig_produit_weekly.update_layout(barmode="stack", height=600, showlegend=True)
 
    st.plotly_chart(fig_produit_weekly, use_container_width=True)
 
    with st.expander("Voir les données filtrées"):
        st.dataframe(df_weekly_grouped, use_container_width=True)
 
# ----------------------------------------------------------------------
# Onglet 5 : Évolution hebdomadaire par année (barres groupées)
# ----------------------------------------------------------------------
with tab5:
    st.subheader("Chiffre d'affaires par semaine, séparé par année")

    if df_filtered.empty:
        st.warning("⚠️ Aucune donnée pour cette sélection.")
    else:
        df_weekly_year = df_filtered.copy()
        df_weekly_year["semaine"] = df_weekly_year["semaine"].astype(int)
        df_weekly_year["annee"] = df_weekly_year["annee"].astype(str)  # string pour légende propre

        df_weekly_year_grouped = (
            df_weekly_year.groupby(["semaine", "annee"], as_index=False)["valeur_prix_vente"]
            .sum()
        )

        fig_weekly_year = px.bar(
            df_weekly_year_grouped,
            x="semaine",
            y="valeur_prix_vente",
            color="annee",
            barmode="group",
            labels={
                "semaine": "Semaine",
                "valeur_prix_vente": "Chiffre d'affaires (€)",
                "annee": "Année",
            },
        )
        fig_weekly_year.update_layout(height=600, showlegend=True)
        fig_weekly_year.update_xaxes(dtick=1)

        st.plotly_chart(fig_weekly_year, use_container_width=True)

        with st.expander("Voir les données filtrées"):
            st.dataframe(df_weekly_year_grouped, use_container_width=True)