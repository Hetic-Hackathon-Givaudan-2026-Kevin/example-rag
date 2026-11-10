"""Moteur de recommandation de questions (G03, Givaudan AI Challenge).

Principe, volontairement simple et explicable :
1. Chaque question de la banque vise une rubrique du brief.
2. Son score « données » = taux de fois où elle a rempli sa rubrique quand elle a été posée
   (lissage de Laplace : (remplies + 1) / (posées + 2)).
3. Son score « seniors » = (votes utiles + 1) / (votes totaux + 2).
4. Score total = 0,7 x score données + 0,3 x score seniors.
5. Pour un rendez-vous : on prend les rubriques encore vides, les plus souvent manquantes en premier,
   et pour chacune la question au meilleur score total.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DOSSIER_DONNEES = Path(__file__).resolve().parent.parent / "data" / "processed"

# Rubriques d'un brief complet (à confirmer avec Product).
RUBRIQUES = {
    "type_produit": "Type de produit et forme",
    "cible": "Cible consommateur",
    "univers_olfactif": "Univers olfactif et émotion",
    "marche": "Marché, pays et canal",
    "contraintes": "Contraintes (réglementation, labels)",
    "budget_volume": "Budget et volumes",
    "delai": "Délai et étapes de validation",
    "references": "Références et concurrents",
}

POIDS_DONNEES = 0.7
POIDS_SENIORS = 0.3


@dataclass
class Moteur:
    questions: pd.DataFrame
    questions_posees: pd.DataFrame
    comptes_rendus: pd.DataFrame

    @classmethod
    def charger(cls, dossier: Path = DOSSIER_DONNEES, ids_cr: list[str] | None = None) -> "Moteur":
        """Charge les CSV. `ids_cr` permet de n'apprendre que sur une partie des comptes rendus."""
        questions = pd.read_csv(dossier / "questions.csv")
        posees = pd.read_csv(dossier / "questions_posees.csv")
        crs = pd.read_csv(dossier / "comptes_rendus.csv")
        if ids_cr is not None:
            posees = posees[posees["id_cr"].isin(ids_cr)]
            crs = crs[crs["id_cr"].isin(ids_cr)]
        return cls(questions=questions, questions_posees=posees, comptes_rendus=crs)

    # ---------- scores ----------
    def scores(self) -> pd.DataFrame:
        """Une ligne par question : posées, remplies, score données, score seniors, score total."""
        utiles = self.questions_posees[self.questions_posees["rubrique_deja_connue"] == 0]
        stats = (
            utiles.groupby("id_question")["a_rempli_rubrique"]
            .agg(posees="count", remplies="sum")
            .reset_index()
        )
        df = self.questions.merge(stats, on="id_question", how="left").fillna({"posees": 0, "remplies": 0})
        df["posees"] = df["posees"].astype(int)
        df["remplies"] = df["remplies"].astype(int)
        df["score_donnees"] = (df["remplies"] + 1) / (df["posees"] + 2)
        votes = df["votes_utile"] + df["votes_a_reformuler"]
        df["score_seniors"] = (df["votes_utile"] + 1) / (votes + 2)
        df["score_total"] = POIDS_DONNEES * df["score_donnees"] + POIDS_SENIORS * df["score_seniors"]
        return df.sort_values("score_total", ascending=False).reset_index(drop=True)

    def priorite_rubriques(self) -> pd.Series:
        """Part des rendez-vous où chaque rubrique est restée vide à la fin (plus c'est haut, plus c'est prioritaire)."""
        n = len(self.comptes_rendus)
        manquantes = self.comptes_rendus["rubriques_manquantes"].fillna("").str.split(";")
        compte = {r: 0 for r in RUBRIQUES}
        for liste in manquantes:
            for r in liste:
                if r in compte:
                    compte[r] += 1
        return pd.Series({r: (c / n if n else 0.0) for r, c in compte.items()}).sort_values(ascending=False)

    # ---------- recommandation ----------
    def recommander(self, rubriques_connues: list[str], nb_questions: int = 3) -> dict:
        connues = set(rubriques_connues)
        manquantes = [r for r in self.priorite_rubriques().index if r not in connues]
        scores = self.scores()
        choix = []
        for rubrique in manquantes[:nb_questions]:
            candidates = scores[scores["rubrique"] == rubrique]
            if candidates.empty:
                continue
            q = candidates.iloc[0]
            choix.append(
                {
                    "id_question": q["id_question"],
                    "texte": q["texte"],
                    "rubrique": rubrique,
                    "rubrique_libelle": RUBRIQUES[rubrique],
                    "pourquoi": q["pourquoi"],
                    "moment": q["moment"],
                    "auteur": q["auteur"],
                    "score": round(float(q["score_total"]), 3),
                }
            )
        return {"questions": choix, "rubriques_manquantes": manquantes}

    def enregistrer_vote(self, id_question: str, vote: str) -> pd.Series:
        colonne = "votes_utile" if vote == "utile" else "votes_a_reformuler"
        masque = self.questions["id_question"] == id_question
        if not masque.any():
            raise KeyError(id_question)
        self.questions.loc[masque, colonne] += 1
        return self.scores().set_index("id_question").loc[id_question]
