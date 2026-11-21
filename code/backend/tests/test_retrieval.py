from retrieval.index import quote_in_chunk, tokenize


def test_relevant_query_hits_expected_paper(corpus):
    hits = corpus.retrieve(["self-rag", "reflection tokens", "adaptive retrieval"])
    assert hits and "selfrag2023" in {h.chunk["paper_id"] for h in hits}


def test_out_of_corpus_query_returns_nothing(corpus):
    assert corpus.retrieve("How do I bake sourdough bread") == []
    assert corpus.retrieve("") == []
    assert corpus.retrieve("the of and") == []


def test_paper_filter_is_respected(corpus):
    hits = corpus.retrieve(["retrieval", "generation"], paper_ids=["realm2020"])
    assert hits and {h.chunk["paper_id"] for h in hits} == {"realm2020"}


def test_tokenizer_normalises():
    assert tokenize("RAG? Retrieval-Augmented!") == ["rag", "retrieval", "augmented"]


def test_quote_check(corpus):
    ch = corpus.chunk("selfrag2023:p1:c0")
    assert quote_in_chunk(ch["text"][60:160], ch["text"])
    assert not quote_in_chunk("A sentence that the paper never contains anywhere", ch["text"])
    assert not quote_in_chunk("short", ch["text"])


def test_paper_context_has_lead_and_relevant(corpus):
    ctx = corpus.paper_context("realm2020", ["retrieval", "pre-training"])
    assert ctx and ctx[0]["page"] <= 2 and all(c["paper_id"] == "realm2020" for c in ctx)


def test_explicitly_named_papers_are_always_included(corpus):
    q = "Compare how REALM and Lewis et al. integrate retrieval into language models"
    assert set(corpus.mentioned_papers(q)) == {"realm2020", "rag_lewis2020"}
    hits = corpus.retrieve(["compare", "retrieval", "language", "models"], max_papers=2, mention_text=q)
    assert {"realm2020", "rag_lewis2020"} <= {h.chunk["paper_id"] for h in hits}


def test_generic_question_names_no_paper(corpus):
    assert corpus.mentioned_papers("Why do papers on RAG evaluation disagree?") == []
    assert corpus.mentioned_papers("What problem does Self-RAG address?") == ["selfrag2023"]
