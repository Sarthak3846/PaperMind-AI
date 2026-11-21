"""Pydantic schemas: the contracts between prompts, agents, API and frontend.
Every LLM output is validated against one of the *Out / report models below."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------- P1 query understanding
TaskType = Literal["factual", "paper_analysis", "comparison", "gap_identification", "literature_review"]


class QueryUnderstanding(_Base):
    task_type: TaskType = "literature_review"
    keywords: list[str] = Field(min_length=1, max_length=20)
    sub_questions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- P2 evidence extraction
EvidenceKind = Literal["fact", "metric", "definition", "method", "limitation", "future_work", "other"]


class EvidenceItem(_Base):
    chunk_id: str
    quote: str
    claim: str
    kind: EvidenceKind = "fact"


class EvidenceExtraction(_Base):
    evidence: list[EvidenceItem] = Field(default_factory=list)


class Evidence(EvidenceItem):
    """Evidence after code-level validation (id and verbatim quote checked)."""
    evidence_id: str
    paper_id: str
    page: int


# ---------------------------------------------------------------- P5 critic
class CriticFlag(_Base):
    evidence_id: str
    reason: str


class CriticReport(_Base):
    validated_ids: list[str] = Field(default_factory=list)
    flagged: list[CriticFlag] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- P3 paper analysis
class Claim(_Base):
    text: str
    chunk_ids: list[str] = Field(default_factory=list)


class QuantResult(_Base):
    metric: str
    value: str
    context: Optional[str] = None
    chunk_ids: list[str] = Field(default_factory=list)


class PaperAnalysisOut(_Base):
    research_problem: Optional[Claim] = None
    objectives: list[Claim] = Field(default_factory=list)
    methodology: list[Claim] = Field(default_factory=list)
    datasets: list[Claim] = Field(default_factory=list)
    findings: list[Claim] = Field(default_factory=list)
    quantitative_results: list[QuantResult] = Field(default_factory=list)
    limitations: list[Claim] = Field(default_factory=list)
    future_directions: list[Claim] = Field(default_factory=list)


class PaperAnalysis(PaperAnalysisOut):
    paper_id: str
    title: str
    filename: str
    chunk_ids_provided: list[str] = Field(default_factory=list)
    pages_provided: list[int] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    rejected_claims: int = 0


# ---------------------------------------------------------------- P4 comparison
class DimEntry(_Base):
    paper_id: str
    value: str
    chunk_ids: list[str] = Field(default_factory=list)


class DimRow(_Base):
    dimension: Literal["methodology", "datasets", "evaluation_metrics", "findings"]
    entries: list[DimEntry] = Field(default_factory=list)


class Statement(_Base):
    text: str
    paper_ids: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)


class Position(_Base):
    paper_id: str
    statement: str
    chunk_ids: list[str] = Field(default_factory=list)


class Contradiction(_Base):
    topic: str
    positions: list[Position] = Field(default_factory=list)
    conditions_comparable: bool = True
    explanation: str = ""


class Incompatibility(_Base):
    paper_ids: list[str] = Field(default_factory=list)
    reason: str


class ComparisonOut(_Base):
    comparable: bool = True
    comparability_notes: str = ""
    table: list[DimRow] = Field(default_factory=list)
    similarities: list[Statement] = Field(default_factory=list)
    differences: list[Statement] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    incompatibilities: list[Incompatibility] = Field(default_factory=list)


class Comparison(ComparisonOut):
    skipped: bool = False
    skip_reason: str = ""
    rejected_items: int = 0


# ---------------------------------------------------------------- P6 research gaps
class GapOut(_Base):
    title: str
    description: str
    why_it_exists: str
    basis: Literal["explicit", "inferred"] = "inferred"
    supporting_paper_ids: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)


class GapsOut(_Base):
    gaps: list[GapOut] = Field(default_factory=list)


class Gap(GapOut):
    gap_id: str
    global_claim_flag: bool = False
    note: str = ""
    status: Optional[str] = None            # supported / partially_supported / unsupported / unverified
    status_reason: Optional[str] = None


class GapsResult(_Base):
    gaps: list[Gap] = Field(default_factory=list)
    scope_disclaimer: str = ""
    rejected_items: int = 0


# ---------------------------------------------------------------- P7 literature review
VerifStatus = Literal["supported", "partially_supported", "unsupported", "unverified"]


class ReviewStatement(_Base):
    text: str
    chunk_ids: list[str] = Field(default_factory=list)
    sid: Optional[str] = None
    invalid_chunk_ids: list[str] = Field(default_factory=list)
    meta: bool = False  # describes the scope of the review itself; needs no citation
    status: Optional[VerifStatus] = None
    status_reason: Optional[str] = None


class PaperSummary(_Base):
    paper_id: str
    statements: list[ReviewStatement] = Field(default_factory=list)


class ReviewOut(_Base):
    research_overview: list[ReviewStatement] = Field(default_factory=list)
    paper_summaries: list[PaperSummary] = Field(default_factory=list)
    cross_paper_synthesis: list[ReviewStatement] = Field(default_factory=list)
    agreements_and_contradictions: list[ReviewStatement] = Field(default_factory=list)
    research_gaps: list[ReviewStatement] = Field(default_factory=list)
    limitations: list[ReviewStatement] = Field(default_factory=list)
    conclusion: list[ReviewStatement] = Field(default_factory=list)


# ---------------------------------------------------------------- P8 verification
class VerdictItem(_Base):
    sid: str
    verdict: Literal["supported", "partially_supported", "unsupported"]
    reason: str = ""


class VerificationOut(_Base):
    verdicts: list[VerdictItem] = Field(default_factory=list)


# ---------------------------------------------------------------- API
class ResearchRequest(_Base):
    question: str = Field(max_length=1000)
    paper_ids: Optional[list[str]] = None
    max_papers: int = Field(default=4, ge=1, le=6)
