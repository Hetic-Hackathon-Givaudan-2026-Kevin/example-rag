# Rapport qualité — échantillon v0 (données réelles brutes)

*Généré par `scripts/quality_report.py` le 2026-11-10T14:30:45+00:00. Relançable : les chiffres viennent des fichiers de `data/raw/`.*

Légende : **rempli %** = cellule non vide ; **utile %** = non vide ET pas une valeur bouche-trou (`unknown`, `not-applicable`, chiffre d'affaires = 0).

## 1. Vue d'ensemble

| jeu              | source                         | licence             |   lignes |   colonnes | clé   |   doublons_clé |
|:-----------------|:-------------------------------|:--------------------|---------:|-----------:|:------|---------------:|
| entreprises_v0   | API Recherche d'entreprises    | Licence Ouverte 2.0 |     1529 |         28 | siren |              0 |
| off_food_fr_v0   | Open Food Facts (Parquet HF)   | ODbL                |    20385 |         19 | code  |              0 |
| obf_beauty_fr_v0 | Open Beauty Facts (Parquet HF) | ODbL                |    21333 |         17 | code  |              0 |

## 2. Entreprises (SIRENE via API Recherche d'entreprises)

- 137 requêtes, 2814 entreprises reçues, **1529 gardées**.
- Exclues : 13 entrepreneurs individuels (RGPD), **1272 (45%) pour opposition à la prospection commerciale ou diffusion partielle**.
- Le champ `dirigeants` a été supprimé à l'import (jamais écrit sur disque).

### Taux de remplissage

|                           |   rempli_% |   utile_% |
|:--------------------------|-----------:|----------:|
| sigle                     |       10.2 |      10.2 |
| enseignes                 |       14.2 |      14.2 |
| chiffre_affaires          |       90.8 |      54   |
| resultat_net              |       90.8 |      88.4 |
| annee_finances            |       90.8 |      90.8 |
| siege_longitude           |       99   |      99   |
| siege_latitude            |       99   |      99   |
| categorie_entreprise      |       99.9 |      99.9 |
| siege_commune             |       99.9 |      99.9 |
| siege_departement         |       99.9 |      99.9 |
| siege_region              |       99.9 |      99.9 |
| siege_code_postal         |       99.9 |      99.9 |
| naf25                     |      100   |     100   |
| naf                       |      100   |     100   |
| siren                     |      100   |     100   |
| raison_sociale            |      100   |     100   |
| nature_juridique          |      100   |     100   |
| nb_etablissements_ouverts |      100   |     100   |
| annee_tranche_effectif    |      100   |     100   |
| date_creation             |      100   |     100   |
| tranche_effectif_libelle  |      100   |     100   |
| tranche_effectif          |      100   |     100   |
| naf_libelle               |      100   |     100   |
| est_bio                   |      100   |     100   |
| est_ess                   |      100   |     100   |
| est_societe_mission       |      100   |     100   |
| egapro_renseignee         |      100   |     100   |
| bilan_ges_renseigne       |      100   |     100   |

> Le chiffre d'affaires est présent à 91% mais vaut 0 dans 563 cas (comptes confidentiels ou non publiés) : seulement 54% de CA exploitables. Années des comptes : 2024 (565), 2025 (507), 2023 (132), 2022 (39).

### Distributions (pour repérer les biais)

**Catégorie d'entreprise**

| categorie_entreprise   |    % |
|:-----------------------|-----:|
| PME                    | 64.2 |
| ETI                    | 25.6 |
| GE                     | 10.1 |
| (vide)                 |  0.1 |

**Tranche d'effectif salarié**

| tranche_effectif_libelle   |    % |
|:---------------------------|-----:|
| 10 à 19                    | 34.5 |
| 20 à 49                    | 32.8 |
| 50 à 99                    | 13.5 |
| 100 à 199                  |  8.8 |
| 250 à 499                  |  4.3 |
| 200 à 249                  |  2.4 |
| 500 à 999                  |  2.3 |
| 1 000 à 1 999              |  1   |
| 2 000 à 4 999              |  0.5 |

**Nombre d'entreprises par code NAF** (plafond 50 par code)

|                                                                                  |   n |
|:---------------------------------------------------------------------------------|----:|
| ('10.11Z', 'Transformation et conservation de la viande de boucherie')           |  50 |
| ('10.12Z', 'Transformation et conservation de la viande de volaille')            |  50 |
| ('10.13A', 'Préparation industrielle de produits à base de viande')              |  50 |
| ('10.13B', 'Charcuterie')                                                        |  50 |
| ('10.20Z', 'Transformation et conservation de poisson, crustacés et mollusques') |  50 |
| ('10.39B', 'Transformation et conservation de fruits')                           |  50 |
| ('10.39A', 'Autre transformation et conservation de légumes')                    |  50 |
| ('10.71D', 'Pâtisserie')                                                         |  50 |
| ('10.72Z', 'Fabrication de biscuits, biscottes et pâtisseries de conservation')  |  50 |
| ('10.82Z', 'Fabrication de cacao, chocolat et produits de confiserie')           |  50 |
| ('10.71A', 'Fabrication industrielle de pain et de pâtisserie fraîche')          |  50 |
| ('10.61A', 'Meunerie')                                                           |  50 |
| ('10.51C', 'Fabrication de fromage')                                             |  50 |
| ('10.91Z', "Fabrication d'aliments pour animaux de ferme")                       |  50 |
| ('11.02B', 'Vinification')                                                       |  50 |
| ('20.42Z', 'Fabrication de parfums et de produits pour la toilette')             |  50 |
| ('11.05Z', 'Fabrication de bière')                                               |  50 |
| ('10.89Z', "Fabrication d'autres produits alimentaires n.c.a.")                  |  50 |
| ('11.01Z', 'Production de boissons alcooliques distillées')                      |  50 |
| ('10.71C', 'Boulangerie et boulangerie-pâtisserie')                              |  50 |
| ('10.71B', 'Cuisson de produits de boulangerie')                                 |  50 |
| ('10.85Z', 'Fabrication de plats préparés')                                      |  50 |
| ('10.83Z', 'Transformation du thé et du café')                                   |  46 |
| ('11.02A', 'Fabrication de vins effervescents')                                  |  46 |
| ('10.51A', 'Fabrication de lait liquide et de produits frais')                   |  44 |
| ('10.52Z', 'Fabrication de glaces et sorbets')                                   |  42 |
| ('11.07A', 'Industrie des eaux de table')                                        |  37 |
| ('10.84Z', 'Fabrication de condiments et assaisonnements')                       |  30 |
| ('10.86Z', "Fabrication d'aliments homogénéisés et diététiques")                 |  29 |
| ('11.07B', 'Production de boissons rafraîchissantes')                            |  28 |
| ('10.73Z', 'Fabrication de pâtes alimentaires')                                  |  23 |
| ('10.92Z', "Fabrication d'aliments pour animaux de compagnie")                   |  18 |
| ('10.61B', 'Autres activités du travail des grains')                             |  14 |
| ('10.51D', "Fabrication d'autres produits laitiers")                             |  14 |
| ('10.32Z', 'Préparation de jus de fruits et légumes')                            |  12 |
| ('10.31Z', 'Transformation et conservation de pommes de terre')                  |  10 |
| ('10.41A', "Fabrication d'huiles et graisses brutes")                            |   8 |
| ('10.51B', 'Fabrication de beurre')                                              |   6 |
| ('10.41B', "Fabrication d'huiles et graisses raffinées")                         |   5 |
| ('10.81Z', 'Fabrication de sucre')                                               |   5 |
| ('11.03Z', 'Fabrication de cidre et de vins de fruits')                          |   4 |
| ('11.04Z', "Production d'autres boissons fermentées non distillées")             |   3 |
| ('10.62Z', 'Fabrication de produits amylacés')                                   |   2 |
| ('11.06Z', 'Fabrication de malt')                                                |   2 |
| ('10.42Z', 'Fabrication de margarine et graisses comestibles similaires')        |   1 |

**Région du siège (top 8)**

| siege_region               |    % |
|:---------------------------|-----:|
| Nouvelle-Aquitaine         | 11.5 |
| Auvergne-Rhône-Alpes       | 11.4 |
| Occitanie                  | 11.2 |
| Île-de-France              |  9.8 |
| Bretagne                   |  8.9 |
| Grand Est                  |  8.5 |
| Hauts-de-France            |  7.5 |
| Provence-Alpes-Côte d'Azur |  6.8 |

**Année de création** : médiane 1995, 25 % avant 1981, 25 % après 2008.

## 3. Open Food Facts (alimentaire)

- Échantillon : 60 row groups sur 4790, tirés avec random.Random(42) -> 61440 produits lus (6.9 Mo téléchargés), **20385 vendus en France**.
- Révision figée : `12a54ce27f7166bad0d8947e2ebeb258cec157c1`.

### Taux de remplissage

|                        |   rempli_% |   utile_% |
|:-----------------------|-----------:|----------:|
| nova_group             |       29.8 |      29.8 |
| ingredients_tags       |       31.7 |      31.7 |
| ingredients_n          |       31.7 |      31.7 |
| nutriscore_grade       |       98.2 |      40.7 |
| labels_tags            |       41.4 |      41.4 |
| brands                 |       53.4 |      53.3 |
| marque_principale      |       53.4 |      53.3 |
| brands_tags            |       53.4 |      53.4 |
| categories_tags        |       54.7 |      54.7 |
| product_name           |       94   |      94   |
| code                   |      100   |     100   |
| countries_tags         |      100   |     100   |
| lang                   |      100   |     100   |
| created_t              |      100   |     100   |
| last_modified_t        |      100   |     100   |
| completeness           |      100   |     100   |
| contient_arome         |      100   |     100   |
| contient_arome_naturel |      100   |     100   |
| fiche_producteur       |      100   |     100   |

### Doublons

- Code-barres en double : 0.
- Même nom + même marque (déclinaisons de format/parfum ou vrais doublons) : **257** (1%). À dédoublonner avant d'agréger par marque.

### Langues (champ `lang` de la fiche)

| lang   |    % |
|:-------|-----:|
| fr     | 89.5 |
| en     |  7.6 |
| de     |  1.1 |
| it     |  0.5 |
| es     |  0.5 |
| nl     |  0.4 |

### Concentration des marques

- 4151 marques distinctes ; les 10 premières = **17%** des produits avec marque.
- Top 10 : auchan (396), maitre-coq (275), findus (273), bjorg (272), carrefour (141), juvamine (124), candia (104), tipiak (95), lidl (94), nestle (93).
- Marques de distributeur visibles dans le top (Auchan, Carrefour, Cosmia…) : ce sont des clients « retail », pas des industriels.

### Indicateurs utiles pour Givaudan

- `contient_arome` : **31%** des produits dont les ingrédients sont connus (6454 produits).
- `contient_arome_naturel` : **20%** des produits dont les ingrédients sont connus (6454 produits).
- Nutri-Score : 41% réellement calculé (le reste = `unknown` / `not-applicable`).
- Fiches fournies par le producteur lui-même : 5% (le reste = contributeurs bénévoles).
- Année de création des fiches : 2012: 63, 2013: 124, 2014: 118, 2015: 348, 2016: 463, 2017: 1519, 2018: 5837, 2019: 4481, 2020: 870, 2021: 2035, 2022: 987, 2023: 551, 2024: 1153, 2025: 816, 2026: 1020.

## 4. Open Beauty Facts (beauté)

- Fichier complet : 80202 produits, **21333 vendus en France**.
- Révision figée : `12a54ce27f7166bad0d8947e2ebeb258cec157c1`.

### Taux de remplissage

|                      |   rempli_% |   utile_% |
|:---------------------|-----------:|----------:|
| labels_tags          |       20   |      20   |
| ingredients_tags     |       31.6 |      31.6 |
| ingredients_n        |       31.6 |      31.6 |
| categories_tags      |       38.4 |      38.4 |
| marque_principale    |       61.8 |      61.8 |
| brands_tags          |       61.9 |      61.9 |
| brands               |       61.9 |      61.9 |
| product_name         |       67.2 |      67.2 |
| completeness         |       76.9 |      76.9 |
| lang                 |      100   |     100   |
| code                 |      100   |     100   |
| countries_tags       |      100   |     100   |
| last_modified_t      |      100   |     100   |
| created_t            |      100   |     100   |
| contient_parfum      |      100   |     100   |
| nb_allergenes_parfum |      100   |     100   |
| fiche_producteur     |      100   |     100   |

### Doublons

- Code-barres en double : 0.
- Même nom + même marque (déclinaisons de format/parfum ou vrais doublons) : **383** (2%). À dédoublonner avant d'agréger par marque.

### Langues (champ `lang` de la fiche)

| lang   |    % |
|:-------|-----:|
| fr     | 86   |
| en     | 10.3 |
| de     |  0.9 |
| nl     |  0.5 |
| es     |  0.5 |
| ar     |  0.5 |

### Concentration des marques

- 3192 marques distinctes ; les 10 premières = **26%** des produits avec marque.
- Top 10 : unilever (599), l-oreal (556), cosmia (424), carrefour (414), yves-rocher (306), henkel (279), axe (240), nivea (203), auchan (194), le-petit-marseillais (156).
- Marques de distributeur visibles dans le top (Auchan, Carrefour, Cosmia…) : ce sont des clients « retail », pas des industriels.

### Indicateurs utiles pour Givaudan

- `contient_parfum` : **66%** des produits dont les ingrédients sont connus (6745 produits).
- Au moins un des 26 allergènes de parfum UE déclaré : 47% des produits avec ingrédients.
- Fiches fournies par le producteur lui-même : 10% (le reste = contributeurs bénévoles).
- Année de création des fiches : 2013: 1, 2014: 112, 2015: 120, 2016: 1572, 2017: 987, 2018: 3447, 2019: 1659, 2020: 1472, 2021: 2133, 2022: 679, 2023: 1214, 2024: 1393, 2025: 3901, 2026: 2643.

## 5. Peut-on relier les produits aux entreprises ?

Test : nom de marque normalisé (sans accents, sans « SAS », « France »…) = raison sociale, sigle ou enseigne.

| jeu    |   produits_relies_% |   marques_reliees |   entreprises_reliees | exemples                                                                      |
|:-------|--------------------:|------------------:|----------------------:|:------------------------------------------------------------------------------|
| food   |                 3.9 |                76 |                    74 | candia, altiflore, fromapac, acapella, charal, panzani                        |
| beauty |                 0.1 |                 9 |                     9 | laboratoirerivadis, europcosmetics, alva, vecteurenergy, comptoirlys, crystal |

> Le lien exact est **faible** : une marque porte rarement le nom légal de la société (ex. une marque grand public appartient souvent à un groupe au nom différent), et l'échantillon d'entreprises est plafonné à 50 par code NAF.

## 6. Biais et limites à retenir

1. **Biais de taille** : l'API renvoie d'abord les entreprises aux plus gros réseaux d'établissements, et on a filtré à ≥ 10 salariés -> les TPE (la majorité des entreprises françaises) sont absentes. Cohérent avec la cible Givaudan (industriels), mais à dire au jury.
2. **Biais d'opposition** : 45% des entreprises reçues refusent la prospection. On les exclut par respect de ce choix : le portrait du marché est donc partiel.
3. **Biais sectoriel** : plafond de 50 par NAF -> les secteurs très peuplés (vin, boulangerie) sont sous-représentés, les petits secteurs (malt, cidre) sur-représentés en proportion. À repondérer si on calcule des parts de marché.
4. **Biais Open Facts** : base collaborative -> sur-représentation des grandes marques et des marques de distributeur, des produits scannés par les bénévoles, et des années de campagnes de contribution (pics 2018-2019 côté food).
5. **Remplissage** : ingrédients connus pour ~1/3 des produits seulement -> les indicateurs « contient un arôme / un parfum » sont calculés sur ce tiers, pas sur tout le catalogue.
6. **Langues** : ~86-90 % des fiches en français, le reste surtout en anglais (produits importés) -> traitement texte à prévoir en FR avec repli EN.
7. **Fraîcheur** : SIRENE à jour (mise à jour quotidienne), comptes financiers souvent de 2024-2025 ; Open Facts figé à la révision du 10/11/2026.
8. **RGPD** : aucune donnée personnelle conservée (dirigeants, entrepreneurs individuels et pseudos de contributeurs exclus à l'import).
