"""Utilidades de texto: normalização, tokenização PT-BR e um TF-IDF mínimo (sem dependências)."""
from __future__ import annotations
import math
import re
import unicodedata
from collections import Counter

STOP = set("""a o e é de da do das dos em no na nos nas um uma uns umas para por com sem que se ao aos as os
ou mais menos muito muita como sobre entre ser ter tem são está estão foi era deve devem pode podem será
este esta isso isto esse essa nosso nossa seu sua seus suas ele ela eles elas eu nós você vocês já também
the and of to in for on with projeto projetos sistema sistemas""".split())


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def tokens(text: str) -> list[str]:
    out = []
    for t in re.findall(r"[a-z0-9][a-z0-9#+.]*", fold(text)):
        t = t.strip(".")
        if len(t) < 2 or t in STOP:
            continue
        out.append(t[:7] if len(t) > 7 and not any(ch in t for ch in "#+.") else t)
    return out


class TfIdf:
    """Índice TF-IDF com similaridade de cosseno (suficiente para ~1k documentos)."""

    def __init__(self, docs: list[str]):
        self.tf = [Counter(tokens(d)) for d in docs]
        n = len(docs)
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        self.idf = {t: math.log((1 + n) / (1 + f)) + 1 for t, f in df.items()}
        self.vecs = [self._vec(c) for c in self.tf]

    def _vec(self, c: Counter) -> dict:
        v = {t: (1 + math.log(f)) * self.idf.get(t, 0.0) for t, f in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def query(self, text: str) -> list[float]:
        q = self._vec(Counter(tokens(text)))
        return [sum(w * d.get(t, 0.0) for t, w in q.items()) for d in self.vecs]

    def top(self, text: str, k: int = 5) -> list[tuple[int, float]]:
        sims = self.query(text)
        return sorted(((i, s) for i, s in enumerate(sims) if s > 0), key=lambda x: -x[1])[:k]
