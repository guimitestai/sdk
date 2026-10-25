"""Portable, deterministic evidence artifacts for Guimi evaluations.

No external agent framework or paid model is required.
Input/output can contain personal data: callers control storage and redaction.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from guimitestai.core.models import EvaluationResult


class EvidenceRecord(BaseModel):
    schema_version: str = "1.0"
    evaluation: EvaluationResult
    source: str = "guimi-sdk"
    context: Dict[str, Any] = Field(default_factory=dict)
    sha256: str


def _canonical(data: Dict[str, Any]) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")


def build_evidence(
    evaluation: EvaluationResult,
    *,
    source: str = "guimi-sdk",
    context: Optional[Dict[str, Any]] = None,
) -> EvidenceRecord:
    """Hash the canonical evidence payload; hash excludes the hash field itself."""
    payload = {
        "schema_version": "1.0",
        "evaluation": evaluation.model_dump(mode="json"),
        "source": source,
        "context": context or {},
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return EvidenceRecord(**payload, sha256=digest)


def verify_evidence(record: EvidenceRecord) -> bool:
    payload = record.model_dump(mode="json", exclude={"sha256"})
    return hashlib.sha256(_canonical(payload)).hexdigest() == record.sha256


def save_evidence(record: EvidenceRecord, path: str | Path) -> Path:
    """Write evidence to an explicit path; do not auto-upload sensitive data."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return destination


def load_evidence(path: str | Path) -> EvidenceRecord:
    record = EvidenceRecord.model_validate_json(Path(path).read_text(encoding="utf-8"))
    if not verify_evidence(record):
        raise ValueError("Evidence integrity verification failed")
    return record
