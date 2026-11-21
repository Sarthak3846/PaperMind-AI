"""Citation verification stage (P8 + code checks).

Order of checks for every claim:
 1. code: no citation / fabricated chunk IDs  -> 'unsupported' (no LLM call needed)
 2. LLM (P8): supported / partially_supported / unsupported against the cited passages only
 3. code: numbers in the claim must appear in the cited passages, otherwise 'supported' is
    downgraded to 'partially_supported'
If the verifier call fails the claim is marked 'unverified' - it is never silently treated as verified."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from agents.common import BaseAgent, dumps, unsupported_numbers
from app.llm import LLMError
from app.schemas import VerificationOut

BATCH = 6
MAX_PASSAGES_PER_CLAIM = 4
MAX_CHARS_PER_PASSAGE = 1300


@dataclass
class VItem:
    sid: str
    text: str
    chunk_ids: list[str]
    invalid_chunk_ids: list[str] = field(default_factory=list)


@dataclass
class VResult:
    status: str
    reason: str


class CitationVerifier(BaseAgent):
    name = "CitationVerifier"
    prompt_id = "P8"

    def run(self, items: list[VItem], on_batch: Callable[[int, int], None] | None = None) -> dict[str, VResult]:
        results: dict[str, VResult] = {}
        to_check: list[VItem] = []
        for it in items:
            valid = [c for c in it.chunk_ids if self.corpus.has_chunk(c)]
            if not it.chunk_ids and not it.invalid_chunk_ids:
                results[it.sid] = VResult("unsupported", "No source passage is cited for this claim.")
            elif not valid:
                results[it.sid] = VResult("unsupported", "Fabricated reference: cited chunk ID(s) "
                                          f"{', '.join(it.invalid_chunk_ids or it.chunk_ids)} do not exist in the corpus.")
            else:
                it.chunk_ids = valid
                to_check.append(it)

        batches = [to_check[i:i + BATCH] for i in range(0, len(to_check), BATCH)]
        for n, batch in enumerate(batches, start=1):
            if on_batch:
                on_batch(n, len(batches))
            payload = []
            for it in batch:
                passages = []
                for cid in it.chunk_ids[:MAX_PASSAGES_PER_CLAIM]:
                    ch = self.corpus.chunk(cid)
                    passages.append({"chunk_id": cid, "text": ch["text"][:MAX_CHARS_PER_PASSAGE]})
                payload.append({"sid": it.sid, "claim": it.text, "passages": passages})
            try:
                out = self.llm.call_json(self.spec, VerificationOut, claims_json=dumps(payload))
            except LLMError as exc:
                for it in batch:
                    results[it.sid] = VResult("unverified", f"Verifier unavailable: {str(exc)[:120]}")
                continue
            verdicts = {v.sid: v for v in out.verdicts}
            for it in batch:
                v = verdicts.get(it.sid)
                if v is None:
                    results[it.sid] = VResult("unverified", "The verifier returned no verdict for this claim.")
                    continue
                status, reason = v.verdict, v.reason
                texts = [self.corpus.chunk(c)["text"] for c in it.chunk_ids]
                bad = unsupported_numbers(it.text, texts)
                if bad and status == "supported":
                    status = "partially_supported"
                    reason = (reason + " " if reason else "") + f"Number(s) {', '.join(sorted(bad))} not found in the cited passages."
                if it.invalid_chunk_ids:
                    reason = (reason + " " if reason else "") + f"Ignored non-existent reference(s): {', '.join(it.invalid_chunk_ids)}."
                results[it.sid] = VResult(status, reason)
        return results
