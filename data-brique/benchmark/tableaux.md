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

| modèle            | testé sur                 | rubrique rang 1   | question rang 1   | question top 3   | question top 5   | MRR   | temps / requête (ms)   | indexation banque (s)   |
|:------------------|:--------------------------|:------------------|:------------------|:-----------------|:-----------------|:------|:-----------------------|:------------------------|
| tfidf             | pc_principal              | 40 %              | 33 %              | 47 %             | 53 %             | 0.443 | 0.1                    |                         |
| nomic-embed-text  | pc_principal              | 53 %              | 47 %              | 60 %             | 73 %             | 0.559 | 128.1                  | 2.44                    |
| all-minilm        | pc_principal              | 73 %              | 67 %              | 80 %             | 87 %             | 0.759 | 26.4                   | 0.8                     |
| bge-m3            | pc_principal              | 93 %              | 93 %              | 100 %            | 100 %            | 0.956 | 152.1                  | 10.37                   |
| mxbai-embed-large | à remplir (PC coéquipier) |                   |                   |                  |                  |       |                        |                         |

## Extraction JSON des rubriques connues (15 notes)

| modèle       | testé sur                 | JSON valide   | F1 brut   | F1 garde-fou   | notes exactes (garde-fou)   | notes avec rubrique inventée (brut)   | notes avec rubrique inventée (garde-fou)   | temps / note moy. (s)   | temps / note max (s)   |
|:-------------|:--------------------------|:--------------|:----------|:---------------|:----------------------------|:--------------------------------------|:-------------------------------------------|:------------------------|:-----------------------|
| qwen2.5:1.5b | pc_principal              | 100 %         | 0.591     | 0.722          | 7 %                         | 100 %                                 | 87 %                                       | 8.25                    | 11.42                  |
| qwen2.5:0.5b | pc_principal              | 73 %          | 0.34      | 0.409          | 7 %                         | 73 %                                  | 47 %                                       | 6.72                    | 12.51                  |
| qwen2.5:3b   | pc_principal              | 93 %          | 0.521     | 0.805          | 47 %                        | 93 %                                  | 20 %                                       | 24.54                   | 62.14                  |
| llama3.2:3b  | à remplir (PC coéquipier) |               |           |                |                             |                                       |                                            |                         |                        |

Détail cas par cas (sorties brutes des modèles) : `benchmark/runs/<pc>.json`.
