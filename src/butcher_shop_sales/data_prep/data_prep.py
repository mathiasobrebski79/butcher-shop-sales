# %%
import os 

import pandas as pd

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
    "saucisse de toulouse",
    "chorizo"
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
    "cotelette" : "agneau"
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
        "brochette" : "BROCHETTE", 
        "chipolata" : "CHIPOLATA"
        })\
    .str.replace({
        "broch" : "brochette", 
        "chipo" : "chipolata"
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

# df_enrich[["libelle","animal_brut","non_identifie","animal_tmp","animal"]]\
#     .drop_duplicates()\
    # .query("animal!=animal")
# %%

df_final = df_enrich[
    ["libelle","animal","preparation","annee","semaine","date","valeur_prix_vente"]
].fillna("autre")

# %%
df_final.head()

# %%

df_final.to_excel(
    os.path.join(DATA_DIR,"processed_" + raw_data_file),
)

# %%
