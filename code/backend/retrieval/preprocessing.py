"""PDF ingestion: PDFs in DATASET/ -> page-aware, citation-ready chunks.

Design goals
* portable: only relative paths, no OS-specific code
* page boundaries preserved: a chunk never spans two pages
* every chunk has a stable ID:  <paper_id>:p<page>:c<index>
* bad input is reported, never fatal: corrupt / text-empty / duplicate PDFs are
  skipped and listed in ingest_report.json

Run:  python -m retrieval.preprocessing        (from code/backend)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CHUNK_SIZE = 900          # characters
CHUNK_OVERLAP = 150
MIN_CHUNK_CHARS = 60
MIN_TEXT_CHARS_PER_PAPER = 1500   # below this a PDF is treated as scanned / text-empty


class PDFReadError(Exception):
    pass


# ----------------------------------------------------------------------------- extraction
def extract_pages(path: Path) -> list[str]:
    """Return the text of every page (index 0 = page 1). Tries pypdfium2 first
    (best spacing / reading order), then pypdf. Raises PDFReadError if neither works."""
    errors: list[str] = []
    try:
        import pypdfium2 as pdfium  # type: ignore

        doc = pdfium.PdfDocument(str(path))
        try:
            return [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
        finally:
            doc.close()
    except Exception as exc:  # noqa: BLE001 - any backend failure falls through
        errors.append(f"pdfium: {exc}")
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [(p.extract_text() or "") for p in reader.pages]
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pypdf: {exc}")
    raise PDFReadError("; ".join(errors))


# ----------------------------------------------------------------------------- cleaning
_SOFT_HYPHEN = re.compile("[\ufffe\u00ad]")


def normalise_text(text: str) -> str:
    """Whitespace/typography normalisation used both when chunking and when
    checking that a quote really occurs in a chunk."""
    text = _SOFT_HYPHEN.sub("", text)
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\u2019", "'")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # re-join hyphenated line breaks
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _line_key(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


def strip_running_lines(pages: list[str]) -> list[str]:
    """Remove running headers/footers (a short line repeated on many pages) and bare
    page numbers. Conservative: only lines < 110 chars seen on >= 40% of pages."""
    if len(pages) < 4:
        return pages
    counts: Counter[str] = Counter()
    for page in pages:
        counts.update({_line_key(l) for l in page.splitlines() if 3 <= len(l.strip()) < 110})
    threshold = max(3, int(0.4 * len(pages)))
    repeated = {k for k, v in counts.items() if v >= threshold}
    cleaned = []
    for page in pages:
        kept = []
        for line in page.splitlines():
            s = line.strip()
            if re.fullmatch(r"\d{1,3}", s):
                continue
            if _line_key(line) in repeated:
                continue
            kept.append(line)
        cleaned.append("\n".join(kept))
    return cleaned


_REFS_HEADING = re.compile(r"^\s*(?:\d+\.?\s*)?(references|bibliography)\s*$", re.I | re.M)


def references_start_page(pages: list[str]) -> int | None:
    """Index of the first page containing a 'References' heading line, if any."""
    for i, page in enumerate(pages):
        if _REFS_HEADING.search(page):
            return i
    return None


def looks_like_bibliography(text: str, strict: bool = False) -> bool:
    """Bibliography entries are dense in years, author initials and venue words.
    In-text citations in body paragraphs are not (so body text is not flagged)."""
    years = len(re.findall(r"\b(?:19|20)\d{2}\b", text))
    initials = len(re.findall(r"\b[A-Z]\.\s?(?:[A-Z]\.\s?)?[A-Z][a-z]+", text))
    venues = len(re.findall(r"arXiv|Proceedings|Conference|Journal|\bIn\s[A-Z]|pp\.|preprint", text))
    need = 7 if strict else 4
    return years >= 4 and initials >= need and venues >= 2


# ----------------------------------------------------------------------------- chunking
def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split on word boundaries into ~size-char chunks with overlap."""
    words = text.split(" ")
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for w in words:
        cur.append(w)
        cur_len += len(w) + 1
        if cur_len >= size:
            chunks.append(" ".join(cur))
            # carry the tail as overlap
            tail: list[str] = []
            n = 0
            for x in reversed(cur):
                n += len(x) + 1
                tail.insert(0, x)
                if n >= overlap:
                    break
            cur, cur_len = tail, n
    if cur and (not chunks or cur_len > overlap + 20):
        chunks.append(" ".join(cur))
    return chunks


# ----------------------------------------------------------------------------- helpers
def slugify(name: str) -> str:
    stem = re.sub(r"\.pdf$", "", name, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")[:40] or "paper"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def guess_title(first_page: str, fallback: str) -> str:
    for line in first_page.splitlines():
        s = line.strip()
        if len(s) >= 15 and not s.lower().startswith(("arxiv", "preprint", "abstract")):
            return s[:200]
    return fallback


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


# ----------------------------------------------------------------------------- ingest
def ingest(dataset_dir: Path, manifest_path: Path, out_dir: Path, verbose: bool = True) -> dict[str, Any]:
    """Build chunks.json, papers.json and ingest_report.json. Returns the report."""
    dataset_dir, out_dir = Path(dataset_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(Path(manifest_path))
    by_file = {m["filename"]: m for m in manifest}
    pdfs = sorted(dataset_dir.glob("*.pdf")) if dataset_dir.exists() else []

    report: dict[str, Any] = {"dataset_dir": dataset_dir.name, "papers": [], "skipped": [], "warnings": []}
    papers: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    seen_hash: dict[str, str] = {}
    seen_ids: set[str] = set()

    if not pdfs:
        report["warnings"].append(f"No PDF files found in {dataset_dir}")

    for m in manifest:
        if not (dataset_dir / m["filename"]).exists():
            report["warnings"].append(f"Manifest entry '{m['paper_id']}' lists missing file {m['filename']}")

    for pdf in pdfs:
        meta = by_file.get(pdf.name)
        digest = sha256_file(pdf)
        if digest in seen_hash:
            report["skipped"].append({"filename": pdf.name, "reason": "duplicate", "detail": f"identical to {seen_hash[digest]}"})
            continue
        try:
            pages = extract_pages(pdf)
        except PDFReadError as exc:
            report["skipped"].append({"filename": pdf.name, "reason": "corrupt_or_unreadable", "detail": str(exc)[:200]})
            continue
        total_chars = sum(len(p.strip()) for p in pages)
        if not pages or total_chars < MIN_TEXT_CHARS_PER_PAPER:
            report["skipped"].append({
                "filename": pdf.name, "reason": "text_empty_or_scanned",
                "detail": f"{total_chars} characters extracted from {len(pages)} pages (OCR is not implemented)"})
            continue

        seen_hash[digest] = pdf.name
        pages = strip_running_lines(pages)
        if meta is None:
            report["warnings"].append(f"{pdf.name} is not in papers_manifest.json; metadata was guessed")
            meta = {"paper_id": slugify(pdf.name), "filename": pdf.name,
                    "title": guess_title(pages[0], pdf.name), "authors": None, "year": None, "url": None}
        paper_id = meta["paper_id"]
        if paper_id in seen_ids:
            report["skipped"].append({"filename": pdf.name, "reason": "duplicate_paper_id", "detail": paper_id})
            continue
        seen_ids.add(paper_id)
        for key in ("title", "authors", "year"):
            if not meta.get(key):
                report["warnings"].append(f"{paper_id}: missing metadata field '{key}'")

        n_before = len(chunks)
        empty_pages = 0
        ref_page = references_start_page(pages)
        for page_no, raw in enumerate(pages, start=1):
            text = normalise_text(raw)
            if len(text) < MIN_CHUNK_CHARS:
                empty_pages += 1
                continue
            for idx, piece in enumerate(chunk_text(text)):
                if len(piece) < MIN_CHUNK_CHARS and idx > 0:
                    continue
                chunks.append({
                    "chunk_id": f"{paper_id}:p{page_no}:c{idx}",
                    "paper_id": paper_id,
                    "filename": pdf.name,
                    "title": meta.get("title") or pdf.name,
                    "page": page_no,
                    "chunk_index": idx,
                    "is_reference": looks_like_bibliography(piece, strict=ref_page is None)
                    if (ref_page is None or page_no - 1 >= ref_page) else False,
                    "text": piece,
                })
        paper_record = {
            "paper_id": paper_id, "filename": pdf.name, "title": meta.get("title") or pdf.name,
            "authors": meta.get("authors"), "year": meta.get("year"), "url": meta.get("url"),
            "pages": len(pages), "chunks": len(chunks) - n_before, "sha256": digest,
        }
        papers.append(paper_record)
        report["papers"].append({**paper_record, "empty_pages": empty_pages})
        if verbose:
            print(f"  ok  {paper_id:24} pages={len(pages):3} chunks={paper_record['chunks']:4}")

    ids = [c["chunk_id"] for c in chunks]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate chunk IDs produced - this is a bug in ingest()")

    with open(out_dir / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    with open(out_dir / "papers.json", "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    report["totals"] = {"papers": len(papers), "chunks": len(chunks),
                        "reference_chunks": sum(1 for c in chunks if c["is_reference"])}
    with open(out_dir / "ingest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    if verbose:
        for s in report["skipped"]:
            print(f"  SKIPPED {s['filename']}: {s['reason']} ({s['detail']})")
        for w in report["warnings"]:
            print(f"  WARNING {w}")
        print(f"Wrote {len(chunks)} chunks for {len(papers)} papers to {out_dir}")
    return report


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.config import get_settings

    s = get_settings()
    print(f"Ingesting PDFs from {s.dataset_dir}")
    report = ingest(s.dataset_dir, s.manifest_path, s.processed_dir)
    return 0 if report["totals"]["papers"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
