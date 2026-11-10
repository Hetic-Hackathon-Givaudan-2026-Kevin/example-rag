"""API Data de l'équipe G03 : propose 3 questions avant un rendez-vous commercial.

Lancer :  uvicorn api.main:app --reload --port 8000   (depuis la racine du projet)
Swagger : http://localhost:8000/docs
Partager à Tech :  ngrok http 8000
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.moteur_v1 import RUBRIQUES, Moteur  # noqa: E402

Rubrique = Enum("Rubrique", {r: r for r in RUBRIQUES}, type=str)


class Secteur(str, Enum):
    parfum_fin = "parfum_fin"
    soin_corps = "soin_corps"
    capillaire = "capillaire"
    hygiene = "hygiene"
    entretien_maison = "entretien_maison"


class Taille(str, Enum):
    multinationale = "multinationale"
    regionale = "regionale"
    locale = "locale"


class Vote(str, Enum):
    utile = "utile"
    a_reformuler = "a_reformuler"


class Client(BaseModel):
    id_client: Optional[str] = Field(None, examples=["C07"])
    nom: Optional[str] = Field(None, examples=["Maison Lunelle (fictif)"])
    secteur: Optional[Secteur] = None
    taille: Optional[Taille] = None
    pays_principal: Optional[str] = Field(None, examples=["France"])


class DemandeQuestions(BaseModel):
    client: Client = Field(default_factory=Client)
    rubriques_connues: List[Rubrique] = Field(
        default_factory=list,
        description="Rubriques du brief déjà connues avant le rendez-vous.",
        examples=[["type_produit", "cible"]],
    )
    nb_questions: int = Field(3, ge=1, le=8)


class QuestionProposee(BaseModel):
    id_question: str
    texte: str
    rubrique: Rubrique
    rubrique_libelle: str
    pourquoi: str
    moment: str = Field(description="debut, milieu ou fin du rendez-vous")
    auteur: str = Field(description="Senior qui a proposé la question, ou trame_generique")
    score: float = Field(description="Score total entre 0 et 1")


class ReponseQuestions(BaseModel):
    client: Client
    questions: List[QuestionProposee]
    rubriques_manquantes: List[Rubrique] = Field(description="Rubriques encore vides, les plus prioritaires d'abord")
    methode: str


class DemandeVote(BaseModel):
    id_question: str = Field(examples=["Q07"])
    id_senior: str = Field(examples=["senior_B"])
    vote: Vote
    commentaire: Optional[str] = None


class ReponseVote(BaseModel):
    id_question: str
    votes_utile: int
    votes_a_reformuler: int
    score_seniors: float
    score_total: float


class QuestionBanque(BaseModel):
    id_question: str
    texte: str
    rubrique: Rubrique
    pourquoi: str
    auteur: str
    posees: int
    remplies: int
    score_donnees: float
    score_seniors: float
    score_total: float


app = FastAPI(
    title="API Data G03 - Copilote de briefing",
    version="0.1.0",
    description=(
        "Propose au commercial junior les 3 questions qui comblent le mieux les trous de son brief, "
        "avec le pourquoi de chaque question, et enregistre les votes des seniors. "
        "Données fictives pour le hackathon : aucune donnée Givaudan réelle."
    ),
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

moteur = Moteur.charger()


@app.get("/sante", tags=["Technique"], summary="Vérifier que l'API répond")
def sante() -> dict:
    return {"statut": "ok", "questions_en_banque": int(len(moteur.questions))}


@app.post("/questions", response_model=ReponseQuestions, tags=["Recommandation"],
          summary="Proposer les questions à poser avant un rendez-vous")
def proposer_questions(demande: DemandeQuestions) -> ReponseQuestions:
    connues = [r.value for r in demande.rubriques_connues]
    resultat = moteur.recommander(connues, demande.nb_questions)
    return ReponseQuestions(
        client=demande.client,
        questions=resultat["questions"],
        rubriques_manquantes=resultat["rubriques_manquantes"],
        methode="Rubriques vides les plus souvent manquantes, puis meilleure question par score "
                "(0,7 taux de réussite dans les comptes rendus + 0,3 votes des seniors).",
    )


@app.post("/feedback", response_model=ReponseVote, tags=["Seniors"],
          summary="Enregistrer le vote d'un senior sur une question")
def voter(demande: DemandeVote) -> ReponseVote:
    try:
        ligne = moteur.enregistrer_vote(demande.id_question, demande.vote.value)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Question inconnue : {demande.id_question}")
    return ReponseVote(
        id_question=demande.id_question,
        votes_utile=int(ligne["votes_utile"]),
        votes_a_reformuler=int(ligne["votes_a_reformuler"]),
        score_seniors=round(float(ligne["score_seniors"]), 3),
        score_total=round(float(ligne["score_total"]), 3),
    )


@app.get("/banque", response_model=List[QuestionBanque], tags=["Seniors"],
         summary="Lister la banque de questions avec leurs scores")
def banque(rubrique: Optional[Rubrique] = None) -> List[QuestionBanque]:
    df = moteur.scores()
    if rubrique is not None:
        df = df[df["rubrique"] == rubrique.value]
    colonnes = list(QuestionBanque.model_fields)
    return [QuestionBanque(**{k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
            for row in df[colonnes].to_dict(orient="records")]
