# CLAUDE.md — Brique Data (Hackathon HETIC × Givaudan)

À relire à chaque session. Le travail Data vit dans `data-brique/`. Le reste du dépôt
(`api.py`, `rag.py`, `story.txt`…) est une démo de l'équipe : ne pas y toucher.

## Contexte
- Hackathon HETIC × Givaudan, semaine du 9 au 13 nov. 2026. Sujet 1 : « La relation commerciale à l'ère de l'IA ».
- Givaudan crée des arômes (Flavors) et des parfums (Fragrance) pour des marques (B2B).
- Utilisateur de Claude : étudiant Data. Rôle : construire l'intelligence de la solution
  (données, traitement ou modèle, validation) et l'exposer via une API à l'équipe Tech.

## Impact map (branche choisie)
- **Pourquoi** : renforcer la performance commerciale en améliorant la connaissance client, l'anticipation des besoins et la détection d'opportunités, et en allégeant la charge de travail.
- **Qui** : le commercial junior (Key Account Manager) ; les seniors en contributeurs.
- **Comment (hypothèse)** : il pose systématiquement les questions essentielles pendant le rendez-vous.
- **Quoi** : avant le rendez-vous, le junior reçoit **3 questions** tirées de celles qui ont débloqué des briefs, avec **pourquoi elles marchent** ; les seniors les valident en 1 clic.
- **Pas** de recommandations de canal / ton : ce n'est pas notre piste.
- Priorité clients **Parfums (Fragrance & Beauty)**. Marques de distributeur : catégorie gardée, noms fictifs.
- **Noms de clients toujours fictifs** (échantillon, API, démo) : Givaudan ne publie pas ses clients. Les données publiques ne servent qu'à calibrer les répartitions (secteurs, tailles, catégories).
- Contrat d'API de l'équipe : `GET /sante`, `POST /questions`, `POST /feedback`, `GET /banque` (à garder exactement).

## Règles à respecter partout
- **Sources** : Open Data ou API officielle d'abord ; scraping seulement en dernier recours, après lecture des CGU et du robots.txt, rythme limité. Jamais de contournement de login ou de CAPTCHA.
- **RGPD** : aucune donnée personnelle (pas de LinkedIn, pas de noms ni d'e-mails de personnes, pas de dirigeants). Si une API renvoie des données personnelles, les supprimer à l'import (avant toute écriture sur disque). Exclure les entrepreneurs individuels (leur raison sociale = un nom de personne).
- **Données internes Givaudan** (CRM, comptes rendus, historique client) inaccessibles → données synthétiques réalistes, documentées, reproductibles (graine fixe `SEED = 42`).
- **Traçabilité** : chaque jeu de données a un fichier `.meta.json` (source, URL, date, licence, filtres, volume).
- **Reproductibilité** : scripts relançables, versions figées dans `requirements.txt`, révision des exports figée si possible (ex. hash de commit Hugging Face).
- **Secrets** : aucun token ni clé dans le dépôt (`.env` + `.gitignore`). Ne jamais écrire le token ngrok.
- **Git** : branche `feature/data-brique`. Ne jamais pousser sur `develop` ou `main`. Pas de PR sans accord. Avant chaque commit, montrer le résultat (diff/fichiers) et attendre l'accord.
- **Style** : tutoyer, répondre en français, explications simples (l'étudiant doit pouvoir justifier chaque choix devant le jury).
- **Ollama** : appeler `http://127.0.0.1:11434` (pas `localhost`, lent sous Windows), `temperature 0`, vecteurs en cache.
- **Validation** : ne jamais régler les prompts sur les cas de validation ; cas de test écrits AVANT de régler les prompts.

## Arborescence
```
data-brique/
  data/raw/  data/processed/  scripts/  notebooks/  src/  api/  tests/  benchmark/  docs/
  requirements.txt  .env.example  .gitignore
```

## Planning
| Jour | Étape | Livrables |
|---|---|---|
| Lun 9 | 1. Inventaire des sources | `docs/inventaire_sources.md`, scripts d'échantillon, `docs/quality_report.md` |
| Mar 10 (Gate 1, 16h) | 2. Échantillon + baseline V1 | `data/processed/sample_v1.csv`, `docs/comparaison_v0_v1.md`, `notebooks/baseline_v1.ipynb`, `src/moteur_v1.py`, `api/main.py` (GET /sante + endpoint métier), `tests/`, `docs/contrat_api.md`, explication ngrok |
| Mer 11 | 3. Benchmark Ollama (CPU) | `benchmark/briefs_test.csv` (15 cas), `benchmark/run_benchmark.py`, `benchmark/resultats.md` — embeddings : nomic-embed-text, bge-m3, mxbai-embed-large vs TF-IDF ; LLM : qwen2.5:1.5b, qwen2.5:3b, llama3.2:3b |
| Jeu 12 | 4. V2 | `src/moteur_v2.py` (même sortie que V1, repli auto sur V1 si Ollama absent), `demo_bot.py`, comparaison V1/V2 chiffrée, validation sur 30 cas définis avec Product (critères écrits à l'avance) dans `docs/` |
| Ven 13 | 5. Pitch | procédure de reproduction, comparaison V1/V2, limites et biais, sources citées, 2–3 visualisations |

## État d'avancement
- [x] Étape 1 : inventaire, échantillon v0, rapport qualité (validé le 10/11)
- [~] Étape 2 : express Gate 1 fait le 10/11 (g03-data.zip intégré : data/processed, src/moteur_v1.py, api/main.py, scripts/premier_resultat.py → docs/premier_resultat.md). Reste : tests pytest, contrat_api.md, notebook, sample_v1 + comparaison v0/v1, mention licences, CRM 1 000 interactions.
- [ ] Étape 3
- [ ] Étape 4
- [ ] Étape 5
