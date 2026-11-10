# Premier résultat Data — G03 (données fictives)

Données : 90 comptes rendus fictifs, 469 questions posées, 24 questions en banque.
Apprentissage sur 62 comptes rendus, test sur 28 gardés de côté.

## Résultat principal

Pour les mêmes rubriques vides, les 3 questions choisies par le moteur remplissent en moyenne
**2.39 rubriques sur 3**, contre **1.17** avec la trame générique
et **1.82** au hasard, soit **+104 %** par rapport à la trame générique
et **+31 %** par rapport au hasard (mesuré sur les rendez-vous test).

Taux de réussite observé sur la partie test : questions classées n°1 par le moteur **90%**
(48 fois posées), questions de la trame générique **41%** (51 fois posées).

## Exemples : les 3 questions proposées

**Brumelle (C02, fictif)** : secteur capillaire, client multinationale, Canada. Déjà connu : Type de produit et forme.

| Question | Rubrique | Pourquoi | Score |
| --- | --- | --- | --- |
| Quel produit du marché se rapproche le plus de ce que vous imaginez, et que voulez-vous faire de différent ? | Références et concurrents | Une référence concrète vaut mieux que dix adjectifs, et la différence montre l'ambition du client. | 0.82 |
| Quelle émotion voulez-vous que le consommateur ressente quand il ouvre le produit ? | Univers olfactif et émotion | Fait parler le client en images plutôt qu'en termes techniques qu'il ne maîtrise pas. | 0.692 |
| Quel prix au kilo visez-vous pour le parfum, et quels volumes annuels prévoyez-vous ? | Budget et volumes | Fixe tout de suite la contrainte de coût, qui limite les matières premières possibles. | 0.798 |

**Boréalys (C11, fictif)** : secteur entretien_maison, client multinationale, Belgique. Déjà connu : Type de produit et forme, Cible consommateur, Budget et volumes.

| Question | Rubrique | Pourquoi | Score |
| --- | --- | --- | --- |
| Quel produit du marché se rapproche le plus de ce que vous imaginez, et que voulez-vous faire de différent ? | Références et concurrents | Une référence concrète vaut mieux que dix adjectifs, et la différence montre l'ambition du client. | 0.82 |
| Quelle émotion voulez-vous que le consommateur ressente quand il ouvre le produit ? | Univers olfactif et émotion | Fait parler le client en images plutôt qu'en termes techniques qu'il ne maîtrise pas. | 0.692 |
| Dans quels pays le produit sera-t-il lancé en premier, et lesquels suivront ? | Marché, pays et canal | Les goûts et la réglementation changent d'un pays à l'autre : mieux vaut le savoir avant de créer. | 0.769 |

**Nacrine (C25, fictif)** : secteur parfum_fin, client locale, Allemagne. Déjà connu : Type de produit et forme, Marché, pays et canal, Délai et étapes de validation.

| Question | Rubrique | Pourquoi | Score |
| --- | --- | --- | --- |
| Quel produit du marché se rapproche le plus de ce que vous imaginez, et que voulez-vous faire de différent ? | Références et concurrents | Une référence concrète vaut mieux que dix adjectifs, et la différence montre l'ambition du client. | 0.82 |
| Quelle émotion voulez-vous que le consommateur ressente quand il ouvre le produit ? | Univers olfactif et émotion | Fait parler le client en images plutôt qu'en termes techniques qu'il ne maîtrise pas. | 0.692 |
| Quel prix au kilo visez-vous pour le parfum, et quels volumes annuels prévoyez-vous ? | Budget et volumes | Fixe tout de suite la contrainte de coût, qui limite les matières premières possibles. | 0.798 |

## Constat sur les comptes rendus : juniors et seniors

| niveau | rendez_vous | briefs_complets | allers_retours | questions_posees |
| --- | --- | --- | --- | --- |
| junior | 56 | 0.05 | 2.38 | 5.3 |
| senior | 34 | 0.24 | 1.68 | 5.06 |

Attention : cet écart vient des paramètres de la simulation (les juniors y choisissent plus souvent la trame générique).
Il illustre le problème, mais ce n'est pas un constat réel.

## Priorité des rubriques (part des rendez-vous où la rubrique est restée vide)

| rubrique | part_manquante |
| --- | --- |
| references | 0.44 |
| univers_olfactif | 0.34 |
| budget_volume | 0.27 |
| marche | 0.26 |
| delai | 0.26 |
| cible | 0.18 |
| contraintes | 0.16 |
| type_produit | 0.13 |

## Scores de toutes les questions

| id_question | rubrique | auteur | posees | score_donnees | score_seniors | score_total |
| --- | --- | --- | --- | --- | --- | --- |
| Q13 | contraintes | senior_A | 18 | 0.9 | 0.83 | 0.88 |
| Q04 | cible | senior_C | 18 | 0.9 | 0.75 | 0.86 |
| Q02 | type_produit | senior_B | 9 | 0.82 | 0.83 | 0.82 |
| Q22 | references | senior_D | 18 | 0.85 | 0.75 | 0.82 |
| Q01 | type_produit | senior_A | 6 | 0.75 | 0.92 | 0.8 |
| Q16 | budget_volume | senior_B | 21 | 0.78 | 0.83 | 0.8 |
| Q20 | delai | senior_A | 14 | 0.88 | 0.58 | 0.79 |
| Q10 | marche | senior_C | 14 | 0.81 | 0.67 | 0.77 |
| Q14 | contraintes | senior_D | 13 | 0.73 | 0.75 | 0.74 |
| Q05 | cible | senior_A | 12 | 0.64 | 0.83 | 0.7 |
| Q07 | univers_olfactif | senior_B | 17 | 0.63 | 0.83 | 0.69 |
| Q08 | univers_olfactif | senior_D | 11 | 0.69 | 0.67 | 0.68 |
| Q17 | budget_volume | senior_E | 9 | 0.64 | 0.75 | 0.67 |
| Q19 | delai | senior_C | 11 | 0.62 | 0.75 | 0.66 |
| Q03 | type_produit | trame_generique | 4 | 0.67 | 0.5 | 0.62 |
| Q11 | marche | senior_E | 11 | 0.54 | 0.75 | 0.6 |
| Q15 | contraintes | trame_generique | 7 | 0.67 | 0.42 | 0.59 |
| Q18 | budget_volume | trame_generique | 5 | 0.71 | 0.25 | 0.57 |
| Q06 | cible | trame_generique | 15 | 0.53 | 0.58 | 0.55 |
| Q21 | delai | trame_generique | 14 | 0.44 | 0.58 | 0.48 |
| Q24 | references | trame_generique | 14 | 0.44 | 0.5 | 0.46 |
| Q12 | marche | trame_generique | 15 | 0.41 | 0.42 | 0.41 |
| Q09 | univers_olfactif | trame_generique | 15 | 0.24 | 0.5 | 0.31 |
| Q23 | references | senior_E | 5 | 0.14 | 0.58 | 0.28 |

## Limites, à dire au jury

- Les données sont fictives. La « qualité » de chaque question a été fixée dans le script de génération,
  et le moteur la retrouve (corrélation de Spearman entre score appris et qualité cachée : 0.61).
  Cela prouve que la chaîne fonctionne, pas que ces questions marchent dans la réalité.
- La preuve réelle viendra de vrais commerciaux : relecture des questions, votes des seniors,
  puis mesure des allers-retours avec les créatifs.
- Certaines questions ont été peu posées : leur score est encore incertain (lissage de Laplace pour limiter l'effet).
