"""Convertit benchmark/resultats.md en HTML puis en PDF (benchmark/benchmark_llm.pdf) avec Microsoft Edge headless.

Pourquoi Edge : il est déjà installé sous Windows -> pas de gros paquet à ajouter (disque C: presque plein).
Seule dépendance : la petite bibliothèque Python `markdown`.

Usage : python benchmark/exporter_pdf.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown

ICI = Path(__file__).resolve().parent
SOURCE = ICI / "resultats.md"
HTML = ICI / "benchmark_llm.html"
PDF = ICI / "benchmark_llm.pdf"
EDGE_CANDIDATS = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

CSS = """
@page { size: A4 landscape; margin: 12mm 12mm 14mm 12mm; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: 10.5pt; line-height: 1.45;
       color: #1f2328; max-width: 100%; margin: 0; }
h1 { font-size: 19pt; border-bottom: 2px solid #1f2328; padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 14pt; margin-top: 18px; border-bottom: 1px solid #d0d7de; padding-bottom: 2px; }
/* Mise en page : un titre ne reste jamais seul en bas de page, un tableau n'est jamais coupé,
   et le bloc « titre + texte d'intro + tableau » d'une section reste sur une même page. */
h2, h3 { break-after: avoid; }
table { break-inside: avoid; }
tr { break-inside: avoid; }
.bloc { break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 10px; font-size: 9pt; }
th, td { border: 1px solid #8c959f; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #eef1f4; font-weight: 600; }
tr:nth-child(even) td { background: #f8f9fa; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; background: #f2f4f6;
       padding: 0 3px; border-radius: 3px; }
pre { background: #f2f4f6; border: 1px solid #d0d7de; padding: 8px; font-size: 8.5pt;
      white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; padding: 0; }
em { color: #57606a; }
blockquote { border-left: 4px solid #bf8700; background: #fff8e5; margin: 8px 0; padding: 6px 12px; }
blockquote p { margin: 0; }
li { margin: 2px 0; }
a { color: #0b5cad; text-decoration: none; }
"""


def trouver_edge() -> Path:
    for p in EDGE_CANDIDATS:
        if p.exists():
            return p
    trouve = shutil.which("msedge")
    if trouve:
        return Path(trouve)
    raise FileNotFoundError("Microsoft Edge introuvable")


LISTE = re.compile(r"^(\s*)([-*]|\d+\.)\s")


def preparer_markdown(texte: str) -> str:
    """Rend le Markdown « style GitHub » lisible par la bibliothèque `markdown` :
    - ligne vide avant une liste qui suit directement un paragraphe ;
    - sous-listes indentées de 1 à 3 espaces -> 4 espaces."""
    sortie, precedente, dans_code = [], "", False
    for ligne in texte.splitlines():
        if ligne.lstrip().startswith("```"):
            dans_code = not dans_code
        m = None if dans_code else LISTE.match(ligne)
        if m:
            indent = len(m.group(1))
            if 0 < indent < 4:
                ligne = "    " + ligne.lstrip()
            if precedente.strip() and not LISTE.match(precedente) and not precedente.startswith("    "):
                sortie.append("")
        sortie.append(ligne)
        precedente = ligne
    return "\n".join(sortie)


SECTION = re.compile(r"(<h2[^>]*>.*?</h2>)(.*?)(?=<h2|\Z)", re.S)
PREMIER_ELEMENT = re.compile(r"\s*<(p|ul|ol|pre|blockquote)\b.*?</\1>", re.S)


def grouper_sections(html: str) -> str:
    """Regroupe chaque section dans un bloc insécable (classe CSS `bloc`) :
    - section avec tableau : titre + texte d'intro + premier tableau ;
    - section sans tableau : titre + premier paragraphe ou liste.
    La suite de la section (lecture, listes) reste libre de passer à la page suivante :
    regrouper toute la section laisserait de grands blancs quand elle dépasse une page."""
    def envelopper(m: re.Match) -> str:
        titre, corps = m.group(1), m.group(2)
        fin_tableau = corps.find("</table>")
        if fin_tableau != -1:
            coupe = fin_tableau + len("</table>")
        else:
            premier = PREMIER_ELEMENT.match(corps)
            coupe = premier.end() if premier else 0
        return f'<div class="bloc">{titre}{corps[:coupe]}</div>{corps[coupe:]}'
    return SECTION.sub(envelopper, html)


def main() -> None:
    corps = markdown.markdown(preparer_markdown(SOURCE.read_text(encoding="utf-8")),
                              extensions=["tables", "fenced_code", "sane_lists"])
    corps = grouper_sections(corps)
    HTML.write_text(
        "<!doctype html>\n<html lang=\"fr\"><head><meta charset=\"utf-8\">"
        f"<title>Benchmark LLM — G03 Data</title><style>{CSS}</style></head>\n<body>\n{corps}\n</body></html>\n",
        encoding="utf-8",
    )
    edge = trouver_edge()
    # Profil temporaire : évite de « confier » l'impression à une fenêtre Edge déjà ouverte.
    with tempfile.TemporaryDirectory() as profil:
        subprocess.run([
            str(edge), "--headless", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
            f"--user-data-dir={profil}", f"--print-to-pdf={PDF}", HTML.as_uri(),
        ], check=True, timeout=120, capture_output=True)
    print(f"-> {HTML.name} et {PDF.name} ({PDF.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
