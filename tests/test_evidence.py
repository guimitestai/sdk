"""GUIMI-001: evidence contract and integrity regression tests."""
from datetime import datetime, timezone

import pytest

from guimitestai.core.models import EvaluationResult
from guimitestai.evidence import (
    build_evidence,
    load_evidence,
    save_evidence,
    verify_evidence,
)


def sample_result():
    return EvaluationResult(
        id="case-001",
        input="Capital do Brasil?",
        output="Brasília",
        expected="Brasília",
        score=1.0,
        passed=True,
        criteria="correctness",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_evidence_round_trip(tmp_path):
    record = build_evidence(sample_result(), context={"suite": "smoke"})
    path = save_evidence(record, tmp_path / "evidence.json")
    loaded = load_evidence(path)
    assert loaded.evaluation.id == "case-001"
    assert loaded.context["suite"] == "smoke"
    assert verify_evidence(loaded)


def test_evidence_is_deterministic():
    result = sample_result()
    assert build_evidence(result).sha256 == build_evidence(result).sha256


def test_evidence_detects_tampering(tmp_path):
    record = build_evidence(sample_result())
    record.evaluation.output = "Rio de Janeiro"
    assert not verify_evidence(record)
    path = save_evidence(record, tmp_path / "tampered.json")
    with pytest.raises(ValueError, match="integrity"):
        load_evidence(path)


def test_evidence_context_changes_hash():
    result = sample_result()
    assert build_evidence(result, context={"run": "a"}).sha256 != build_evidence(
        result, context={"run": "b"}
    ).sha256
