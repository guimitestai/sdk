"""Local demonstration without an API key or paid LLM."""
from pathlib import Path
from uuid import uuid4

from guimitestai.core.models import EvaluationResult
from guimitestai.evidence import build_evidence, load_evidence, save_evidence

expected = "Brasília"
actual = "Brasília"
result = EvaluationResult(
    id=str(uuid4()),
    input="Qual é a capital do Brasil?",
    output=actual,
    expected=expected,
    criteria="exact_match",
    score=float(actual == expected),
    passed=actual == expected,
    reasoning="Deterministic exact match; no LLM judge used.",
)
record = build_evidence(result, context={"demo": "guimi-001"})
path = save_evidence(record, Path("artifacts") / "evidence.json")
print(f"Evidence saved: {path}")
print(f"Verified: {load_evidence(path).sha256 == record.sha256}")
