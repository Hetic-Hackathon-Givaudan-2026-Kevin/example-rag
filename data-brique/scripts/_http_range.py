"""Lecture d'un gros fichier distant par plages d'octets (HTTP Range).

Pourquoi : food.parquet (Open Food Facts) fait ~8 Go. Le format Parquet est découpé
en blocs (« row groups ») et en colonnes : en lisant seulement quelques blocs et
quelques colonnes, on télécharge quelques dizaines de Mo au lieu de 8 Go.
pyarrow sait lire un objet « fichier » Python : on lui en fournit un qui fait des
requêtes HTTP Range à chaque lecture.
"""
from __future__ import annotations

import io

import requests


class HttpRangeFile(io.RawIOBase):
    def __init__(self, url: str, session: requests.Session | None = None, timeout: int = 60):
        self.session = session or requests.Session()
        self.timeout = timeout
        # On suit la redirection une fois (Hugging Face -> CDN signé) et on garde l'URL finale.
        r = self.session.get(url, headers={"Range": "bytes=0-0"}, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        self.url = r.url
        self.size = int(r.headers["Content-Range"].split("/")[-1])
        self.pos = 0
        self.bytes_read = 0  # pour savoir combien on a vraiment téléchargé

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        else:
            self.pos = self.size + offset
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.pos + n, self.size) - 1
        r = self.session.get(self.url, headers={"Range": f"bytes={self.pos}-{end}"}, timeout=self.timeout)
        r.raise_for_status()
        data = r.content
        self.pos += len(data)
        self.bytes_read += len(data)
        return data

    def readinto(self, b) -> int:
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)
