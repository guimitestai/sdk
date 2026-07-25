"""Modelos de dados principais do Guimí Test AI SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Nível de severidade de alertas e brechas."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceFramework(str, Enum):
    """Frameworks de conformidade suportados."""
    EU_AI_ACT = "eu_ai_act"
    LGPD = "lgpd"
    NIST_AI_RMF = "nist_ai_rmf"
    OWASP_LLM = "owasp_llm"
    ISO_42001 = "iso_42001"


class EvaluationResult(BaseModel):
    """Resultado de uma avaliação LLM-as-Judge."""
    id: str = Field(..., description="ID único da avaliação")
    trace_id: Optional[str] = Field(None, description="ID do trace associado")
    input: str = Field(..., description="Entrada enviada ao modelo")
    output: str = Field(..., description="Saída gerada pelo modelo")
    expected: Optional[str] = Field(None, description="Saída esperada (ground truth)")
    score: float = Field(..., ge=0.0, le=1.0, description="Score de 0 a 1")
    passed: bool = Field(..., description="Se passou no critério de avaliação")
    criteria: str = Field(..., description="Critério de avaliação utilizado")
    reasoning: Optional[str] = Field(None, description="Raciocínio do juiz LLM")
    latency_ms: Optional[int] = Field(None, description="Latência em milissegundos")
    model: Optional[str] = Field(None, description="Modelo avaliado")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    """Evento de trace de observabilidade."""
    id: str = Field(..., description="ID único do trace")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    name: str = Field(..., description="Nome da operação")
    input: Optional[str] = Field(None, description="Entrada da operação")
    output: Optional[str] = Field(None, description="Saída da operação")
    model: Optional[str] = Field(None, description="Modelo utilizado")
    latency_ms: Optional[int] = Field(None, description="Latência em ms")
    tokens_input: Optional[int] = Field(None, description="Tokens de entrada")
    tokens_output: Optional[int] = Field(None, description="Tokens de saída")
    cost_usd: Optional[float] = Field(None, description="Custo estimado em USD")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityAlert(BaseModel):
    """Alerta de segurança detectado pelo Red Teamer."""
    id: str = Field(..., description="ID único do alerta")
    attack_type: str = Field(..., description="Tipo de ataque (ex: prompt_injection)")
    severity: Severity = Field(..., description="Nível de severidade")
    payload: str = Field(..., description="Payload do ataque testado")
    response: str = Field(..., description="Resposta do modelo ao ataque")
    vulnerable: bool = Field(..., description="Se o modelo foi vulnerável")
    owasp_category: Optional[str] = Field(None, description="Categoria OWASP LLM")
    recommendation: Optional[str] = Field(None, description="Recomendação de mitigação")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceGap(BaseModel):
    """Brecha de conformidade identificada."""
    framework: ComplianceFramework
    article: str = Field(..., description="Artigo ou cláusula violada")
    title: str = Field(..., description="Título da brecha")
    description: str = Field(..., description="Descrição detalhada")
    severity: Severity
    recommendation: str = Field(..., description="Recomendação de correção")
    evidence: Optional[str] = Field(None, description="Evidência encontrada")


class ComplianceReport(BaseModel):
    """Relatório de conformidade gerado pelo ComplianceChecker."""
    id: str = Field(..., description="ID único do relatório")
    organization: str = Field(..., description="Nome da organização")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Score geral 0-100")
    frameworks_analyzed: List[ComplianceFramework]
    gaps: List[ComplianceGap] = Field(default_factory=list)
    total_gaps: int = Field(0)
    critical_gaps: int = Field(0)
    high_gaps: int = Field(0)
    medium_gaps: int = Field(0)
    low_gaps: int = Field(0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
