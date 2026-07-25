"""Verificador de conformidade regulatória para sistemas de IA."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from guimitestai.core.models import (
    ComplianceFramework,
    ComplianceGap,
    ComplianceReport,
    Severity,
)


class ComplianceChecker:
    """Verificador de conformidade regulatória para sistemas de IA.

    Analisa um conjunto de métricas e traces para identificar brechas
    em relação a frameworks regulatórios como LGPD e EU AI Act.

    Exemplo:
        >>> from guimitestai.compliance import ComplianceChecker
        >>> from guimitestai.core.models import ComplianceFramework
        >>>
        >>> checker = ComplianceChecker()
        >>> report = checker.analyze(
        ...     organization="Minha Empresa",
        ...     metrics={
        ...         "has_audit_trail": True,
        ...         "has_human_oversight": False,
        ...         "pii_detected_count": 5,
        ...         "explainability_score": 0.3,
        ...     },
        ...     frameworks=[ComplianceFramework.LGPD, ComplianceFramework.EU_AI_ACT]
        ... )
        >>> print(f"Score: {report.overall_score:.1f}%")
        >>> print(f"Brechas críticas: {report.critical_gaps}")
    """

    def analyze(
        self,
        organization: str,
        metrics: Dict[str, Any],
        frameworks: Optional[List[ComplianceFramework]] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> ComplianceReport:
        """Analisa métricas e gera relatório de conformidade.

        Args:
            organization: Nome da organização.
            metrics: Dicionário de métricas do sistema de IA.
            frameworks: Frameworks a verificar. Se None, verifica todos.
            period_start: Início do período de análise.
            period_end: Fim do período de análise.

        Returns:
            ComplianceReport com score, gaps e recomendações.
        """
        frameworks_to_check = frameworks or list(ComplianceFramework)
        all_gaps: List[ComplianceGap] = []

        for framework in frameworks_to_check:
            gaps = self._check_framework(framework, metrics)
            all_gaps.extend(gaps)

        critical = sum(1 for g in all_gaps if g.severity == Severity.CRITICAL)
        high = sum(1 for g in all_gaps if g.severity == Severity.HIGH)
        medium = sum(1 for g in all_gaps if g.severity == Severity.MEDIUM)
        low = sum(1 for g in all_gaps if g.severity == Severity.LOW)

        # Score: começa em 100, desconta por severidade
        score = 100.0
        score -= critical * 15
        score -= high * 8
        score -= medium * 4
        score -= low * 1
        score = max(0.0, min(100.0, score))

        return ComplianceReport(
            id=str(uuid.uuid4()),
            organization=organization,
            overall_score=score,
            frameworks_analyzed=frameworks_to_check,
            gaps=all_gaps,
            total_gaps=len(all_gaps),
            critical_gaps=critical,
            high_gaps=high,
            medium_gaps=medium,
            low_gaps=low,
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
        )

    def _check_framework(
        self, framework: ComplianceFramework, metrics: Dict[str, Any]
    ) -> List[ComplianceGap]:
        """Verifica um framework específico."""
        if framework == ComplianceFramework.LGPD:
            return self._check_lgpd(metrics)
        elif framework == ComplianceFramework.EU_AI_ACT:
            return self._check_eu_ai_act(metrics)
        elif framework == ComplianceFramework.NIST_AI_RMF:
            return self._check_nist(metrics)
        elif framework == ComplianceFramework.OWASP_LLM:
            return self._check_owasp(metrics)
        elif framework == ComplianceFramework.ISO_42001:
            return self._check_iso42001(metrics)
        return []

    def _check_lgpd(self, m: Dict[str, Any]) -> List[ComplianceGap]:
        gaps = []
        if m.get("pii_detected_count", 0) > 0:
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.LGPD,
                article="Art. 46",
                title="Dados pessoais expostos em respostas",
                description=f"{m['pii_detected_count']} ocorrências de PII detectadas nas respostas do modelo.",
                severity=Severity.CRITICAL,
                recommendation="Implemente filtros de PII nas saídas do modelo e revise o acesso a dados pessoais.",
                evidence=f"pii_detected_count={m['pii_detected_count']}",
            ))
        if not m.get("has_audit_trail", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.LGPD,
                article="Art. 37",
                title="Ausência de registro de operações de tratamento",
                description="O sistema não mantém registro das operações de tratamento de dados pessoais.",
                severity=Severity.HIGH,
                recommendation="Implemente audit trail completo de todas as operações com dados pessoais.",
            ))
        if not m.get("has_consent_mechanism", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.LGPD,
                article="Art. 6",
                title="Ausência de mecanismo de consentimento",
                description="Não há mecanismo documentado para coleta e gestão de consentimento dos titulares.",
                severity=Severity.HIGH,
                recommendation="Implemente fluxo de consentimento explícito conforme Art. 7 da LGPD.",
            ))
        return gaps

    def _check_eu_ai_act(self, m: Dict[str, Any]) -> List[ComplianceGap]:
        gaps = []
        if not m.get("has_human_oversight", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.EU_AI_ACT,
                article="Art. 14",
                title="Ausência de supervisão humana",
                description="O sistema de IA não possui mecanismo de supervisão humana obrigatório para sistemas de alto risco.",
                severity=Severity.CRITICAL,
                recommendation="Implemente ponto de revisão humana para decisões de alto impacto.",
            ))
        explainability = m.get("explainability_score", 1.0)
        if explainability < 0.5:
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.EU_AI_ACT,
                article="Art. 13",
                title="Transparência insuficiente",
                description=f"Score de explicabilidade ({explainability:.2f}) abaixo do mínimo recomendado (0.5).",
                severity=Severity.HIGH,
                recommendation="Adicione explicações das decisões do modelo e documentação técnica acessível.",
                evidence=f"explainability_score={explainability}",
            ))
        if not m.get("has_risk_assessment", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.EU_AI_ACT,
                article="Art. 9",
                title="Ausência de avaliação de risco",
                description="Não há sistema de gestão de riscos documentado conforme exigido pelo EU AI Act.",
                severity=Severity.HIGH,
                recommendation="Conduza e documente avaliação de risco conforme Anexo III do EU AI Act.",
            ))
        return gaps

    def _check_nist(self, m: Dict[str, Any]) -> List[ComplianceGap]:
        gaps = []
        if not m.get("has_model_card", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.NIST_AI_RMF,
                article="GOVERN 1.1",
                title="Ausência de Model Card",
                description="O modelo não possui documentação padronizada (Model Card) descrevendo capacidades e limitações.",
                severity=Severity.MEDIUM,
                recommendation="Crie um Model Card seguindo o padrão do NIST AI RMF GOVERN.",
            ))
        error_rate = m.get("error_rate", 0.0)
        if error_rate > 0.05:
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.NIST_AI_RMF,
                article="MEASURE 2.5",
                title="Taxa de erros elevada",
                description=f"Taxa de erros ({error_rate:.1%}) acima do limiar aceitável (5%).",
                severity=Severity.HIGH,
                recommendation="Investigue causas raiz dos erros e implemente monitoramento contínuo.",
                evidence=f"error_rate={error_rate:.3f}",
            ))
        return gaps

    def _check_owasp(self, m: Dict[str, Any]) -> List[ComplianceGap]:
        gaps = []
        if m.get("prompt_injection_vulnerable", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.OWASP_LLM,
                article="LLM01",
                title="Vulnerabilidade a Prompt Injection",
                description="O modelo é vulnerável a ataques de prompt injection detectados no red teaming.",
                severity=Severity.CRITICAL,
                recommendation="Implemente validação de entrada, sanitização e separação de instruções/dados.",
            ))
        if m.get("jailbreak_vulnerable", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.OWASP_LLM,
                article="LLM01",
                title="Vulnerabilidade a Jailbreak",
                description="O modelo pode ser manipulado para ignorar suas diretrizes de segurança.",
                severity=Severity.CRITICAL,
                recommendation="Reforce o system prompt, adicione guardrails e monitore padrões de jailbreak.",
            ))
        return gaps

    def _check_iso42001(self, m: Dict[str, Any]) -> List[ComplianceGap]:
        gaps = []
        if not m.get("has_ai_policy", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.ISO_42001,
                article="Cláusula 5.2",
                title="Ausência de política de IA documentada",
                description="A organização não possui política formal de uso responsável de IA.",
                severity=Severity.MEDIUM,
                recommendation="Elabore e aprove política de IA alinhada à ISO/IEC 42001:2023.",
            ))
        if not m.get("has_continuous_monitoring", False):
            gaps.append(ComplianceGap(
                framework=ComplianceFramework.ISO_42001,
                article="Cláusula 9.1",
                title="Ausência de monitoramento contínuo",
                description="Não há processo de monitoramento e avaliação contínua do sistema de IA.",
                severity=Severity.HIGH,
                recommendation="Implemente ciclo de monitoramento contínuo com métricas e alertas automáticos.",
            ))
        return gaps
