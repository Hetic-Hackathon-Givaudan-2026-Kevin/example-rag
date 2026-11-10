"""Rapport qualité de l'échantillon v0 -> docs/quality_report.md

Mesures : volume, taux de remplissage par champ (vrai et « utile », c.-à-d. hors valeurs
bouche-trou comme « unknown » ou CA = 0), doublons, langues, distributions (biais),
faisabilité du rapprochement marques (Open Facts) <-> entreprises (SIRENE).

Usage : python scripts/quality_report.py
"""
from __future__ import annotations

import json
import re
import unicodedata

import pandas as pd

from _common import RAW, ROOT, now_iso

DOCS = ROOT / "docs"
BOUCHE_TROUS = {"unknown", "not-applicable", "", "none"}


def charger(nom: str) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(RAW / nom, dtype=str, encoding="utf-8")
    meta = json.loads((RAW / f"{nom}.meta.json").read_text(encoding="utf-8"))
    return df, meta


def table(df: pd.DataFrame, index: bool = True) -> str:
    return df.to_markdown(index=index)


def remplissage(df: pd.DataFrame, zero_vide: tuple[str, ...] = ()) -> pd.DataFrame:
    brut = df.notna().mean() * 100
    utile = df.apply(lambda s: s.notna() & ~s.fillna("").str.lower().isin(BOUCHE_TROUS)).mean() * 100
    for c in zero_vide:
        utile[c] = (pd.to_numeric(df[c], errors="coerce").fillna(0) != 0).mean() * 100
    out = pd.DataFrame({"rempli_%": brut.round(1), "utile_%": utile.round(1)})
    return out.sort_values("utile_%")


def repartition(s: pd.Series, n: int = 10, normalize: bool = True) -> pd.DataFrame:
    vc = s.fillna("(vide)").value_counts(normalize=normalize).head(n)
    return (vc * 100).round(1).to_frame("%") if normalize else vc.to_frame("n")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace("-", " ")
    s = re.sub(r"\b(sas|sa|sarl|sasu|snc|groupe|group|france|ste|societe|ets|etablissements|les|la|le|de|des|du)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def main() -> None:
    ent, m_ent = charger("entreprises_v0.csv")
    food, m_food = charger("off_food_fr_v0.csv")
    beauty, m_beauty = charger("obf_beauty_fr_v0.csv")
    L: list[str] = []
    w = L.append

    w("# Rapport qualité — échantillon v0 (données réelles brutes)\n")
    w(f"*Généré par `scripts/quality_report.py` le {now_iso()}. Relançable : les chiffres viennent des fichiers de `data/raw/`.*\n")
    w("Légende : **rempli %** = cellule non vide ; **utile %** = non vide ET pas une valeur bouche-trou "
      "(`unknown`, `not-applicable`, chiffre d'affaires = 0).\n")

    # ---------- Vue d'ensemble ----------
    w("## 1. Vue d'ensemble\n")
    vue = pd.DataFrame([
        {"jeu": "entreprises_v0", "source": "API Recherche d'entreprises", "licence": "Licence Ouverte 2.0",
         "lignes": len(ent), "colonnes": ent.shape[1], "clé": "siren", "doublons_clé": int(ent["siren"].duplicated().sum())},
        {"jeu": "off_food_fr_v0", "source": "Open Food Facts (Parquet HF)", "licence": "ODbL",
         "lignes": len(food), "colonnes": food.shape[1], "clé": "code", "doublons_clé": int(food["code"].duplicated().sum())},
        {"jeu": "obf_beauty_fr_v0", "source": "Open Beauty Facts (Parquet HF)", "licence": "ODbL",
         "lignes": len(beauty), "colonnes": beauty.shape[1], "clé": "code", "doublons_clé": int(beauty["code"].duplicated().sum())},
    ])
    w(table(vue, index=False) + "\n")

    # ---------- Entreprises ----------
    st = m_ent["statistiques"]
    w("## 2. Entreprises (SIRENE via API Recherche d'entreprises)\n")
    w(f"- {st['requetes']} requêtes, {st['recus']} entreprises reçues, **{len(ent)} gardées**.")
    w(f"- Exclues : {st['exclus_ei']} entrepreneurs individuels (RGPD), "
      f"**{st['exclus_diffusion_ou_opposition']} ({st['exclus_diffusion_ou_opposition'] / st['recus']:.0%}) "
      f"pour opposition à la prospection commerciale ou diffusion partielle**.")
    w("- Le champ `dirigeants` a été supprimé à l'import (jamais écrit sur disque).\n")
    w("### Taux de remplissage\n")
    w(table(remplissage(ent, zero_vide=("chiffre_affaires", "resultat_net"))) + "\n")
    ca = pd.to_numeric(ent["chiffre_affaires"], errors="coerce")
    w(f"> Le chiffre d'affaires est présent à {ent['chiffre_affaires'].notna().mean():.0%} mais vaut 0 dans "
      f"{(ca == 0).sum()} cas (comptes confidentiels ou non publiés) : seulement {(ca > 0).mean():.0%} de CA exploitables. "
      f"Années des comptes : {', '.join(f'{k} ({v})' for k, v in ent['annee_finances'].value_counts().head(4).items())}.\n")
    w("### Distributions (pour repérer les biais)\n")
    w("**Catégorie d'entreprise**\n\n" + table(repartition(ent["categorie_entreprise"])) + "\n")
    w("**Tranche d'effectif salarié**\n\n" + table(repartition(ent["tranche_effectif_libelle"], 12)) + "\n")
    w("**Nombre d'entreprises par code NAF** (plafond 50 par code)\n\n"
      + table(ent.groupby(["naf", "naf_libelle"]).size().sort_values(ascending=False).to_frame("n")) + "\n")
    regions = {"11": "Île-de-France", "24": "Centre-Val de Loire", "27": "Bourgogne-Franche-Comté",
               "28": "Normandie", "32": "Hauts-de-France", "44": "Grand Est", "52": "Pays de la Loire",
               "53": "Bretagne", "75": "Nouvelle-Aquitaine", "76": "Occitanie", "84": "Auvergne-Rhône-Alpes",
               "93": "Provence-Alpes-Côte d'Azur", "94": "Corse"}
    w("**Région du siège (top 8)**\n\n"
      + table(repartition(ent["siege_region"].map(lambda r: regions.get(r, r)), 8)) + "\n")
    annees = pd.to_numeric(ent["date_creation"].str[:4], errors="coerce")
    w(f"**Année de création** : médiane {annees.median():.0f}, 25 % avant {annees.quantile(.25):.0f}, "
      f"25 % après {annees.quantile(.75):.0f}.\n")

    # ---------- Open Facts ----------
    for nom, df, meta, flags in [
        ("Open Food Facts (alimentaire)", food, m_food, ["contient_arome", "contient_arome_naturel"]),
        ("Open Beauty Facts (beauté)", beauty, m_beauty, ["contient_parfum"]),
    ]:
        vol = meta["volume"]
        w(f"## {3 if 'Food' in nom else 4}. {nom}\n")
        if "lignes_lues" in vol:
            w(f"- Échantillon : {meta['filtres']['echantillonnage']} -> {vol['lignes_lues']} produits lus "
              f"({vol['mo_telecharges_blocs']} Mo téléchargés), **{vol['lignes']} vendus en France**.")
        else:
            w(f"- Fichier complet : {vol['lignes_source']} produits, **{vol['lignes']} vendus en France**.")
        w(f"- Révision figée : `{meta['revision']}`.\n")
        w("### Taux de remplissage\n")
        w(table(remplissage(df)) + "\n")
        dup_nm = df.dropna(subset=["product_name", "marque_principale"]).duplicated(["product_name", "marque_principale"]).sum()
        w("### Doublons\n")
        w(f"- Code-barres en double : {df['code'].duplicated().sum()}.")
        w(f"- Même nom + même marque (déclinaisons de format/parfum ou vrais doublons) : **{dup_nm}** "
          f"({dup_nm / len(df):.0%}). À dédoublonner avant d'agréger par marque.\n")
        w("### Langues (champ `lang` de la fiche)\n")
        w(table(repartition(df["lang"], 6)) + "\n")
        vc = df["marque_principale"].value_counts()
        w("### Concentration des marques\n")
        w(f"- {len(vc)} marques distinctes ; les 10 premières = **{vc.head(10).sum() / vc.sum():.0%}** des produits avec marque.")
        w(f"- Top 10 : {', '.join(f'{k} ({v})' for k, v in vc.head(10).items())}.")
        w(f"- Marques de distributeur visibles dans le top (Auchan, Carrefour, Cosmia…) : ce sont des clients "
          f"« retail », pas des industriels.\n")
        w("### Indicateurs utiles pour Givaudan\n")
        avec_ingr = df["ingredients_tags"].notna()
        for fl in flags:
            v = df.loc[avec_ingr, fl].eq("True").mean()
            w(f"- `{fl}` : **{v:.0%}** des produits dont les ingrédients sont connus ({avec_ingr.sum()} produits).")
        if "nb_allergenes_parfum" in df:
            nb = pd.to_numeric(df.loc[avec_ingr, "nb_allergenes_parfum"])
            w(f"- Au moins un des 26 allergènes de parfum UE déclaré : {(nb > 0).mean():.0%} des produits avec ingrédients.")
        if "nutriscore_grade" in df:
            w(f"- Nutri-Score : {df['nutriscore_grade'].isin(list('abcde')).mean():.0%} réellement calculé "
              f"(le reste = `unknown` / `not-applicable`).")
        prod = df["fiche_producteur"].eq("True").mean()
        w(f"- Fiches fournies par le producteur lui-même : {prod:.0%} (le reste = contributeurs bénévoles).")
        an = pd.to_datetime(df["created_t"], errors="coerce").dt.year.value_counts().sort_index()
        w(f"- Année de création des fiches : {', '.join(f'{int(k)}: {v}' for k, v in an.items())}.\n")

    # ---------- Rapprochement ----------
    w("## 5. Peut-on relier les produits aux entreprises ?\n")
    noms: dict[str, str] = {}
    for col in ["raison_sociale", "sigle", "enseignes"]:
        for s, v in zip(ent["siren"], ent[col]):
            if pd.notna(v):
                for part in v.split("|"):
                    k = norm(part)
                    if len(k) >= 4:
                        noms[k] = s
    lignes = []
    for nom, df in [("food", food), ("beauty", beauty)]:
        mq = df["marque_principale"].dropna().map(norm)
        ok = mq.isin(noms)
        lignes.append({"jeu": nom, "produits_relies_%": round(ok.mean() * 100, 1),
                       "marques_reliees": int(mq[ok].nunique()),
                       "entreprises_reliees": len({noms[x] for x in mq[ok]}),
                       "exemples": ", ".join(mq[ok].value_counts().head(6).index)})
    w("Test : nom de marque normalisé (sans accents, sans « SAS », « France »…) = raison sociale, sigle ou enseigne.\n")
    w(table(pd.DataFrame(lignes), index=False) + "\n")
    w("> Le lien exact est **faible** : une marque porte rarement le nom légal de la société "
      "(ex. une marque grand public appartient souvent à un groupe au nom différent), "
      "et l'échantillon d'entreprises est plafonné à 50 par code NAF.\n")

    # ---------- Synthèse ----------
    w("## 6. Biais et limites à retenir\n")
    w(f"1. **Biais de taille** : l'API renvoie d'abord les entreprises aux plus gros réseaux d'établissements, et on a "
      f"filtré à ≥ 10 salariés -> les TPE (la majorité des entreprises françaises) sont absentes. "
      f"Cohérent avec la cible Givaudan (industriels), mais à dire au jury.")
    w(f"2. **Biais d'opposition** : {st['exclus_diffusion_ou_opposition'] / st['recus']:.0%} des entreprises reçues "
      f"refusent la prospection. On les exclut par respect de ce choix : le portrait du marché est donc partiel.")
    w("3. **Biais sectoriel** : plafond de 50 par NAF -> les secteurs très peuplés (vin, boulangerie) sont sous-représentés, "
      "les petits secteurs (malt, cidre) sur-représentés en proportion. À repondérer si on calcule des parts de marché.")
    w("4. **Biais Open Facts** : base collaborative -> sur-représentation des grandes marques et des marques de distributeur, "
      "des produits scannés par les bénévoles, et des années de campagnes de contribution (pics 2018-2019 côté food).")
    w("5. **Remplissage** : ingrédients connus pour ~1/3 des produits seulement -> les indicateurs « contient un arôme / "
      "un parfum » sont calculés sur ce tiers, pas sur tout le catalogue.")
    w("6. **Langues** : ~86-90 % des fiches en français, le reste surtout en anglais (produits importés) -> "
      "traitement texte à prévoir en FR avec repli EN.")
    w("7. **Fraîcheur** : SIRENE à jour (mise à jour quotidienne), comptes financiers souvent de 2024-2025 ; "
      "Open Facts figé à la révision du 10/11/2026.")
    w("8. **RGPD** : aucune donnée personnelle conservée (dirigeants, entrepreneurs individuels et pseudos de "
      "contributeurs exclus à l'import).\n")
    (DOCS / "quality_report.md").write_text("\n".join(L), encoding="utf-8")
    print(f"-> {DOCS / 'quality_report.md'}")


if __name__ == "__main__":
    main()
