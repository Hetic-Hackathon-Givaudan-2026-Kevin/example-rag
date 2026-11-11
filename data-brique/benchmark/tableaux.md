# Tableaux du benchmark (générés par `run_benchmark.py --rapport`)

## Configuration des PC

|                         | pc_principal                                      |
|:------------------------|:--------------------------------------------------|
| os                      | Windows 10                                        |
| cpu                     | AMD64 Family 23 Model 96 Stepping 1, AuthenticAMD |
| coeurs_logiques         | 12                                                |
| ram_totale_go           | 15.3                                              |
| ram_libre_go            | 1.9                                               |
| disque_systeme_libre_go | 1.6                                               |
| disque_systeme_total_go | 237.4                                             |
| ollama                  | 0.40.16                                           |
| python                  | 3.11.9                                            |
| date                    | 2026-11-11T13:07:54                               |

## Recherche de la bonne question (15 cas)

| pc           | modele           |   rubrique_rang1 |   question_rang1 |   question_top3 |   question_top5 |   mrr |   temps_moyen_ms | indexation_banque_s   |
|:-------------|:-----------------|-----------------:|-----------------:|----------------:|----------------:|------:|-----------------:|:----------------------|
| pc_principal | tfidf            |            0.4   |            0.333 |           0.467 |           0.533 | 0.443 |              0.1 |                       |
| pc_principal | nomic-embed-text |            0.533 |            0.467 |           0.6   |           0.733 | 0.559 |            128.1 | 2.44                  |
| pc_principal | all-minilm       |            0.733 |            0.667 |           0.8   |           0.867 | 0.759 |             26.4 | 0.8                   |
| pc_principal | bge-m3           |            0.933 |            0.933 |           1     |           1     | 0.956 |            152.1 | 10.37                 |

## Extraction JSON des rubriques connues (15 notes)

| pc           | modele       |   json_valide |   precision |   rappel |    f1 |   cas_exacts |   notes_avec_rubrique_inventee |   notes_avec_valeur_inventee |   f1_garde_fou |   precision_garde_fou |   rappel_garde_fou |   cas_exacts_garde_fou |   notes_avec_rubrique_inventee_garde_fou |   temps_moyen_s |   temps_max_s |   tokens_par_s |   chargement_s |
|:-------------|:-------------|--------------:|------------:|---------:|------:|-------------:|-------------------------------:|-----------------------------:|---------------:|----------------------:|-------------------:|-----------------------:|-----------------------------------------:|----------------:|--------------:|---------------:|---------------:|
| pc_principal | qwen2.5:1.5b |         1     |       0.435 |    0.92  | 0.591 |            0 |                          1     |                        0.6   |          0.722 |                 0.623 |              0.859 |                  0.067 |                                    0.867 |            8.25 |         11.42 |           15.7 |           11.7 |
| pc_principal | qwen2.5:0.5b |         0.733 |       0.229 |    0.667 | 0.34  |            0 |                          0.733 |                        0.6   |          0.409 |                 0.361 |              0.473 |                  0.067 |                                    0.467 |            6.72 |         12.51 |           34.2 |            5.2 |
| pc_principal | qwen2.5:3b   |         0.933 |       0.392 |    0.778 | 0.521 |            0 |                          0.933 |                        0.933 |          0.805 |                 0.833 |              0.779 |                  0.467 |                                    0.2   |           24.54 |         62.14 |            6.8 |           20.7 |
