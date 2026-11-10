"""Échantillon v0 des produits vendus par les marques (Open Food Facts + Open Beauty Facts), France.

Source : exports officiels Parquet publiés par Open Food Facts sur Hugging Face
  https://huggingface.co/datasets/openfoodfacts/product-database
Révision FIGÉE (hash de commit) pour la reproductibilité : REVISION ci-dessous.
Licence : base de données ODbL 1.0, contenus DbCL 1.0 (images CC BY-SA, non utilisées).
L'API d'OFF n'est pas utilisée (robots.txt : Disallow /api pour les robots ; on passe par l'export prévu pour ça).

- beauty.parquet (~67 Mo) : téléchargé entier dans data/raw/_cache (non versionné).
- food.parquet (~8 Go) : on lit seulement N blocs (« row groups ») tirés au hasard (graine fixe)
  et quelques colonnes, par requêtes HTTP Range -> quelques dizaines de Mo.

RGPD : les colonnes de contributeurs (creator, editors, last_editor, photographers, informers,
correctors, checkers, last_modified_by) ne sont jamais lues. `owner` est réduit à un booléen
« fiche fournie par le producteur » (owner commençant par « org- »).

Usage : python scripts/fetch_open_facts.py [--food-row-groups 60]
"""
from __future__ import annotations

import argparse
import random
import re

import pandas as pd
import pyarrow.parquet as pq
import requests

from _common import CACHE, RAW, SEED, USER_AGENT, write_meta
from _http_range import HttpRangeFile

REPO = "openfoodfacts/product-database"
REVISION = "12a54ce27f7166bad0d8947e2ebeb258cec157c1"  # commit HF du 2026-11-10
BASE = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}"
LICENCE = "ODbL 1.0 (base) / DbCL 1.0 (contenus) — Open Food Facts"

COLS_COMMUNES = [
    "code", "product_name", "brands", "brands_tags", "categories_tags", "labels_tags",
    "countries_tags", "lang", "ingredients_tags", "ingredients_n", "created_t",
    "last_modified_t", "completeness", "owner",
]
COLS_FOOD = COLS_COMMUNES + ["nutriscore_grade", "nova_group"]

# 26 allergènes de parfum à déclarer en UE (règlement 1223/2009, annexe III) — noms INCI simplifiés.
ALLERGENES_PARFUM = [
    "limonene", "linalool", "citronellol", "geraniol", "citral", "coumarin", "eugenol",
    "benzyl-alcohol", "benzyl-benzoate", "benzyl-salicylate", "benzyl-cinnamate", "cinnamal",
    "cinnamyl-alcohol", "hydroxycitronellal", "isoeugenol", "amyl-cinnamal", "amylcinnamyl-alcohol",
    "anise-alcohol", "anisyl-alcohol", "farnesol", "hexyl-cinnamal", "butylphenyl-methylpropional",
    "alpha-isomethyl-ionone", "hydroxyisohexyl-3-cyclohexene-carboxaldehyde",
    "evernia-prunastri", "evernia-furfuracea", "methyl-2-octynoate",
]
RE_PARFUM = re.compile(r"^[a-z]{2}:(parfums?|fragrances?|perfume|aroma)$")
# « flavouring » = arôme ; on exclut volontairement « flavour-enhancer » (exhausteur de goût, ex. glutamate).
RE_AROME = re.compile(r"flavouring|flavoring|:aromes?$|:arome-")
RE_AROME_NATUREL = re.compile(r"natural-(.+-)?flavouring")


def nom_produit(valeur) -> str | None:
    """product_name est une liste [{lang, text}] : on prend le français, sinon 'main', sinon le 1er."""
    if valeur is None or len(valeur) == 0:
        return None
    par_langue = {d["lang"]: d["text"] for d in valeur if d.get("text")}
    return par_langue.get("fr") or par_langue.get("main") or next(iter(par_langue.values()), None)


def liste(v) -> list[str]:
    return [] if v is None else [str(x) for x in v]


def preparer(df: pd.DataFrame, base: str) -> pd.DataFrame:
    df = df[df["countries_tags"].apply(lambda t: "en:france" in liste(t))].copy()
    df["product_name"] = df["product_name"].apply(nom_produit)
    # brands_tags arrive sous la forme « xx:Cosmia » / « xx:cosmia » : on retire le préfixe et on uniformise la casse.
    df["marque_principale"] = df["brands_tags"].apply(
        lambda t: re.sub(r"^[a-z]{2}:", "", liste(t)[0]).lower() if len(liste(t)) else None)
    ingr = df["ingredients_tags"].apply(liste)
    if base == "food":
        df["contient_arome"] = ingr.apply(lambda t: any(RE_AROME.search(x) for x in t))
        df["contient_arome_naturel"] = ingr.apply(lambda t: any(RE_AROME_NATUREL.search(x) for x in t))
    else:
        df["contient_parfum"] = ingr.apply(lambda t: any(RE_PARFUM.match(x) for x in t))
        df["nb_allergenes_parfum"] = ingr.apply(
            lambda t: sum(any(x.endswith(":" + a) for x in t) for a in ALLERGENES_PARFUM))
    df["fiche_producteur"] = df["owner"].fillna("").str.startswith("org-")
    df = df.drop(columns=["owner"])
    for c in ["brands_tags", "categories_tags", "labels_tags", "countries_tags", "ingredients_tags"]:
        df[c] = df[c].apply(lambda t: "|".join(liste(t)) or None)
    for c in ["created_t", "last_modified_t"]:
        df[c] = pd.to_datetime(df[c], unit="s", errors="coerce").dt.date
    return df


def fichier_distant(nom: str, session: requests.Session):
    """Ouvre food.parquet à distance, en mettant en cache son pied de page (métadonnées, ~100 Mo)."""
    h = HttpRangeFile(f"{BASE}/{nom}", session=session)
    meta_cache = CACHE / f"{nom}.{REVISION[:8]}.footer"
    if meta_cache.exists():
        return pq.ParquetFile(h, metadata=pq.read_metadata(meta_cache)), h
    pf = pq.ParquetFile(h)
    pf.metadata.write_metadata_file(meta_cache)
    return pf, h


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--food-row-groups", type=int, default=60)
    args = p.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    # --- Open Beauty Facts : fichier complet (petit) ---
    local = CACHE / f"beauty.{REVISION[:8]}.parquet"
    if not local.exists():
        with session.get(f"{BASE}/beauty.parquet", stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(local, "wb") as f:
                for bloc in r.iter_content(1 << 20):
                    f.write(bloc)
    total_beauty = pq.ParquetFile(local).metadata.num_rows
    beauty = preparer(pq.read_table(local, columns=COLS_COMMUNES).to_pandas(), "beauty")
    out_b = RAW / "obf_beauty_fr_v0.csv"
    beauty.to_csv(out_b, index=False, encoding="utf-8")
    write_meta(
        out_b, source="Open Beauty Facts — export Parquet officiel (beauty.parquet)",
        url=f"https://huggingface.co/datasets/{REPO}/blob/{REVISION}/beauty.parquet",
        revision=REVISION, licence=LICENCE,
        filtres={"pays": "countries_tags contient en:france", "colonnes": COLS_COMMUNES},
        rgpd=["colonnes contributeurs non lues", "owner réduit à un booléen fiche_producteur"],
        volume={"lignes_source": int(total_beauty), "lignes": int(len(beauty)), "colonnes": int(beauty.shape[1])},
    )
    print(f"-> {out_b} ({len(beauty)} produits FR sur {total_beauty})")

    # --- Open Food Facts : quelques blocs tirés au hasard ---
    pf, h = fichier_distant("food.parquet", session)
    n_rg = pf.metadata.num_row_groups
    tirage = sorted(random.Random(SEED).sample(range(n_rg), args.food_row_groups))
    lu_avant = h.bytes_read
    food = pf.read_row_groups(tirage, columns=COLS_FOOD).to_pandas()
    lus = len(food)
    food = preparer(food, "food")
    out_f = RAW / "off_food_fr_v0.csv"
    food.to_csv(out_f, index=False, encoding="utf-8")
    write_meta(
        out_f, source="Open Food Facts — export Parquet officiel (food.parquet)",
        url=f"https://huggingface.co/datasets/{REPO}/blob/{REVISION}/food.parquet",
        revision=REVISION, licence=LICENCE,
        filtres={
            "echantillonnage": f"{args.food_row_groups} row groups sur {n_rg}, tirés avec random.Random({SEED})",
            "row_groups": tirage, "pays": "countries_tags contient en:france", "colonnes": COLS_FOOD,
        },
        rgpd=["colonnes contributeurs non lues", "owner réduit à un booléen fiche_producteur"],
        volume={"lignes_source": int(pf.metadata.num_rows), "lignes_lues": int(lus),
                "lignes": int(len(food)), "colonnes": int(food.shape[1]),
                "mo_telecharges_blocs": round((h.bytes_read - lu_avant) / 1e6, 1)},
    )
    print(f"-> {out_f} ({len(food)} produits FR sur {lus} lus, {(h.bytes_read - lu_avant) / 1e6:.0f} Mo)")


if __name__ == "__main__":
    main()
