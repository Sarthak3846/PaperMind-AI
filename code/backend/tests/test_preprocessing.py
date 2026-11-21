import json
import shutil
from pathlib import Path

from pypdf import PdfWriter

from app.config import get_settings
from retrieval.preprocessing import chunk_text, ingest, normalise_text, strip_running_lines


def test_shipped_corpus_is_complete(corpus):
    s = get_settings()
    manifest = json.loads(s.manifest_path.read_text(encoding="utf-8"))
    assert {m["paper_id"] for m in manifest} == set(corpus.papers)       # every manifest paper is indexed
    assert len(corpus.papers) == 7
    ids = list(corpus.chunks)
    assert len(ids) == len(set(ids))
    for c in corpus.chunks.values():
        assert c["page"] >= 1 and c["chunk_id"].startswith(c["paper_id"] + ":p")
        assert ":" in c["chunk_id"] and "\\" not in c["filename"] and "/" not in c["filename"]  # no absolute paths


def test_pages_are_never_mixed(corpus):
    for c in list(corpus.chunks.values())[:300]:
        assert c["chunk_id"].split(":")[1] == f"p{c['page']}"


def test_ingest_handles_bad_pdfs(tmp_path):
    s = get_settings()
    ds = tmp_path / "ds"
    ds.mkdir()
    src = s.dataset_dir / "2002.08909v1.pdf"
    shutil.copy(src, ds / "good.pdf")
    shutil.copy(src, ds / "duplicate_copy.pdf")           # identical bytes
    (ds / "corrupt.pdf").write_bytes(b"this is not a pdf at all")
    w = PdfWriter()
    for _ in range(3):
        w.add_blank_page(width=200, height=200)           # scanned-like: no text layer
    with open(ds / "blank.pdf", "wb") as f:
        w.write(f)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([{"paper_id": "ghost", "filename": "missing.pdf", "title": "T"}]))
    report = ingest(ds, manifest, tmp_path / "out", verbose=False)
    reasons = {x["filename"]: x["reason"] for x in report["skipped"]}
    assert reasons["corrupt.pdf"] == "corrupt_or_unreadable"
    assert reasons["blank.pdf"] == "text_empty_or_scanned"
    dup = [f for f in ("good.pdf", "duplicate_copy.pdf") if reasons.get(f) == "duplicate"]
    assert len(dup) == 1                                   # exactly one of the identical pair is skipped
    assert report["totals"]["papers"] == 1
    assert any("not in papers_manifest" in w for w in report["warnings"])      # metadata guessed
    assert any("missing.pdf" in w for w in report["warnings"])                  # manifest lists absent file


def test_ingest_empty_dataset(tmp_path):
    (tmp_path / "ds").mkdir()
    report = ingest(tmp_path / "ds", tmp_path / "m.json", tmp_path / "out", verbose=False)
    assert report["totals"]["papers"] == 0 and report["warnings"]


def test_text_helpers():
    assert normalise_text("ques\ufffetion  a-\nb") == "question ab"
    chunks = chunk_text("word " * 600)
    assert all(len(c) < 1100 for c in chunks) and len(chunks) > 2
    pages = ["Header\nbody one\n3", "Header\nbody two\n4", "Header\nbody three\n5", "Header\nbody four\n6"]
    assert "Header" not in "\n".join(strip_running_lines(pages))
