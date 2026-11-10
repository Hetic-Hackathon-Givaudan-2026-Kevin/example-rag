"""Outils partagés par les scripts de collecte : chemins, graine, fichiers .meta.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
CACHE = RAW / "_cache"  # gros fichiers téléchargés, jamais versionnés

USER_AGENT = "hackathon-hetic-data-brique/0.1 (projet etudiant, usage non commercial)"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_meta(data_path: Path, **fields) -> Path:
    """Écrit <fichier>.meta.json à côté du jeu de données (traçabilité)."""
    meta = {"fichier": data_path.name, "date_extraction": now_iso(), **fields}
    meta_path = data_path.with_name(data_path.name + ".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta_path
