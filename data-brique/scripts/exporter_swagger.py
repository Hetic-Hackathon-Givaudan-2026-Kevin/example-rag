"""Exporte la description OpenAPI (Swagger) de l'API dans openapi.yaml et openapi.json.

Lancer : python scripts/exporter_swagger.py
"""

import json
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from api.main import app  # noqa: E402

spec = app.openapi()
(RACINE / "docs" / "openapi.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
(RACINE / "docs" / "openapi.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
print("openapi.yaml et openapi.json écrits")
