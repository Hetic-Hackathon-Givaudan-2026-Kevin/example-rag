"""Échantillon v0 des entreprises clientes potentielles (agroalimentaire, boissons, parfums-cosmétiques).

Source : API Recherche d'entreprises (DINUM), https://recherche-entreprises.api.gouv.fr
Données issues de la base SIRENE (INSEE) et du RNE (INPI), Licence Ouverte 2.0 (Etalab).
Accès : sans clé, limite officielle 7 requêtes/s -> on reste à ~3 req/s.

RGPD, appliqué AVANT toute écriture sur disque :
- le champ `dirigeants` n'est jamais conservé ;
- les entrepreneurs individuels (nature juridique 1xxx) sont exclus : leur nom = nom d'une personne ;
- les unités en diffusion partielle (statut_diffusion != "O") sont exclues ;
- les entreprises qui ont fait opposition à la prospection commerciale
  (`opposition_diffusion_commerciale` = true) sont exclues, puisque notre usage est commercial.

Usage : python scripts/fetch_entreprises.py [--max-par-code 50]
"""
from __future__ import annotations

import argparse
import time

import pandas as pd
import requests

from _common import RAW, USER_AGENT, write_meta

API = "https://recherche-entreprises.api.gouv.fr/search"

# Nomenclature NAF rév. 2 (INSEE, Licence Ouverte) — libellés courts des codes ciblés.
NAF = {
    "10.11Z": "Transformation et conservation de la viande de boucherie",
    "10.12Z": "Transformation et conservation de la viande de volaille",
    "10.13A": "Préparation industrielle de produits à base de viande",
    "10.13B": "Charcuterie",
    "10.20Z": "Transformation et conservation de poisson, crustacés et mollusques",
    "10.31Z": "Transformation et conservation de pommes de terre",
    "10.32Z": "Préparation de jus de fruits et légumes",
    "10.39A": "Autre transformation et conservation de légumes",
    "10.39B": "Transformation et conservation de fruits",
    "10.41A": "Fabrication d'huiles et graisses brutes",
    "10.41B": "Fabrication d'huiles et graisses raffinées",
    "10.42Z": "Fabrication de margarine et graisses comestibles similaires",
    "10.51A": "Fabrication de lait liquide et de produits frais",
    "10.51B": "Fabrication de beurre",
    "10.51C": "Fabrication de fromage",
    "10.51D": "Fabrication d'autres produits laitiers",
    "10.52Z": "Fabrication de glaces et sorbets",
    "10.61A": "Meunerie",
    "10.61B": "Autres activités du travail des grains",
    "10.62Z": "Fabrication de produits amylacés",
    "10.71A": "Fabrication industrielle de pain et de pâtisserie fraîche",
    "10.71B": "Cuisson de produits de boulangerie",
    "10.71C": "Boulangerie et boulangerie-pâtisserie",
    "10.71D": "Pâtisserie",
    "10.72Z": "Fabrication de biscuits, biscottes et pâtisseries de conservation",
    "10.73Z": "Fabrication de pâtes alimentaires",
    "10.81Z": "Fabrication de sucre",
    "10.82Z": "Fabrication de cacao, chocolat et produits de confiserie",
    "10.83Z": "Transformation du thé et du café",
    "10.84Z": "Fabrication de condiments et assaisonnements",
    "10.85Z": "Fabrication de plats préparés",
    "10.86Z": "Fabrication d'aliments homogénéisés et diététiques",
    "10.89Z": "Fabrication d'autres produits alimentaires n.c.a.",
    "10.91Z": "Fabrication d'aliments pour animaux de ferme",
    "10.92Z": "Fabrication d'aliments pour animaux de compagnie",
    "11.01Z": "Production de boissons alcooliques distillées",
    "11.02A": "Fabrication de vins effervescents",
    "11.02B": "Vinification",
    "11.03Z": "Fabrication de cidre et de vins de fruits",
    "11.04Z": "Production d'autres boissons fermentées non distillées",
    "11.05Z": "Fabrication de bière",
    "11.06Z": "Fabrication de malt",
    "11.07A": "Industrie des eaux de table",
    "11.07B": "Production de boissons rafraîchissantes",
    "20.42Z": "Fabrication de parfums et de produits pour la toilette",
}

# Tranches d'effectif salarié INSEE ; on garde les employeurs de 10 salariés et plus.
TRANCHES = {
    "11": "10 à 19", "12": "20 à 49", "21": "50 à 99", "22": "100 à 199", "31": "200 à 249",
    "32": "250 à 499", "41": "500 à 999", "42": "1 000 à 1 999", "51": "2 000 à 4 999",
    "52": "5 000 à 9 999", "53": "10 000 et plus",
}


def get(session: requests.Session, params: dict) -> dict:
    for essai in range(4):
        r = session.get(API, params=params, timeout=30)
        if r.status_code == 429:  # trop de requêtes : on attend et on réessaie
            time.sleep(2 ** essai)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return {}


def nettoyer(e: dict) -> dict | None:
    """Garde uniquement des champs « entreprise » (aucune donnée de personne)."""
    if str(e.get("nature_juridique") or "").startswith("1"):
        return None  # entrepreneur individuel
    if e.get("statut_diffusion") != "O" or e.get("opposition_diffusion_commerciale"):
        return None
    siege = e.get("siege") or {}
    comp = e.get("complements") or {}
    fin = e.get("finances") or {}
    annee_fin = max(fin) if fin else None
    return {
        "siren": e["siren"],
        "raison_sociale": e.get("nom_raison_sociale") or e.get("nom_complet"),
        "sigle": e.get("sigle"),
        "enseignes": "|".join(siege.get("liste_enseignes") or []) or None,
        "naf": e.get("activite_principale"),
        "naf_libelle": NAF.get(e.get("activite_principale")),
        "naf25": e.get("activite_principale_naf25"),
        "categorie_entreprise": e.get("categorie_entreprise"),
        "tranche_effectif": e.get("tranche_effectif_salarie"),
        "tranche_effectif_libelle": TRANCHES.get(e.get("tranche_effectif_salarie")),
        "annee_tranche_effectif": e.get("annee_tranche_effectif_salarie"),
        "date_creation": e.get("date_creation"),
        "nature_juridique": e.get("nature_juridique"),
        "nb_etablissements_ouverts": e.get("nombre_etablissements_ouverts"),
        "siege_code_postal": siege.get("code_postal"),
        "siege_commune": siege.get("libelle_commune"),
        "siege_departement": siege.get("departement"),
        "siege_region": siege.get("region"),
        "siege_latitude": siege.get("latitude"),
        "siege_longitude": siege.get("longitude"),
        "annee_finances": annee_fin,
        "chiffre_affaires": (fin.get(annee_fin) or {}).get("ca") if annee_fin else None,
        "resultat_net": (fin.get(annee_fin) or {}).get("resultat_net") if annee_fin else None,
        "est_bio": comp.get("est_bio"),
        "est_ess": comp.get("est_ess"),
        "est_societe_mission": comp.get("est_societe_mission"),
        "egapro_renseignee": comp.get("egapro_renseignee"),
        "bilan_ges_renseigne": comp.get("bilan_ges_renseigne"),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--max-par-code", type=int, default=50, help="plafond d'entreprises par code NAF")
    args = p.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    lignes, stats = [], {"recus": 0, "exclus_ei": 0, "exclus_diffusion_ou_opposition": 0,
                         "exclus_naf_etablissement_seulement": 0, "requetes": 0}
    for code in NAF:
        gardes, page = 0, 1
        while gardes < args.max_par_code and page <= 20:
            data = get(session, {
                "activite_principale": code, "etat_administratif": "A",
                "tranche_effectif_salarie": ",".join(TRANCHES), "per_page": 25, "page": page,
            })
            stats["requetes"] += 1
            time.sleep(0.35)  # ~3 requêtes/s, sous la limite officielle de 7/s
            resultats = data.get("results", [])
            for e in resultats:
                stats["recus"] += 1
                if e.get("activite_principale") != code:
                    stats["exclus_naf_etablissement_seulement"] += 1
                    continue
                if str(e.get("nature_juridique") or "").startswith("1"):
                    stats["exclus_ei"] += 1
                    continue
                ligne = nettoyer(e)  # `dirigeants` est jeté ici, jamais écrit
                if ligne is None:
                    stats["exclus_diffusion_ou_opposition"] += 1
                    continue
                lignes.append(ligne)
                gardes += 1
                if gardes >= args.max_par_code:
                    break
            if page >= data.get("total_pages", 0) or not resultats:
                break
            page += 1
        print(f"{code}: {gardes} entreprises")

    df = pd.DataFrame(lignes).drop_duplicates("siren")
    out = RAW / "entreprises_v0.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    write_meta(
        out,
        source="API Recherche d'entreprises (DINUM) — données SIRENE (INSEE) et RNE (INPI)",
        url=API,
        documentation="https://recherche-entreprises.api.gouv.fr/docs/",
        licence="Licence Ouverte / Open Licence 2.0 (Etalab)",
        filtres={
            "codes_naf": list(NAF),
            "etat_administratif": "A (active)",
            "tranche_effectif_salarie": "10 salariés et plus (codes " + ",".join(TRANCHES) + ")",
            "naf_unite_legale_egal_code_demande": True,
            "max_par_code_naf": args.max_par_code,
            "ordre_api": "tri par défaut de l'API (les plus gros réseaux d'établissements d'abord)",
        },
        rgpd=[
            "champ dirigeants supprimé à l'import (jamais écrit sur disque)",
            "entrepreneurs individuels exclus (nature juridique 1xxx)",
            "statut_diffusion partiel exclu",
            "opposition_diffusion_commerciale = true exclu",
        ],
        statistiques=stats,
        volume={"lignes": int(len(df)), "colonnes": int(df.shape[1])},
    )
    print(f"-> {out} ({len(df)} lignes) | {stats}")


if __name__ == "__main__":
    main()
