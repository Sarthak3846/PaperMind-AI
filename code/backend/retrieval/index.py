"""BM25 retrieval over the processed chunks, with relevance gating.

Improvements over the original DebateRAG retriever:
* real tokenisation (lower-case, punctuation stripped, stop-words removed, light stemming)
* query-term *coverage* gating, so out-of-corpus questions return no hits instead of
  "the 5 least-bad chunks"
* paper filtering and per-paper grouping
* bibliography chunks excluded from the index
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from rank_bm25 import BM25Okapi

STOPWORDS = frozenset("""
a an and are as at be been but by can could did do does for from had has have how i in into is it its
may might more most of on or other our over should so some such than that the their them then there these
they this those to us was we were what when where which while who whom why will with would you your
about across after also any between both each few if not only own same than too very just using use used
paper papers study studies work works approach method methods propose proposed show shows result results
please tell explain describe compare comparison difference differences summarize summary analysis analyse
""".split())


def stem(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith(("ss", "us", "is")):
        return tok[:-1]
    return tok


def tokenize(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(t) for t in toks if t not in STOPWORDS and len(t) > 1]


@dataclass
class Hit:
    chunk: dict[str, Any]
    score: float
    coverage: float

    @property
    def chunk_id(self) -> str:
        return self.chunk["chunk_id"]


class Corpus:
    """In-memory corpus: papers, chunks and a BM25 index."""

    def __init__(self, papers: list[dict[str, Any]], chunks: list[dict[str, Any]]):
        self.papers: dict[str, dict[str, Any]] = {p["paper_id"]: p for p in papers}
        self.chunks: dict[str, dict[str, Any]] = {c["chunk_id"]: c for c in chunks}
        self._searchable = [c for c in chunks if not c.get("is_reference")]
        self._tokens = [tokenize(c["text"]) for c in self._searchable]
        self._tokensets = [set(t) for t in self._tokens]
        self._bm25 = BM25Okapi(self._tokens) if self._tokens else None
        self.aliases: dict[str, list[str]] = {pid: _aliases(p) for pid, p in self.papers.items()}
        self._by_paper: dict[str, list[dict[str, Any]]] = {}
        for c in chunks:
            self._by_paper.setdefault(c["paper_id"], []).append(c)
        for lst in self._by_paper.values():
            lst.sort(key=lambda c: (c["page"], c["chunk_index"]))

    # ------------------------------------------------------------------ loading
    @classmethod
    def load(cls, processed_dir: Path) -> "Corpus":
        processed_dir = Path(processed_dir)
        with open(processed_dir / "papers.json", encoding="utf-8") as f:
            papers = json.load(f)
        with open(processed_dir / "chunks.json", encoding="utf-8") as f:
            chunks = json.load(f)
        return cls(papers, chunks)

    # ------------------------------------------------------------------ lookup
    def paper(self, paper_id: str) -> dict[str, Any] | None:
        return self.papers.get(paper_id)

    def chunk(self, chunk_id: str) -> dict[str, Any] | None:
        return self.chunks.get(chunk_id)

    def has_chunk(self, chunk_id: str) -> bool:
        return chunk_id in self.chunks

    # ------------------------------------------------------------------ search
    def search(self, query: str | Iterable[str], top_k: int = 10,
               paper_ids: Iterable[str] | None = None, min_coverage: float = 0.34) -> list[Hit]:
        """BM25 search. A hit must contain >= min_coverage of the distinct query terms
        (and at least 2 terms when the query has 3+ terms)."""
        if self._bm25 is None:
            return []
        text = " ".join(query) if not isinstance(query, str) else query
        q = tokenize(text)
        if not q:
            return []
        uniq = set(q)
        allowed = set(paper_ids) if paper_ids is not None else None
        scores = self._bm25.get_scores(q)
        min_terms = 1 if len(uniq) < 3 else 2
        hits: list[Hit] = []
        for i, chunk in enumerate(self._searchable):
            if allowed is not None and chunk["paper_id"] not in allowed:
                continue
            matched = len(uniq & self._tokensets[i])
            cov = matched / len(uniq)
            if matched < min_terms or cov < min_coverage or scores[i] <= 0:
                continue
            hits.append(Hit(chunk=chunk, score=float(scores[i]), coverage=cov))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    def mentioned_papers(self, text: str, paper_ids: Iterable[str] | None = None) -> list[str]:
        """Papers the text names explicitly (short name such as 'REALM' / 'Self-RAG', or first-author surname)."""
        norm = " " + re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() + " "
        allowed = set(paper_ids) if paper_ids is not None else None
        return [pid for pid, al in self.aliases.items()
                if (allowed is None or pid in allowed) and any(f" {a} " in norm for a in al)]

    def retrieve(self, query: str | Iterable[str], paper_ids: Iterable[str] | None = None,
                 top_k: int = 12, max_papers: int = 4, mention_text: str = "") -> list[Hit]:
        """Search, then keep hits from the `max_papers` best papers (ranked by the sum of
        their top-3 hit scores) so that comparison tasks see several papers. Papers that the
        question names explicitly (`mention_text`) are always included."""
        hits = self.search(query, top_k=top_k * 4, paper_ids=paper_ids)
        named = self.mentioned_papers(mention_text, paper_ids) if mention_text else []
        for pid in named:  # make sure each named paper contributes hits even if generic terms favour surveys
            if not any(h.chunk["paper_id"] == pid for h in hits):
                hits += self.search(query, top_k=4, paper_ids=[pid], min_coverage=0.0)
        if not hits:
            return []
        per_paper: dict[str, list[Hit]] = {}
        for h in hits:
            per_paper.setdefault(h.chunk["paper_id"], []).append(h)
        ranked = sorted(per_paper, key=lambda p: sum(x.score for x in per_paper[p][:3]), reverse=True)
        named = [p for p in named if p in per_paper]
        ranked = named + [p for p in ranked if p not in named]
        max_papers = max(max_papers, min(6, len(named)))
        keep = set(ranked[:max_papers])
        chosen: list[Hit] = []
        # round-robin so each kept paper contributes evidence, then fill by score
        rank_lists = [per_paper[p] for p in ranked[:max_papers]]
        depth = 0
        while len(chosen) < top_k and any(depth < len(l) for l in rank_lists):
            for l in rank_lists:
                if depth < len(l) and len(chosen) < top_k:
                    chosen.append(l[depth])
            depth += 1
        return [h for h in sorted(chosen, key=lambda h: h.score, reverse=True) if h.chunk["paper_id"] in keep]

    def paper_context(self, paper_id: str, query: str | Iterable[str],
                      n_query: int = 6, n_lead: int = 2, max_chars: int = 12000) -> list[dict[str, Any]]:
        """Chunks used to analyse one paper: its opening chunks (abstract/intro) plus the
        chunks most relevant to the query, in document order."""
        lead = [c for c in self._by_paper.get(paper_id, []) if not c.get("is_reference")][:n_lead]
        rel = [h.chunk for h in self.search(query, top_k=n_query * 3, paper_ids=[paper_id], min_coverage=0.0)][:n_query]
        chosen: dict[str, dict[str, Any]] = {}
        for c in lead + rel:
            chosen.setdefault(c["chunk_id"], c)
        ordered = sorted(chosen.values(), key=lambda c: (c["page"], c["chunk_index"]))
        out, total = [], 0
        for c in ordered:
            if total + len(c["text"]) > max_chars and out:
                break
            out.append(c)
            total += len(c["text"])
        return out


def _aliases(paper: dict[str, Any]) -> list[str]:
    """Short names a researcher might use for a paper, e.g. 'realm', 'self rag', 'lewis'."""
    out: set[str] = set()
    title = paper.get("title") or ""
    if ":" in title:
        prefix = title.split(":", 1)[0].strip()
        if 1 <= len(prefix.split()) <= 3 and prefix.lower() not in {"rag"}:
            out.add(re.sub(r"[^a-z0-9]+", " ", prefix.lower()).strip())
    authors = paper.get("authors") or ""
    m = re.match(r"\s*([A-Za-z\-]+)", authors)
    if m and len(m.group(1)) >= 3:
        out.add(m.group(1).lower())
    stem = re.sub(r"\d+$", "", paper["paper_id"]).replace("_", "")
    if stem and stem not in {"ragsurveygao", "ragsurveygupta", "ragssrn", "raglewis"}:
        out.add(stem)
        out.add(re.sub(r"rag$", " rag", stem).strip() if stem.endswith("rag") and stem != "rag" else stem)
    return sorted(a for a in out if a)


_CORPUS: Corpus | None = None


def get_corpus(force_reload: bool = False) -> Corpus:
    """Singleton loader. Auto-runs ingestion if the processed files are missing."""
    global _CORPUS
    if _CORPUS is not None and not force_reload:
        return _CORPUS
    from app.config import get_settings
    from retrieval.preprocessing import ingest

    s = get_settings()
    if not (s.processed_dir / "chunks.json").exists() or not (s.processed_dir / "papers.json").exists():
        ingest(s.dataset_dir, s.manifest_path, s.processed_dir, verbose=False)
    _CORPUS = Corpus.load(s.processed_dir)
    return _CORPUS


def normalise_for_match(text: str) -> str:
    """Normalisation used when checking that a quote occurs in a chunk."""
    from retrieval.preprocessing import normalise_text

    t = normalise_text(text).lower()
    t = t.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"[^a-z0-9%.]+", " ", t).strip()


def quote_in_chunk(quote: str, chunk_text: str, min_part_chars: int = 15) -> bool:
    """True if every ellipsis-separated part of `quote` occurs verbatim (after
    normalisation) in `chunk_text`. Very short quotes are rejected."""
    parts = [p for p in re.split(r"\.\.\.|\u2026", quote) if p.strip()]
    if not parts:
        return False
    hay = normalise_for_match(chunk_text)
    ok = False
    for p in parts:
        n = normalise_for_match(p)
        if len(n) < min_part_chars:
            if len(parts) == 1:
                return False
            continue
        if n not in hay:
            return False
        ok = True
    return ok


def nan_safe(x: float) -> float:
    return 0.0 if (x is None or math.isnan(x)) else x
