# Inventaire des sources — piste « Questions qui débloquent les briefs »

*Livrable étape 1 — Hackathon HETIC × Givaudan — mis à jour le 10/11/2026.*

## 1. Ce qu'on veut produire

**Avant un rendez-vous**, le commercial junior (Key Account Manager) reçoit **3 questions à poser**, tirées d'une
banque de questions qui **ont déjà débloqué des briefs** chez des clients comparables, avec **pourquoi elles marchent**.
Les commerciaux seniors **valident (ou rejettent) une question en 1 clic** : la banque s'améliore avec l'usage.

- **Pourquoi** : renforcer la performance commerciale (connaissance client, anticipation des besoins, détection
  d'opportunités) tout en allégeant la charge de travail.
- **Qui** : le commercial junior (KAM) ; les seniors comme contributeurs.
- **Comment (hypothèse)** : il pose systématiquement les questions essentielles pendant le rendez-vous.
- **Priorité** : clients **Parfums (Fragrance & Beauty)** d'abord, Arômes (Taste & Wellbeing) ensuite.

Pour choisir les bonnes questions, il faut trois familles de données :

| Famille | À quoi elle sert | Disponible en public ? |
|---|---|---|
| **A. Profil du client** (secteur, taille, âge, région, engagements RSE) | Trouver des clients « comparables » | Oui (SIRENE), pour **calibrer** des clients fictifs |
| **B. Ce qu'il vend** (catégories, part de produits parfumés/aromatisés, allergènes, naturalité) | Rendre la question pertinente pour son portefeuille | Oui (Open Beauty / Food Facts), pour **calibrer** |
| **C. Questions et résultats** (questions posées en RDV, brief obtenu ou non, validation des seniors) | Savoir quelles questions « débloquent » | **Non** (CRM Givaudan) → synthétique |

**Noms fictifs partout** : Givaudan ne publie pas le nom de ses clients. Dans l'échantillon, l'API et la démo, tous
les clients portent un nom fictif. Les données publiques servent uniquement à rendre réalistes les **répartitions**
(secteurs, tailles, catégories de produits), jamais à nommer un client.

## 2. Tableau d'inventaire

Statut : ✅ confirmé (testé, échantillon récupéré) · 🟡 à confirmer · ⛔ bloqué

| # | Donnée nécessaire | Source | Méthode d'accès | Licence | Statut | Format | Qualité attendue | Alternative |
|---|---|---|---|---|---|---|---|---|
| 1 | **Profil entreprise** (pour calibrer) : NAF, effectif, catégorie PME/ETI/GE, date de création, région | API Recherche d'entreprises (DINUM) — SIRENE (INSEE) + RNE (INPI) | API REST sans clé, ~3 req/s (limite 7/s), `scripts/fetch_entreprises.py` | Licence Ouverte 2.0 | ✅ 1 529 entreprises | JSON → CSV | Très bonne (≥ 99 % rempli) | Fichier stock SIRENE sur data.gouv.fr |
| 2 | **Finances** : CA, résultat net | Même API (`finances`) | Idem | Licence Ouverte 2.0 | ✅ partiel | CSV | CA exploitable 54 % seulement | Tranche d'effectif comme proxy de taille |
| 3 | **Signaux RSE** : bio, ESS, société à mission, bilan GES, Egapro renseignés | Même API (`complements`) | Idem | Licence Ouverte 2.0 | ✅ | Booléens | 100 % rempli (« renseigné » ≠ « bon score ») | — |
| 4 | **Nomenclatures** NAF, tranches, régions | INSEE | Tables intégrées aux scripts | Licence Ouverte 2.0 | ✅ | Dictionnaires | Parfaite | ⚠️ NAF 2025 arrive (`naf25` gardé) |
| 5 | **Portefeuille beauté** (prioritaire) : catégories, présence de parfum, 26 allergènes de parfum UE | Open Beauty Facts — export Parquet officiel (Hugging Face) | Téléchargement complet (67 Mo), révision figée `12a54ce2` | ODbL 1.0 / DbCL | ✅ 21 333 produits FR | Parquet → CSV | Ingrédients 32 %, catégories 38 %, marque 62 % | — |
| 6 | **Portefeuille alimentaire** : catégories, arômes (naturels ou non), Nutri-Score | Open Food Facts — export Parquet officiel | Lecture partielle HTTP Range (60 blocs, graine 42), même révision | ODbL 1.0 / DbCL | ✅ 20 385 produits FR | Parquet → CSV | Ingrédients 32 %, Nutri-Score réel 41 % | Export CSV complet (9 Go). API OFF interdite aux robots → non utilisée |
| 7 | **Marques de distributeur** (catégorie de client) | Open Facts (Auchan, Carrefour, Cosmia… très présentes) | Dérivé de 5/6 | ODbL | ✅ | — | Bonne | On garde la **catégorie** « marque de distributeur », avec des **noms fictifs** |
| 8 | **Contexte réglementaire et tendances** utiles aux questions (allergènes de parfum, naturalité, clean label, réduction du sucre) | Open Facts (évolution labels/ingrédients) + textes réglementaires UE (EUR-Lex, réutilisation autorisée) | Dérivé + lecture manuelle | ODbL / réutilisation EUR-Lex | 🟡 | Texte court / agrégats | Biais des campagnes de contribution | Résumés synthétiques sourcés |
| 9 | **Offre Givaudan** (Fragrance & Beauty, Taste & Wellbeing) | Rapport annuel public | Lecture manuelle, résumé | Tous droits réservés → citation courte | 🟡 | Texte | Bonne | Description générique |
| 10 | **Banque de questions** posées en RDV, avec catégorie (besoin, budget, calendrier, réglementation, concurrence…) | Pratiques des commerciaux Givaudan | — | Confidentiel | ⛔ | — | — | **Synthétique** : questions rédigées et étiquetées, « pourquoi elle marche » en une phrase |
| 11 | **Résultats** : question posée → brief obtenu ou non, par type de client | CRM Givaudan | — | Confidentiel | ⛔ | — | — | **Synthétique**, graine fixe : taux de déblocage par question × segment |
| 12 | **Validations des seniors** (1 clic : valider / rejeter) | Usage de l'outil | Endpoint `POST /feedback` | — | 🟡 créée par l'outil | JSON | — | Validations simulées pour la démo |
| 13 | **Contacts chez le client** (nom, poste, e-mail, LinkedIn) | — | — | — | ⛔ **interdit (RGPD)** | — | — | Rôles sans nom (« Directeur·rice R&D », « Acheteur·se ») |
| 14 | **Dirigeants** (renvoyés par l'API) | API Recherche d'entreprises | — | — | ⛔ **supprimés à l'import** | — | — | Aucune |
| 15 | **Noms des clients de Givaudan** | Non publics | — | — | ⛔ | — | — | **Noms fictifs** partout |

## 3. Choix RGPD et éthiques appliqués à l'import

- **Dirigeants** : champ jeté avant toute écriture sur disque.
- **Entrepreneurs individuels** (nature juridique 1xxx) exclus : leur raison sociale est un nom de personne (13 cas).
- **Opposition à la prospection** : 1 272 entreprises sur 2 814 (45 %) ont refusé l'usage commercial de leurs données
  (`opposition_diffusion_commerciale`) → exclues. Biais assumé, par respect de leur choix.
- **Open Food/Beauty Facts** : pseudos de contributeurs jamais lus ; `owner` réduit à un booléen.
- **Aucun vrai nom de client** dans l'échantillon, l'API ou la démo : les noms sont fictifs, les répartitions sont réelles.

## 4. Données synthétiques prévues (après la Gate 1)

Graine fixe `42`, documentées dans un `.meta.json` et `docs/synthetique.md`.

| Jeu | Contenu | Comment c'est réaliste |
|---|---|---|
| `clients_fictifs` | Clients **Fragrance & Beauty en priorité**, puis Taste & Wellbeing ; catégorie « marque de distributeur » incluse | Secteur, taille, région, RSE tirés des fréquences de `entreprises_v0` ; portefeuille tiré des statistiques Open Beauty/Food Facts du secteur ; noms fictifs |
| `questions` | Banque de questions étiquetées + « pourquoi elle marche » | Rédigées à partir du vocabulaire métier (briefs, allergènes, naturalité, coûts, calendrier de lancement) |
| `rendez_vous` (CRM réduit) | Questions posées, brief obtenu ou non | Taux de déblocage différent selon question × segment. Le gros CRM de 1 000 interactions est reporté. |

Limite à dire au jury : sur des données qu'on a générées, le moteur retrouve forcément nos règles. Le synthétique
démontre la chaîne de bout en bout ; la vraie valeur se mesurerait sur le CRM Givaudan.

## 5. Échantillon v0 récupéré

| Fichier | Lignes | Source | Méta |
|---|---|---|---|
| `data/raw/entreprises_v0.csv` | 1 529 | API Recherche d'entreprises, 45 codes NAF (10.xx, 11.xx, 20.42Z), actives, ≥ 10 salariés, max 50 par code | `.meta.json` |
| `data/raw/off_food_fr_v0.csv` | 20 385 | Open Food Facts, 60 blocs / 4 790, vendus en France | `.meta.json` |
| `data/raw/obf_beauty_fr_v0.csv` | 21 333 | Open Beauty Facts, fichier complet, vendus en France | `.meta.json` |

`entreprises_v0.csv` contient des raisons sociales réelles (données publiques SIRENE) : il sert **uniquement à calculer
des répartitions** et n'est jamais exposé par l'API ni la démo.

Qualité, doublons, langues et biais : [quality_report.md](quality_report.md).

## 6. Reproduire

```bash
cd data-brique
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/fetch_entreprises.py  # ~1 min
python scripts/fetch_open_facts.py   # 1er lancement ~170 Mo, puis cache
python scripts/quality_report.py
```

Open Facts est figé au commit Hugging Face `12a54ce27f7166bad0d8947e2ebeb258cec157c1` (relance identique) ;
SIRENE est mis à jour chaque jour → le CSV v0 versionné fait foi.

## 7. Questions ouvertes

1. Liste des catégories de questions à valider avec Product (besoin, budget, calendrier, réglementation, concurrence, durabilité…).
2. Définition de « débloquer un brief » (brief reçu dans les N semaines après le RDV ?).
3. Règle de validation des seniors : combien de validations pour qu'une question entre dans la banque ?
