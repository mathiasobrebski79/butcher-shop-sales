# %%
import os 

import pandas as pd
import numpy as np

from butcher_shop_sales.settings import DATA_DIR

pd.set_option('display.max_rows', None)
# pd.reset_option('display.max_rows')

# %%

raw_data_file = "summer_2025.xlsx"

df_raw = pd.read_excel(
    os.path.join(DATA_DIR,raw_data_file),
    skiprows=7
)


# %%
df_refactor = df_raw.copy()

df_refactor.columns = df_refactor.columns\
    .str.replace(" ","_")\
    .str.replace("é","e")\
    .str.lower()


# %%
df_sel = df_refactor[
     ["libelle","annee/semaine","valeur_prix_vente"]
     ]

# remove empty cells
df_sel.dropna(inplace=True) 
    

# %%

df_enrich = df_sel.copy()


df_enrich[["annee","semaine"]] = \
           df_enrich["annee/semaine"].str.split("/", expand=True)

df_enrich["date"] = pd.to_datetime(df_enrich["annee/semaine"]+"/1", format="%Y/%W/%w").dt.date


df_enrich["libelle"] = df_enrich["libelle"].str.lower()



# %%

meat_types = [
    "boeuf",
    "bovine",
    "agneau",
    "ovine",
    "porc",
    "veau",
    "poulet",
    "caille",
    "lapin",
    "volaille",
    "plt",
    "coqlt",
    "coquelet",
    "canette"
    ]

preparation_types = [
    "merguez",
    "andouilette",
    "chair saucisse",
    "toulouse",
    "saucisse de toulouse",
    "toulouse",
    "saucisse de veau",
    "chorizo",
    "chipolatas herbes",
    "chipo herbes",
    "chipolata",
    "chipo",
    "cordon bleu",
    "brochette",
    "broch"
    ]

unidentified_cuts = {
    "rumsteck" : "boeuf",
    "tournedos" : "boeuf",
    "bavette" : "boeuf",
    "steak" : "boeuf",
    "basse cote" : "boeuf",
    "paleron" : "boeuf",
    "bourguignon" : "boeuf",
    "jarret" : "boeuf",
    "pot au feu" : "boeuf",
    "faux filet" : "boeuf",
    "entrecote" : "boeuf",
    "tournedos" : "boeuf",
    "tendron" : "veau",
    "tranche poitrine" : "porc",
    "cotelette" : "agneau",
    "toulouse" : "porc",
    "chair" : "porc",
    "merguez" : "boeuf-agneau",
    "chipo" : "porc",
    "cordon bleu" : "volaille"
}

others = [
    "bouch trad",
    "boucherie trad",
    "viande pour animaux"
]


# extract meat info
meat_pat = "(" + "|".join(meat_types) + ")"

df_enrich["animal_brut"] = \
    df_enrich["libelle"]\
        .str.extract(meat_pat)

df_enrich["animal_brut"] = df_enrich["animal_brut"]\
    .str.replace({
        "bovine" : "boeuf", 
        "ovine" : "agneau",
        "plt" : "poulet",
        "coqlt" : "coquelet"
        })

# extract prep info
prep_pat = "(" + "|".join(preparation_types) + ")"
df_enrich["preparation"] = \
    df_enrich["libelle"]\
        .str.extract(prep_pat)

df_enrich["preparation"] = df_enrich["preparation"]\
    .str.replace({
        "chipolatas herbes" : "chipolata herbe", 
        "chipo herbes" : "chipolata herbe",
        })\
    .str.replace({
        "brochette" : "BROCHETTE", 
        "chipolata" : "CHIPOLATA",
        "saucisse de toulouse" : "SAUCISSE DE TOULOUSE"
        })\
    .str.replace({
        "broch" : "brochette", 
        "chipo" : "chipolata",
        "toulouse"  : "saucisse de toulouse"
        })\
    .str.lower()

# extract unidentified cuts

ui_pat = "(" + "|".join(unidentified_cuts.keys()) + ")"
df_enrich["non_identifie"] = \
    df_enrich["libelle"]\
        .str.extract(ui_pat)

df_enrich["animal_tmp"] = df_enrich["non_identifie"]\
    .str.replace(unidentified_cuts)

df_enrich["animal"] = df_enrich["animal_brut"]\
    .where(
        ~df_enrich["animal_brut"].isna(),
        df_enrich["animal_tmp"]
    )


# %%

beef_cuts = [
    "cote",
    "aloyau a l'os",
    "rumsteck",
    "tranch",
    "onglet",
    "bavette aloyau",
    "bavette d'aloyau",
    "bavette flanchet",
    "filet",
    "tournedos",
    "faux filet",
    "entrecote",
    "poire",
    "macreuse",
    "hampe",
    "basse cote",
    "araignee",
    "gite noix",
    "bifteck hache",
    "paleron",
    "plat cote",
    "jarret",
    "bourg",
    "queue",
    "os a moelle",
    "pieces a fondu",
    "steak",
    "poitrine",
    "pot au feu",
    "t bone",
    "pave",
    "abt.*os",
    "roti"
]
porc_cuts = [
    "pave",
    "araignee",
    "cote echine",
    "cote filet",
    "cote 1ere",
    "filet mignon",
    "echine",
    "carre",
    "filet",
    "grillade",
    "saute",
    "poitrine",
    "chair",
    "travers",
    "barde",
    "farce",
    "brasse",
    "ribs",
    "roti"
]
veal_cuts = [
    "epaule",
    "filet",
    "nx",
    "noix",
    "cote premiere",
    "tendron",
    "blanquette",
    "foie",
    "rognon",
    "grenadin",
    "escalope",
    "cote",
    "osso bucco",
    "paupiette",
    "jarret"
]
lamb_cuts = [
    "collier",
    "gigot entier",
    "souris",
    "tranche gigot",
    "cote filet",
    "cote premiere",
    "cote decouverte",
    "epaule",
    "poitrine",
    "rognon",
    "roti",
    "tranche",
    "cotelette",
    "navarin",
    "tr"
]
chicken_cuts = [
    "cuisse",
    "crapodine",
    "aile",
    "pilon",
    "cuiss ",
    "hdc",
    "filet",
    "flts"
]


df_enrich["morceau"] = pd.NA

# beef cuts
beef_cut_pat = r"(" + "|".join(beef_cuts) + ")"

mask_beef = df_enrich["animal"]=='boeuf'

df_enrich.loc[mask_beef,"morceau"] = \
    df_enrich.loc[mask_beef,"libelle"] \
        .str.extract(beef_cut_pat).values

df_enrich["morceau"] = df_enrich["morceau"]\
        .str.replace({
            "bavette d'aloyau" : "bavette aloyau",
             "tranch" : "tranche",
             "abt v.bovine os" : "os a moelle"
             })

# porc cuts 
porc_cut_pat = r"(" + "|".join(porc_cuts) + ")"

mask_porc = df_enrich["animal"]=='porc'

df_enrich.loc[mask_porc,"morceau"] = \
    df_enrich.loc[mask_porc,"libelle"] \
        .str.extract(porc_cut_pat).values


# veal cuts
veal_cut_pat = r"(" + "|".join(veal_cuts) + ")"

mask_veal = df_enrich["animal"]=='veau'

df_enrich.loc[mask_veal,"morceau"] = \
    df_enrich.loc[mask_veal,"libelle"] \
        .str.extract(veal_cut_pat).values

df_enrich.loc[mask_veal,"morceau"] = \
    df_enrich.loc[mask_veal,"morceau"] \
        .str.replace({
            "nx" : "noix",
             "jarret" : "osso bucco"
             }).values

# lamb cuts
lamb_cut_pat = r"(" + "|".join(lamb_cuts) + ")"

mask_lamb = df_enrich ["animal"]=='agneau'

df_enrich.loc[mask_lamb,"morceau"] = \
    df_enrich.loc[mask_lamb,"libelle"] \
        .str.extract(lamb_cut_pat).values

# chicken cuts
chicken_cut_pat = r"(" + "|".join(chicken_cuts) + ")"

mask_chicken = df_enrich["animal"]=='poulet'

df_enrich.loc[mask_chicken,"morceau"] = \
    df_enrich.loc[mask_chicken,"libelle"] \
        .str.extract(chicken_cut_pat).values

df_enrich.loc[mask_chicken,"morceau"] = \
    df_enrich.loc[mask_chicken,"morceau"] \
        .str.replace({
            "flts" : "filet",
             "hdc" : "cuisse",
             "cuiss " : "cuisse"
             }).values

# %%
df_enrich["morceau_preparation"] = \
    df_enrich["morceau"].where(
        ~df_enrich["morceau"].isna(),
        df_enrich["preparation"]
    )

# %%
df_enrich[["libelle","animal","morceau","morceau_preparation"]]\
    .drop_duplicates()\
    [df_enrich["animal"].str.contains("poulet")]

    # .query("preparation contains 'chipo'")

# %%

df_final = df_enrich[
    ["libelle","animal","morceau_preparation","preparation","morceau","annee","semaine","date","valeur_prix_vente"]
].fillna("autre")

df_final["produit"] = df_final[["animal","morceau_preparation"]].agg('-'.join, axis=1)

del df_final["morceau_preparation"]

# %%
df_final.head()

# %%

df_final.to_excel(
    os.path.join(DATA_DIR,"processed_" + raw_data_file),
)

# %%
