"""Benchmark des modèles locaux (Ollama, CPU) pour la piste « 3 questions qui débloquent les briefs ».

Deux tâches, mesurées sur les 15 cas de benchmark/briefs_test.csv (écrits AVANT les prompts) :

1. RECHERCHE : à partir d'un besoin du commercial en langage courant, retrouver la bonne question
   dans la banque (data/processed/questions.csv).
   Mesures : bonne rubrique au rang 1, bonne question au rang 1, dans le top 3 (= les 3 questions
   montrées au junior), dans le top 5,
   MRR (rang moyen inversé), temps par requête. Référence : TF-IDF (sans modèle).
2. EXTRACTION (LLM) : à partir d'une note de rendez-vous, sortir en JSON les rubriques du brief déjà connues.
   Mesures : JSON valide, précision / rappel / F1 sur les rubriques, rubriques inventées,
   valeurs inventées (mots absents de la note), temps par note.

Règles : Ollama sur 127.0.0.1 (pas localhost, lent sous Windows), temperature 0 + graine fixe,
vecteurs de la banque en cache (benchmark/cache/). Un modèle non installé est signalé et sauté.

Usage
  python benchmark/run_benchmark.py --pc pc_principal                       # modèles par défaut
  python benchmark/run_benchmark.py --pc pc2 --embed bge-m3 --llm qwen2.5:3b # sur le PC d'un coéquipier
  python benchmark/run_benchmark.py --rapport                               # regroupe tous les PC -> tableaux.md
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import re
import shutil
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
from src.moteur_v1 import RUBRIQUES  # noqa: E402

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").replace("localhost", "127.0.0.1")
CACHE = ICI / "cache"
RUNS = ICI / "runs"
SEED = 42
# Plafond de tokens par réponse : évite qu'un petit modèle boucle sans fin (vu avec qwen2.5:0.5b en mode JSON).
# Une réponse coupée n'est pas un JSON valide -> comptée comme échec.
MAX_TOKENS = 400
EMBED_DEFAUT = ["nomic-embed-text", "all-minilm", "bge-m3"]
LLM_DEFAUT = ["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b"]
# Modèles prévus mais pas encore testés : à mesurer sur le PC d'un coéquipier.
MODELES_COEQUIPIERS = {"embed": ["mxbai-embed-large"], "llm": ["llama3.2:3b"]}

# Préfixes demandés par certains modèles d'embeddings (documentation des modèles).
PREFIXES = {"nomic-embed-text": ("search_query: ", "search_document: "),
            "mxbai-embed-large": ("Represent this sentence for searching relevant passages: ", "")}

STOPWORDS = set("""a au aux avec ce ces c cela d dans de des du elle en est et eux il ils je j l la le les leur leurs
lui ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton
tu un une vos votre vous y ça ca est-ce quel quelle quels quelles plutot tout tous faut savoir sais veux voudrais
aimerais dois chez ils elles""".split())


# ---------------------------------------------------------------- utilitaires
def sans_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def mots(s: str) -> list[str]:
    return [m for m in re.findall(r"[a-z0-9]+", sans_accents(s)) if m not in STOPWORDS and len(m) > 1]


def config_pc() -> dict:
    class MEM(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    ram = {}
    if platform.system() == "Windows":
        m = MEM()
        m.dwLength = ctypes.sizeof(MEM)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        ram = {"ram_totale_go": round(m.ullTotalPhys / 2**30, 1), "ram_libre_go": round(m.ullAvailPhys / 2**30, 1)}
    disque = shutil.disk_usage(Path.home().anchor)
    try:
        version = requests.get(f"{OLLAMA}/api/version", timeout=5).json().get("version")
    except requests.RequestException:
        version = None
    return {"os": f"{platform.system()} {platform.release()}", "cpu": platform.processor(),
            "coeurs_logiques": os.cpu_count(), **ram,
            "disque_systeme_libre_go": round(disque.free / 2**30, 1),
            "disque_systeme_total_go": round(disque.total / 2**30, 1),
            "ollama": version, "python": platform.python_version(),
            "date": datetime.now().isoformat(timespec="seconds")}


def modeles_installes() -> set[str]:
    try:
        tags = requests.get(f"{OLLAMA}/api/tags", timeout=10).json()["models"]
    except requests.RequestException:
        return set()
    noms = set()
    for t in tags:
        noms.add(t["name"])
        if t["name"].endswith(":latest"):
            noms.add(t["name"].removesuffix(":latest"))
    return noms


# ---------------------------------------------------------------- recherche
def texte_question(q: pd.Series) -> str:
    return f"{RUBRIQUES[q['rubrique']]}. {q['texte']} {q['pourquoi']}"


class TfIdf:
    """TF-IDF minimal (mots + bigrammes, tf logarithmique, normalisation L2), sans dépendance lourde."""

    def __init__(self, docs: list[str]):
        self.toks = [self._grams(d) for d in docs]
        df = Counter(g for t in self.toks for g in set(t))
        n = len(docs)
        self.idf = {g: math.log((1 + n) / (1 + c)) + 1 for g, c in df.items()}
        self.mat = [self._vec(t) for t in self.toks]

    @staticmethod
    def _grams(s: str) -> list[str]:
        m = mots(s)
        return m + [f"{a}_{b}" for a, b in zip(m, m[1:])]

    def _vec(self, toks: list[str]) -> dict[str, float]:
        v = {g: (1 + math.log(c)) * self.idf[g] for g, c in Counter(toks).items() if g in self.idf}
        norme = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {g: x / norme for g, x in v.items()}

    def scores(self, requete: str) -> np.ndarray:
        q = self._vec(self._grams(requete))
        return np.array([sum(w * d.get(g, 0.0) for g, w in q.items()) for d in self.mat])


def embed(modele: str, textes: list[str]) -> np.ndarray:
    r = requests.post(f"{OLLAMA}/api/embed", json={"model": modele, "input": textes}, timeout=300)
    r.raise_for_status()
    v = np.array(r.json()["embeddings"], dtype=float)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def embed_banque(modele: str, docs: list[str]) -> tuple[np.ndarray, float]:
    """Vecteurs de la banque, mis en cache (clé = modèle + empreinte des textes)."""
    CACHE.mkdir(exist_ok=True)
    cle = hashlib.sha1(("\n".join(docs)).encode()).hexdigest()[:12]
    f = CACHE / f"{modele.replace(':', '_').replace('/', '_')}_{cle}.npy"
    if f.exists():
        return np.load(f), 0.0
    t0 = time.perf_counter()
    v = embed(modele, docs)
    duree = time.perf_counter() - t0
    np.save(f, v)
    return v, duree


def evaluer_recherche(nom: str, scorer, cas: pd.DataFrame, banque: pd.DataFrame) -> dict:
    ids = banque["id_question"].tolist()
    lignes, temps = [], []
    for _, c in cas.iterrows():
        t0 = time.perf_counter()
        s = scorer(c["besoin"])
        temps.append(time.perf_counter() - t0)
        ordre = [ids[i] for i in np.argsort(-s)]
        ok = set(c["questions_acceptables"].split("|"))
        rang = next((i + 1 for i, q in enumerate(ordre) if q in ok), None)
        top1_rub = banque.set_index("id_question").loc[ordre[0], "rubrique"]
        lignes.append({"id_cas": c["id_cas"], "top1": ordre[0], "top5": "|".join(ordre[:5]),
                       "rubrique_rang1_ok": top1_rub == c["rubrique_attendue"],
                       "question_rang1_ok": ordre[0] in ok,
                       "question_top3_ok": rang is not None and rang <= 3,
                       "question_top5_ok": rang is not None and rang <= 5,
                       "rang": rang})
    d = pd.DataFrame(lignes)
    return {"modele": nom, "type": "recherche",
            "rubrique_rang1": round(d["rubrique_rang1_ok"].mean(), 3),
            "question_rang1": round(d["question_rang1_ok"].mean(), 3),
            "question_top3": round(d["question_top3_ok"].mean(), 3),
            "question_top5": round(d["question_top5_ok"].mean(), 3),
            "mrr": round(d["rang"].apply(lambda r: 1 / r if r else 0).mean(), 3),
            "temps_moyen_ms": round(1000 * float(np.mean(temps)), 1),
            "details": lignes}


# ---------------------------------------------------------------- extraction LLM
PROMPT_EXTRACTION = """Tu aides un commercial d'une maison de parfums. On te donne la note d'un rendez-vous client.
Indique quelles rubriques du brief sont DÉJÀ renseignées par la note, avec l'extrait correspondant.
N'invente rien : si une information n'est pas écrite dans la note, la rubrique n'est pas renseignée.
Si la note dit qu'un sujet n'a pas été abordé, la rubrique n'est pas renseignée.

Rubriques possibles (utilise exactement ces codes) :
{rubriques}

Réponds uniquement en JSON, au format :
{{"rubriques_remplies": ["code", ...], "valeurs": {{"code": "extrait de la note", ...}}}}"""


def appeler_llm(modele: str, note: str) -> tuple[str, float, dict]:
    rubriques = "\n".join(f"- {k} : {v}" for k, v in RUBRIQUES.items())
    corps = {
        "model": modele, "stream": False, "format": "json",
        "options": {"temperature": 0, "seed": SEED, "num_ctx": 2048, "num_predict": MAX_TOKENS},
        "messages": [{"role": "system", "content": PROMPT_EXTRACTION.format(rubriques=rubriques)},
                     {"role": "user", "content": f"Note du rendez-vous :\n{note}"}],
    }
    t0 = time.perf_counter()
    r = requests.post(f"{OLLAMA}/api/chat", json=corps, timeout=300)
    duree = time.perf_counter() - t0
    r.raise_for_status()
    j = r.json()
    return j["message"]["content"], duree, j


def valeur_inventee(valeur: str, note: str) -> bool:
    """Une valeur est « inventée » si moins de la moitié de ses mots utiles figurent dans la note."""
    m = mots(str(valeur))
    if not m:
        return False
    n = set(mots(note))
    return sum(x in n for x in m) / len(m) < 0.5


VIDES = re.compile(r"^\s*(|aucune?.*|non (precise|mentionne|aborde).*|n/?a|inconnu.*|none|null)\s*$")


def garde_fou(predit: set[str], valeurs: dict, note: str) -> set[str]:
    """Règle sans IA, ajoutée APRÈS le 1er passage (à confirmer sur les cas de validation) :
    une rubrique ne compte que si son code existe, que sa valeur est non vide, et que cette valeur
    se retrouve dans la note (sinon c'est probablement une invention)."""
    gardes = set()
    for r in predit:
        v = str(valeurs.get(r, "") or "")
        if r in RUBRIQUES and not VIDES.match(sans_accents(v)) and not valeur_inventee(v, note):
            gardes.add(r)
    return gardes


def scores_ensemble(predit: set[str], attendu: set[str]) -> tuple[float, float]:
    vp = len(predit & attendu)
    precision = vp / len(predit) if predit else (1.0 if not attendu else 0.0)
    rappel = vp / len(attendu) if attendu else (1.0 if not predit else 0.0)
    return precision, rappel


def evaluer_extraction(modele: str, cas: pd.DataFrame) -> dict:
    # Chauffe : charge le modèle en mémoire (temps mesuré à part, pas compté dans le temps par note).
    t0 = time.perf_counter()
    appeler_llm(modele, "Test.")
    chargement = time.perf_counter() - t0
    lignes = []
    for _, c in cas.iterrows():
        attendu = set(filter(None, str(c["rubriques_remplies_attendues"] or "").split(";"))) - {"nan"}
        try:
            brut, duree, meta = appeler_llm(modele, c["note_rdv"])
        except requests.RequestException as e:  # délai dépassé, etc. -> échec de ce cas, on continue
            brut, duree, meta = f"ERREUR: {type(e).__name__}", 300.0, {}
        try:
            j = json.loads(brut)
            predit_brut = j.get("rubriques_remplies", [])
            valeurs = j.get("valeurs", {}) or {}
            valide = isinstance(predit_brut, list) and isinstance(valeurs, dict)
        except (json.JSONDecodeError, AttributeError):
            j, predit_brut, valeurs, valide = None, [], {}, False
        predit = {str(x) for x in predit_brut} if valide else set()
        inconnues = {x for x in predit if x not in RUBRIQUES}
        vp = len(predit & attendu)
        inventees = (predit - attendu)
        val_inv = [k for k, v in valeurs.items() if valeur_inventee(v, c["note_rdv"])] if valide else []
        tok_s = meta.get("eval_count", 0) / (meta.get("eval_duration", 1) / 1e9) if meta.get("eval_duration") else None
        filtre = garde_fou(predit, valeurs, c["note_rdv"])
        pf, rf = scores_ensemble(filtre, attendu)
        lignes.append({
            "id_cas": c["id_cas"], "json_valide": valide,
            "attendu": sorted(attendu), "predit": sorted(predit), "predit_garde_fou": sorted(filtre),
            "precision": vp / len(predit) if predit else (1.0 if not attendu else 0.0),
            "rappel": vp / len(attendu) if attendu else (1.0 if not predit else 0.0),
            "precision_gf": pf, "rappel_gf": rf, "exact_gf": filtre == attendu,
            "inventee_gf": len(filtre - attendu) > 0,
            "exact": predit == attendu, "rubriques_inventees": sorted(inventees),
            "codes_inconnus": sorted(inconnues), "valeurs_inventees": val_inv,
            "temps_s": round(duree, 2), "tokens_par_s": round(tok_s, 1) if tok_s else None, "brut": brut,
        })
    d = pd.DataFrame(lignes)
    p, r = d["precision"].mean(), d["rappel"].mean()
    return {"modele": modele, "type": "extraction",
            "json_valide": round(d["json_valide"].mean(), 3),
            "precision": round(p, 3), "rappel": round(r, 3),
            "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
            "cas_exacts": round(d["exact"].mean(), 3),
            "notes_avec_rubrique_inventee": round((d["rubriques_inventees"].str.len() > 0).mean(), 3),
            "notes_avec_valeur_inventee": round((d["valeurs_inventees"].str.len() > 0).mean(), 3),
            "f1_garde_fou": round(2 * d["precision_gf"].mean() * d["rappel_gf"].mean()
                                  / ((d["precision_gf"].mean() + d["rappel_gf"].mean()) or 1), 3),
            "precision_garde_fou": round(d["precision_gf"].mean(), 3),
            "rappel_garde_fou": round(d["rappel_gf"].mean(), 3),
            "cas_exacts_garde_fou": round(d["exact_gf"].mean(), 3),
            "notes_avec_rubrique_inventee_garde_fou": round(d["inventee_gf"].mean(), 3),
            "temps_moyen_s": round(d["temps_s"].mean(), 2), "temps_max_s": round(d["temps_s"].max(), 2),
            "tokens_par_s": round(d["tokens_par_s"].dropna().mean(), 1) if d["tokens_par_s"].notna().any() else None,
            "chargement_s": round(chargement, 1), "details": lignes}


# ---------------------------------------------------------------- rapport
def rapport() -> None:
    runs = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(RUNS.glob("*.json"))}
    L = ["# Tableaux du benchmark (générés par `run_benchmark.py --rapport`)\n"]
    L.append("## Configuration des PC\n")
    L.append(pd.DataFrame({pc: r["config"] for pc, r in runs.items()}).to_markdown() + "\n")
    pct = lambda x: f"{100 * x:.0f} %" if isinstance(x, (int, float)) else x  # noqa: E731
    rech, ext = [], []
    for pc, r in runs.items():
        for res in r["resultats"].values():
            if res["type"] == "recherche":
                rech.append({"modèle": res["modele"], "testé sur": pc,
                             "rubrique rang 1": pct(res["rubrique_rang1"]),
                             "question rang 1": pct(res["question_rang1"]),
                             "question top 3": pct(res.get("question_top3", "")),
                             "question top 5": pct(res["question_top5"]), "MRR": res["mrr"],
                             "temps / requête (ms)": res["temps_moyen_ms"],
                             "indexation banque (s)": res.get("indexation_banque_s", "")})
            else:
                ext.append({"modèle": res["modele"], "testé sur": pc,
                            "JSON valide": pct(res["json_valide"]), "F1 brut": res["f1"],
                            "F1 garde-fou": res.get("f1_garde_fou", ""),
                            "notes exactes (garde-fou)": pct(res.get("cas_exacts_garde_fou", "")),
                            "notes avec rubrique inventée (brut)": pct(res["notes_avec_rubrique_inventee"]),
                            "notes avec rubrique inventée (garde-fou)":
                                pct(res.get("notes_avec_rubrique_inventee_garde_fou", "")),
                            "temps / note moy. (s)": res["temps_moyen_s"],
                            "temps / note max (s)": res["temps_max_s"]})
    # Lignes « à remplir » uniquement pour les modèles que personne n'a encore testés.
    vus = {x["modèle"] for x in rech + ext}
    for m in MODELES_COEQUIPIERS["embed"]:
        if m not in vus:
            rech.append({"modèle": m, "testé sur": "à remplir (PC coéquipier)"})
    for m in MODELES_COEQUIPIERS["llm"]:
        if m not in vus:
            ext.append({"modèle": m, "testé sur": "à remplir (PC coéquipier)"})
    L.append("## Recherche de la bonne question (15 cas)\n")
    L.append(pd.DataFrame(rech).fillna("").to_markdown(index=False) + "\n")
    L.append("## Extraction JSON des rubriques connues (15 notes)\n")
    L.append(pd.DataFrame(ext).fillna("").to_markdown(index=False) + "\n")
    L.append("Détail cas par cas (sorties brutes des modèles) : `benchmark/runs/<pc>.json`.\n")
    (ICI / "tableaux.md").write_text("\n".join(L), encoding="utf-8")
    print(f"-> {ICI / 'tableaux.md'}")


# ---------------------------------------------------------------- main
def sauver(fichier: Path, run: dict) -> None:
    """Sauvegarde après chaque modèle : un plantage ne fait pas perdre les résultats déjà obtenus."""
    fichier.write_text(json.dumps(run, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pc", default="pc_principal", help="étiquette du PC (sans nom de personne)")
    p.add_argument("--embed", nargs="*", default=EMBED_DEFAUT)
    p.add_argument("--llm", nargs="*", default=LLM_DEFAUT)
    p.add_argument("--rapport", action="store_true")
    a = p.parse_args()
    if a.rapport:
        return rapport()

    RUNS.mkdir(exist_ok=True)
    cas = pd.read_csv(ICI / "briefs_test.csv", dtype=str, keep_default_na=False)
    banque = pd.read_csv(RACINE / "data" / "processed" / "questions.csv")
    docs = [texte_question(q) for _, q in banque.iterrows()]
    installes = modeles_installes()
    fichier = RUNS / f"{a.pc}.json"
    run = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {"resultats": {}}
    run["config"] = config_pc()
    run["non_installes"] = []

    # Référence TF-IDF
    tf = TfIdf(docs)
    run["resultats"]["tfidf"] = evaluer_recherche("tfidf", tf.scores, cas, banque)
    print("tfidf", {k: v for k, v in run["resultats"]["tfidf"].items() if k != "details"})

    for m in a.embed:
        if m not in installes:
            print(f"[saute] {m} non installé (ollama pull {m})")
            run["non_installes"].append(m)
            continue
        pq, pd_ = PREFIXES.get(m, ("", ""))
        vb, duree_index = embed_banque(m, [pd_ + d for d in docs])
        res = evaluer_recherche(m, lambda q, m=m, pq=pq, vb=vb: vb @ embed(m, [pq + q])[0], cas, banque)
        # 0 = vecteurs lus dans le cache : on garde alors la mesure du premier passage (sans cache).
        ancien = run["resultats"].get(m, {}).get("indexation_banque_s")
        res["indexation_banque_s"] = round(duree_index, 2) if duree_index or ancien is None else ancien
        run["resultats"][m] = res
        sauver(fichier, run)
        print(m, {k: v for k, v in res.items() if k != "details"})

    for m in a.llm:
        if m not in installes:
            print(f"[saute] {m} non installé (ollama pull {m})")
            run["non_installes"].append(m)
            continue
        res = evaluer_extraction(m, cas)
        run["resultats"][m] = res
        sauver(fichier, run)
        print(m, {k: v for k, v in res.items() if k != "details"})

    sauver(fichier, run)
    print(f"-> {fichier}")
    rapport()


if __name__ == "__main__":
    main()
