"""Génère le jeu de données FICTIF de l'équipe G03 (reproductible : graine fixe).

Fichiers produits dans data/ :
- clients.csv           30 marques clientes fictives
- questions.csv         banque de 24 questions (3 par rubrique : bonne, moyenne, générique)
- comptes_rendus.csv    90 rendez-vous simulés et leur issue
- questions_posees.csv  une ligne par question posée en rendez-vous, avec son effet
- briefs.csv            le brief obtenu après chaque rendez-vous
- parametres_simulation.json  les paramètres cachés de la simulation (pour être transparent)

ATTENTION : la « qualité » de chaque question est fixée à la main dans ce script, puis le moteur
la retrouve à partir des comptes rendus. Le résultat prouve que la chaîne fonctionne, pas que
telle question marche dans la réalité. Seuls de vrais retours de commerciaux peuvent le prouver.

Lancer : python scripts/generer_donnees.py
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

GRAINE = 42
RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "data" / "processed"

RUBRIQUES = ["type_produit", "cible", "univers_olfactif", "marche",
             "contraintes", "budget_volume", "delai", "references"]

# (id, rubrique, texte, pourquoi, moment, auteur, qualité cachée)
QUESTIONS = [
    ("Q01", "type_produit", "Dans quel produit le parfum sera-t-il utilisé, et sous quelle forme (spray, gel, poudre) ?",
     "La base technique change toute la formule : un parfum pour lessive ne se travaille pas comme un parfum fin.", "debut", "senior_A", 0.90),
    ("Q02", "type_produit", "Est-ce une création, une rénovation ou l'extension d'une gamme existante ?",
     "Dit au parfumeur s'il part de zéro ou d'une formule existante.", "debut", "senior_B", 0.80),
    ("Q03", "type_produit", "Quel est votre produit ?",
     "Question de la trame générique : trop large, le client répond souvent par le nom commercial.", "debut", "trame_generique", 0.55),
    ("Q04", "cible", "Décrivez-moi la personne qui achètera ce produit : son âge, son quotidien, ce qu'elle achète déjà.",
     "Fait passer d'une cible marketing abstraite à un portrait concret que les créatifs peuvent utiliser.", "debut", "senior_C", 0.85),
    ("Q05", "cible", "Votre produit s'adresse-t-il plutôt à un public jeune, familial ou premium ?",
     "Donne vite un ordre de grandeur, mais reste une case à cocher.", "debut", "senior_A", 0.65),
    ("Q06", "cible", "Quelle est votre cible ?",
     "Question de la trame générique : le client répète souvent sa plaquette marketing.", "debut", "trame_generique", 0.45),
    ("Q07", "univers_olfactif", "Quelle émotion voulez-vous que le consommateur ressente quand il ouvre le produit ?",
     "Fait parler le client en images plutôt qu'en termes techniques qu'il ne maîtrise pas.", "milieu", "senior_B", 0.90),
    ("Q08", "univers_olfactif", "Y a-t-il un souvenir, un lieu ou une matière qui représente votre marque ?",
     "Donne au parfumeur une piste créative concrète, même si le client ne connaît pas les familles olfactives.", "milieu", "senior_D", 0.80),
    ("Q09", "univers_olfactif", "Préférez-vous des notes florales, boisées ou fruitées ?",
     "Question fermée de la trame générique : le client choisit souvent au hasard.", "milieu", "trame_generique", 0.40),
    ("Q10", "marche", "Dans quels pays le produit sera-t-il lancé en premier, et lesquels suivront ?",
     "Les goûts et la réglementation changent d'un pays à l'autre : mieux vaut le savoir avant de créer.", "milieu", "senior_C", 0.85),
    ("Q11", "marche", "Le produit sera-t-il vendu en grande surface, en pharmacie ou en ligne ?",
     "Le canal de vente fixe le niveau de prix et l'intensité de parfum attendue.", "milieu", "senior_E", 0.70),
    ("Q12", "marche", "Où allez-vous vendre ?",
     "Question de la trame générique : la réponse reste souvent vague.", "milieu", "trame_generique", 0.50),
    ("Q13", "contraintes", "Y a-t-il des ingrédients interdits ou des labels à respecter (vegan, naturel, sans allergènes) ?",
     "Évite de créer une formule qui sera refusée à la fin par le service réglementaire du client.", "milieu", "senior_A", 0.90),
    ("Q14", "contraintes", "Votre service réglementaire a-t-il une liste de restrictions que je peux recevoir ?",
     "Récupère les contraintes écrites au lieu de les deviner.", "fin", "senior_D", 0.80),
    ("Q15", "contraintes", "Avez-vous des contraintes ?",
     "Question de la trame générique : le client répond souvent « non » faute d'y avoir pensé.", "milieu", "trame_generique", 0.35),
    ("Q16", "budget_volume", "Quel prix au kilo visez-vous pour le parfum, et quels volumes annuels prévoyez-vous ?",
     "Fixe tout de suite la contrainte de coût, qui limite les matières premières possibles.", "fin", "senior_B", 0.85),
    ("Q17", "budget_volume", "À quel prix le produit fini sera-t-il vendu en magasin ?",
     "Permet de déduire le budget parfum même quand le client n'ose pas donner un chiffre.", "fin", "senior_E", 0.75),
    ("Q18", "budget_volume", "Quel est votre budget ?",
     "Question de la trame générique : directe, elle braque souvent le client.", "fin", "trame_generique", 0.40),
    ("Q19", "delai", "À quelle date le produit doit-il être en rayon, et quelles validations faut-il avant ?",
     "En partant de la date de lancement, on retrouve la vraie date limite du brief.", "fin", "senior_C", 0.85),
    ("Q20", "delai", "Qui doit valider les échantillons chez vous, et combien de tours prévoyez-vous ?",
     "Révèle les décideurs cachés et évite les allers-retours en fin de projet.", "fin", "senior_A", 0.80),
    ("Q21", "delai", "C'est pour quand ?",
     "Question de la trame générique : donne une date, mais pas les étapes de validation.", "fin", "trame_generique", 0.50),
    ("Q22", "references", "Quel produit du marché se rapproche le plus de ce que vous imaginez, et que voulez-vous faire de différent ?",
     "Une référence concrète vaut mieux que dix adjectifs, et la différence montre l'ambition du client.", "milieu", "senior_D", 0.90),
    ("Q23", "references", "Quels produits concurrents voulez-vous dépasser ?",
     "Situe le niveau d'exigence du client face à la concurrence.", "milieu", "senior_E", 0.70),
    ("Q24", "references", "Avez-vous des références ?",
     "Question de la trame générique : le client n'a souvent rien préparé.", "milieu", "trame_generique", 0.45),
]

NOMS_CLIENTS = ["Calyra", "Brumelle", "Ondevia", "Savonnerie Ardel", "Pétrelia", "Lumiokid", "Ysalis",
                "Vétivora", "Clairhyg", "Néroline", "Boréalys", "Sablenoir", "Mistraline", "Verdeau",
                "Aubeline", "Corolys", "Fennelia", "Glaciane", "Hibiscane", "Iridelle", "Jasmora",
                "Kalyane", "Lavandys", "Myrtelle", "Nacrine", "Opaline Home", "Pivoinea", "Quartzia",
                "Rosalie Care", "Santalys"]
SECTEURS = ["parfum_fin", "soin_corps", "capillaire", "hygiene", "entretien_maison"]
TAILLES = ["multinationale", "regionale", "locale"]
PAYS = ["France", "Belgique", "Maroc", "Allemagne", "Espagne", "Canada", "Royaume-Uni", "Italie"]

VALEURS = {
    "type_produit": {
        "parfum_fin": ["Eau de parfum 50 ml en spray", "Eau de toilette unisexe, extension de gamme"],
        "soin_corps": ["Crème corps hydratante", "Huile sèche pour le corps"],
        "capillaire": ["Shampoing doux usage quotidien", "Après-shampoing réparateur"],
        "hygiene": ["Gel douche surgras", "Savon solide"],
        "entretien_maison": ["Lessive liquide concentrée", "Spray d'intérieur"],
    },
    "cible": ["Femmes 25-40 ans, urbaines, sensibles au naturel", "Familles avec jeunes enfants",
              "Hommes 30-50 ans, gamme premium", "Adolescents 13-18 ans", "Seniors attentifs à la peau sensible"],
    "univers_olfactif": ["Frais et propre, comme du linge au soleil", "Chaleureux et enveloppant, notes ambrées",
                         "Floral lumineux, fleur blanche", "Agrumes énergisants", "Boisé sec et élégant"],
    "marche": ["France puis Benelux, grande surface", "Europe de l'Ouest, en ligne", "Maroc et Afrique du Nord, pharmacie",
               "Amérique du Nord, grande surface", "France, parfumerie sélective"],
    "contraintes": ["Vegan, sans allergènes à étiqueter", "Ingrédients facilement biodégradables",
                    "Indice d'origine naturelle supérieur à 90 %", "Aucune contrainte particulière",
                    "Liste interne d'ingrédients interdits fournie par le client"],
    "budget_volume": ["Environ 15 €/kg, 200 t par an", "Environ 40 €/kg, 30 t par an", "Environ 120 €/kg, 2 t par an",
                      "Environ 8 €/kg, 500 t par an", "Environ 60 €/kg, 10 t par an"],
    "delai": ["Lancement au printemps 2027, 2 tours de validation", "Lancement en septembre 2027, 3 tours",
              "Lancement fin 2027, validation par le comité marketing", "Lancement urgent, 1 seul tour possible"],
    "references": ["Proche d'un best-seller frais du marché, en plus naturel", "Plus intense que la gamme actuelle",
                   "Se démarquer des concurrents trop sucrés", "Reprendre l'esprit du produit phare de la marque"],
}


def main() -> None:
    rng = random.Random(GRAINE)
    SORTIE.mkdir(exist_ok=True)

    # ----- banque de questions, avec des votes de seniors fictifs -----
    lignes_q = []
    for qid, rub, texte, pourquoi, moment, auteur, qualite in QUESTIONS:
        votes = 10
        utiles = sum(rng.random() < qualite for _ in range(votes))
        lignes_q.append({"id_question": qid, "rubrique": rub, "texte": texte, "pourquoi": pourquoi,
                         "moment": moment, "auteur": auteur, "votes_utile": utiles,
                         "votes_a_reformuler": votes - utiles})
    questions = pd.DataFrame(lignes_q)
    par_rubrique = {r: [q for q in QUESTIONS if q[1] == r] for r in RUBRIQUES}  # ordre : bonne, moyenne, générique
    qualite = {q[0]: q[6] for q in QUESTIONS}
    rubrique_de = {q[0]: q[1] for q in QUESTIONS}

    # ----- clients -----
    clients = []
    for i, nom in enumerate(NOMS_CLIENTS, start=1):
        clients.append({"id_client": f"C{i:02d}", "nom": nom, "secteur": rng.choice(SECTEURS),
                        "taille": rng.choices(TAILLES, weights=[3, 4, 3])[0], "pays_principal": rng.choice(PAYS)})
    clients_df = pd.DataFrame(clients)

    # ----- rendez-vous simulés -----
    commerciaux = {"junior": ["J01", "J02", "J03", "J04"], "senior": ["S01", "S02", "S03"]}
    poids_choix = {"junior": [0.25, 0.25, 0.50], "senior": [0.55, 0.35, 0.10]}  # bonne, moyenne, générique
    p_poser = {"junior": 0.75, "senior": 0.9}
    debut = date(2026, 1, 5)

    crs, posees, briefs = [], [], []
    id_cr = 0
    for client in clients:
        for _ in range(3):
            id_cr += 1
            cr = f"CR{id_cr:03d}"
            niveau = rng.choices(["junior", "senior"], weights=[6, 4])[0]
            commercial = rng.choice(commerciaux[niveau])
            jour = debut + timedelta(days=rng.randint(0, 290))
            connues = {r for r in RUBRIQUES if rng.random() < (0.6 if r == "type_produit" else 0.3)}
            remplies = set()
            ordre = 0
            for r in RUBRIQUES:
                deja = r in connues
                if deja and not (niveau == "junior" and rng.random() < 0.10):
                    continue  # rubrique déjà connue : en général on ne repose pas la question
                if not deja and rng.random() > p_poser[niveau]:
                    continue  # rubrique oubliée pendant le rendez-vous
                essais = 2 if rng.random() < 0.5 else 1
                for _ in range(essais):
                    q = rng.choices(par_rubrique[r], weights=poids_choix[niveau])[0][0]
                    ordre += 1
                    rempli = 0 if deja or r in remplies else int(rng.random() < qualite[q])
                    if rempli:
                        remplies.add(r)
                    posees.append({"id_cr": cr, "id_question": q, "rubrique": rubrique_de[q], "ordre": ordre,
                                   "rubrique_deja_connue": int(deja), "a_rempli_rubrique": rempli})
                    if r in remplies:
                        break
            manquantes = [r for r in RUBRIQUES if r not in connues and r not in remplies]
            allers_retours = len(manquantes) + int(rng.random() < 0.15)
            crs.append({"id_cr": cr, "id_client": client["id_client"], "date": jour.isoformat(),
                        "commercial": commercial, "niveau": niveau,
                        "rubriques_connues_avant": ";".join(sorted(connues)),
                        "nb_questions_posees": ordre,
                        "rubriques_remplies": ";".join(r for r in RUBRIQUES if r in remplies),
                        "rubriques_manquantes": ";".join(manquantes),
                        "brief_complet": int(not manquantes),
                        "nb_allers_retours_creatifs": allers_retours})
            brief = {"id_brief": f"B{id_cr:03d}", "id_cr": cr, "id_client": client["id_client"]}
            for r in RUBRIQUES:
                if r in connues or r in remplies:
                    choix = VALEURS[r][client["secteur"]] if r == "type_produit" else VALEURS[r]
                    brief[r] = rng.choice(choix)
                else:
                    brief[r] = ""
            brief["statut"] = "complet" if not manquantes else "incomplet"
            briefs.append(brief)

    questions.to_csv(SORTIE / "questions.csv", index=False)
    clients_df.to_csv(SORTIE / "clients.csv", index=False)
    pd.DataFrame(crs).sort_values("date").to_csv(SORTIE / "comptes_rendus.csv", index=False)
    pd.DataFrame(posees).to_csv(SORTIE / "questions_posees.csv", index=False)
    pd.DataFrame(briefs).to_csv(SORTIE / "briefs.csv", index=False)
    (SORTIE / "parametres_simulation.json").write_text(json.dumps({
        "graine": GRAINE,
        "qualite_cachee_par_question": qualite,
        "probabilite_rubrique_connue_avant": {"type_produit": 0.6, "autres": 0.3},
        "probabilite_de_poser_une_question": p_poser,
        "choix_bonne_moyenne_generique": poids_choix,
        "avertissement": "Données fictives. La qualité des questions est fixée à la main.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(clients_df)} clients, {len(questions)} questions, {len(crs)} comptes rendus, "
          f"{len(posees)} questions posées -> {SORTIE}")


if __name__ == "__main__":
    main()
