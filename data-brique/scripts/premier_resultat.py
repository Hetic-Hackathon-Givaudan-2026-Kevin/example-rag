"""Premier résultat Data pour la Gate 1 : le moteur choisit-il de meilleures questions que la trame générique ?

Méthode
- On sépare les comptes rendus : 70 % pour apprendre les scores, 30 % gardés de côté pour tester.
- Sur la partie test, on mesure le taux réel de réussite de chaque question (a-t-elle rempli sa rubrique ?).
- Pour chaque rendez-vous test, on compare 3 façons de choisir 3 questions pour les mêmes rubriques vides :
  le moteur, la trame générique, et un choix au hasard.

Produit : resultats/premier_resultat.md et resultats/scores_questions.csv
Lancer : python scripts/premier_resultat.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from src.moteur_v1 import RUBRIQUES, Moteur  # noqa: E402

GRAINE = 7
DONNEES = RACINE / "data" / "processed"
SORTIE = RACINE / "docs"


def taux_lisse(remplies: float, posees: float) -> float:
    return (remplies + 1) / (posees + 2)


def tableau_md(df: pd.DataFrame) -> str:
    colonnes = list(df.columns)
    lignes = ["| " + " | ".join(colonnes) + " |", "| " + " | ".join("---" for _ in colonnes) + " |"]
    for _, row in df.iterrows():
        lignes.append("| " + " | ".join(str(row[c]) for c in colonnes) + " |")
    return "\n".join(lignes)


def main() -> None:
    SORTIE.mkdir(exist_ok=True)
    rng = random.Random(GRAINE)
    crs = pd.read_csv(DONNEES / "comptes_rendus.csv")
    posees = pd.read_csv(DONNEES / "questions_posees.csv")
    questions = pd.read_csv(DONNEES / "questions.csv")
    clients = pd.read_csv(DONNEES / "clients.csv")
    cachees = json.loads((DONNEES / "parametres_simulation.json").read_text(encoding="utf-8"))["qualite_cachee_par_question"]

    ids = sorted(crs["id_cr"])
    rng.shuffle(ids)
    coupe = int(len(ids) * 0.7)
    ids_app, ids_test = set(ids[:coupe]), set(ids[coupe:])

    moteur = Moteur.charger(DONNEES, ids_cr=list(ids_app))
    scores = moteur.scores()
    priorite = moteur.priorite_rubriques()

    # Taux réel de réussite sur la partie test
    test = posees[(posees["id_cr"].isin(ids_test)) & (posees["rubrique_deja_connue"] == 0)]
    stats_test = test.groupby("id_question")["a_rempli_rubrique"].agg(posees="count", remplies="sum")
    taux_test = {q: taux_lisse(stats_test.loc[q, "remplies"], stats_test.loc[q, "posees"]) if q in stats_test.index
                 else taux_lisse(0, 0) for q in questions["id_question"]}

    generique = questions[questions["auteur"] == "trame_generique"].set_index("rubrique")["id_question"].to_dict()
    par_rubrique = questions.groupby("rubrique")["id_question"].apply(list).to_dict()

    # Comparaison sur chaque rendez-vous test
    lignes = []
    for _, cr in crs[crs["id_cr"].isin(ids_test)].iterrows():
        connues = [r for r in str(cr["rubriques_connues_avant"]).split(";") if r in RUBRIQUES]
        reco = moteur.recommander(connues, 3)["questions"]
        rubriques_visees = [q["rubrique"] for q in reco]
        if not rubriques_visees:
            continue
        lignes.append({
            "id_cr": cr["id_cr"],
            "moteur": sum(taux_test[q["id_question"]] for q in reco),
            "trame_generique": sum(taux_test[generique[r]] for r in rubriques_visees),
            "hasard": sum(sum(taux_test[q] for q in par_rubrique[r]) / len(par_rubrique[r]) for r in rubriques_visees),
            "nb_questions": len(reco),
        })
    comp = pd.DataFrame(lignes)
    moyennes = comp[["moteur", "trame_generique", "hasard"]].mean()

    # Taux observé (non lissé) : questions classées n°1 par le moteur vs questions génériques
    numero_un = scores.drop_duplicates("rubrique")["id_question"].tolist()
    obs_un = test[test["id_question"].isin(numero_un)]["a_rempli_rubrique"]
    obs_gen = test[test["id_question"].isin(generique.values())]["a_rempli_rubrique"]

    # Le moteur retrouve-t-il les bonnes questions ? (comparaison avec la qualité cachée de la simulation)
    scores["qualite_cachee"] = scores["id_question"].map(cachees)
    correlation = scores[["score_donnees", "qualite_cachee"]].corr(method="spearman").iloc[0, 1]

    # Constat descriptif : juniors contre seniors
    par_niveau = crs.groupby("niveau").agg(rendez_vous=("id_cr", "count"),
                                           briefs_complets=("brief_complet", "mean"),
                                           allers_retours=("nb_allers_retours_creatifs", "mean"),
                                           questions_posees=("nb_questions_posees", "mean")).round(2)

    # Exemples pour trois clients
    exemples_spec = [("C02", ["type_produit"]), ("C11", ["type_produit", "cible", "budget_volume"]), ("C25", ["type_produit", "marche", "delai"])]
    blocs_exemples = []
    for cid, connues in exemples_spec:
        c = clients.set_index("id_client").loc[cid]
        reco = moteur.recommander(connues, 3)["questions"]
        lignes_ex = pd.DataFrame([{"Question": q["texte"], "Rubrique": q["rubrique_libelle"],
                                   "Pourquoi": q["pourquoi"], "Score": q["score"]} for q in reco])
        blocs_exemples.append(f"**{c['nom']} ({cid}, fictif)** : secteur {c['secteur']}, client {c['taille']}, "
                              f"{c['pays_principal']}. Déjà connu : {', '.join(RUBRIQUES[r] for r in connues)}.\n\n"
                              + tableau_md(lignes_ex))

    # Sorties
    colonnes_scores = ["id_question", "rubrique", "auteur", "posees", "remplies", "score_donnees",
                       "score_seniors", "score_total", "qualite_cachee", "texte"]
    scores[colonnes_scores].round(3).to_csv(SORTIE / "scores_questions.csv", index=False)

    gain_gen = (moyennes["moteur"] / moyennes["trame_generique"] - 1) * 100
    gain_hasard = (moyennes["moteur"] / moyennes["hasard"] - 1) * 100
    top = scores[["id_question", "rubrique", "auteur", "posees", "score_donnees", "score_seniors", "score_total"]].round(2)

    md = f"""# Premier résultat Data — G03 (données fictives)

Données : {len(crs)} comptes rendus fictifs, {len(posees)} questions posées, {len(questions)} questions en banque.
Apprentissage sur {len(ids_app)} comptes rendus, test sur {len(ids_test)} gardés de côté.

## Résultat principal

Pour les mêmes rubriques vides, les 3 questions choisies par le moteur remplissent en moyenne
**{moyennes['moteur']:.2f} rubriques sur 3**, contre **{moyennes['trame_generique']:.2f}** avec la trame générique
et **{moyennes['hasard']:.2f}** au hasard, soit **{gain_gen:+.0f} %** par rapport à la trame générique
et **{gain_hasard:+.0f} %** par rapport au hasard (mesuré sur les rendez-vous test).

Taux de réussite observé sur la partie test : questions classées n°1 par le moteur **{obs_un.mean():.0%}**
({len(obs_un)} fois posées), questions de la trame générique **{obs_gen.mean():.0%}** ({len(obs_gen)} fois posées).

## Exemples : les 3 questions proposées

""" + "\n\n".join(blocs_exemples) + f"""

## Constat sur les comptes rendus : juniors et seniors

{tableau_md(par_niveau.reset_index())}

Attention : cet écart vient des paramètres de la simulation (les juniors y choisissent plus souvent la trame générique).
Il illustre le problème, mais ce n'est pas un constat réel.

## Priorité des rubriques (part des rendez-vous où la rubrique est restée vide)

{tableau_md(priorite.round(2).rename('part_manquante').reset_index().rename(columns={'index': 'rubrique'}))}

## Scores de toutes les questions

{tableau_md(top)}

## Limites, à dire au jury

- Les données sont fictives. La « qualité » de chaque question a été fixée dans le script de génération,
  et le moteur la retrouve (corrélation de Spearman entre score appris et qualité cachée : {correlation:.2f}).
  Cela prouve que la chaîne fonctionne, pas que ces questions marchent dans la réalité.
- La preuve réelle viendra de vrais commerciaux : relecture des questions, votes des seniors,
  puis mesure des allers-retours avec les créatifs.
- Certaines questions ont été peu posées : leur score est encore incertain (lissage de Laplace pour limiter l'effet).
"""
    (SORTIE / "premier_resultat.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
