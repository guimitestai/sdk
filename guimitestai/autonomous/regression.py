"""
Regression Detector — Detecta regressões comparando runs de teste.

Compara resultados de execuções anteriores e identifica:
- Testes que passaram e agora falham (regressões)
- Degradação de performance (latência aumentou)
- Novos endpoints sem cobertura de teste
- Mudanças de contrato (status codes diferentes)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from guimitestai.autonomous.runner import TestResult, TestSuiteResult


@dataclass
class Regression:
    """Representa uma regressão detectada."""
    test_id: str
    test_name: str
    type: str  # status_change | latency_degradation | new_failure | contract_change
    severity: str  # critical | high | medium | low
    description: str
    previous_value: Any = None
    current_value: Any = None
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "recommendation": self.recommendation,
        }


@dataclass
class RegressionReport:
    """Relatório completo de regressões detectadas."""
    regressions: List[Regression] = field(default_factory=list)
    improvements: List[Dict[str, Any]] = field(default_factory=list)
    new_tests: List[str] = field(default_factory=list)
    removed_tests: List[str] = field(default_factory=list)
    baseline_pass_rate: float = 0.0
    current_pass_rate: float = 0.0
    baseline_avg_latency: float = 0.0
    current_avg_latency: float = 0.0
    generated_at: float = field(default_factory=time.time)

    @property
    def has_regressions(self) -> bool:
        return len(self.regressions) > 0

    @property
    def critical_regressions(self) -> List[Regression]:
        return [r for r in self.regressions if r.severity == "critical"]

    @property
    def pass_rate_delta(self) -> float:
        return self.current_pass_rate - self.baseline_pass_rate

    @property
    def latency_delta_ms(self) -> float:
        return self.current_avg_latency - self.baseline_avg_latency

    def summary(self) -> Dict[str, Any]:
        return {
            "has_regressions": self.has_regressions,
            "total_regressions": len(self.regressions),
            "critical_regressions": len(self.critical_regressions),
            "improvements": len(self.improvements),
            "pass_rate_delta": round(self.pass_rate_delta * 100, 1),
            "latency_delta_ms": round(self.latency_delta_ms, 2),
            "baseline_pass_rate": round(self.baseline_pass_rate * 100, 1),
            "current_pass_rate": round(self.current_pass_rate * 100, 1),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "regressions": [r.to_dict() for r in self.regressions],
            "improvements": self.improvements,
            "new_tests": self.new_tests,
            "removed_tests": self.removed_tests,
            "generated_at": self.generated_at,
        }


class RegressionDetector:
    """
    Detecta regressões comparando runs de teste.

    Persiste resultados em arquivo JSON local e compara
    com a execução atual para identificar degradações.

    Exemplo:
        detector = RegressionDetector(baseline_file="baseline.json")

        # Primeira execução — salva como baseline
        await detector.save_baseline(suite_result)

        # Execuções seguintes — detecta regressões
        report = detector.detect(suite_result)
        if report.has_regressions:
            print(f"⚠️ {len(report.regressions)} regressões detectadas!")
    """

    # Thresholds de detecção
    LATENCY_REGRESSION_THRESHOLD = 1.5   # 50% mais lento = regressão
    LATENCY_CRITICAL_THRESHOLD = 3.0     # 200% mais lento = crítico
    PASS_RATE_REGRESSION_THRESHOLD = 0.05  # queda de 5% na taxa = regressão

    def __init__(
        self,
        baseline_file: str = ".guimi-baseline.json",
        latency_threshold: float = 1.5,
        auto_update_baseline: bool = False,
    ):
        """
        Args:
            baseline_file: Caminho do arquivo JSON com resultados baseline.
            latency_threshold: Multiplicador de latência para considerar regressão.
            auto_update_baseline: Atualizar baseline automaticamente após cada run.
        """
        self.baseline_file = Path(baseline_file)
        self.latency_threshold = latency_threshold
        self.auto_update_baseline = auto_update_baseline

    def detect(self, current: TestSuiteResult) -> RegressionReport:
        """
        Detecta regressões comparando com o baseline salvo.

        Args:
            current: Resultado da execução atual.

        Returns:
            RegressionReport com regressões e melhorias detectadas.
        """
        baseline_data = self._load_baseline()

        if not baseline_data:
            # Sem baseline — salvar como primeiro baseline
            self.save_baseline(current)
            return RegressionReport(
                current_pass_rate=current.pass_rate,
                current_avg_latency=current.avg_latency_ms,
                baseline_pass_rate=current.pass_rate,
                baseline_avg_latency=current.avg_latency_ms,
            )

        report = RegressionReport(
            baseline_pass_rate=baseline_data.get("pass_rate", 0),
            current_pass_rate=current.pass_rate,
            baseline_avg_latency=baseline_data.get("avg_latency_ms", 0),
            current_avg_latency=current.avg_latency_ms,
        )

        baseline_results = {
            r["test_id"]: r
            for r in baseline_data.get("results", [])
        }
        current_results = {r.test_case.id: r for r in current.results}

        # Detectar novos testes (sem baseline)
        report.new_tests = [
            tid for tid in current_results
            if tid not in baseline_results
        ]

        # Detectar testes removidos
        report.removed_tests = [
            tid for tid in baseline_results
            if tid not in current_results
        ]

        # Comparar resultados comuns
        for test_id, current_result in current_results.items():
            if test_id not in baseline_results:
                continue

            baseline_result = baseline_results[test_id]
            regressions = self._compare_results(baseline_result, current_result)
            report.regressions.extend(regressions)

            # Detectar melhorias
            improvements = self._detect_improvements(baseline_result, current_result)
            report.improvements.extend(improvements)

        # Detectar degradação geral de taxa de aprovação
        if (baseline_data.get("pass_rate", 0) - current.pass_rate) > self.PASS_RATE_REGRESSION_THRESHOLD:
            report.regressions.append(Regression(
                test_id="suite",
                test_name="Suite Completa",
                type="pass_rate_degradation",
                severity="high",
                description=(
                    f"Taxa de aprovação caiu de "
                    f"{baseline_data.get('pass_rate', 0):.0%} para "
                    f"{current.pass_rate:.0%}"
                ),
                previous_value=f"{baseline_data.get('pass_rate', 0):.0%}",
                current_value=f"{current.pass_rate:.0%}",
                recommendation="Investigar os testes que passaram a falhar nesta execução.",
            ))

        if self.auto_update_baseline and not report.has_regressions:
            self.save_baseline(current)

        return report

    def _compare_results(
        self,
        baseline: Dict[str, Any],
        current: TestResult,
    ) -> List[Regression]:
        """Compara um resultado individual com o baseline."""
        regressions: List[Regression] = []
        test_id = current.test_case.id
        test_name = current.test_case.name

        # 1. Passou → Falhou (regressão de status)
        if baseline.get("passed") and not current.passed:
            severity = "critical" if current.priority == "critical" else "high"
            regressions.append(Regression(
                test_id=test_id,
                test_name=test_name,
                type="new_failure",
                severity=severity,
                description=f"Teste passou no baseline mas falhou agora: {current.error or 'status inesperado'}",
                previous_value="PASSED",
                current_value=f"FAILED (status {current.actual_status})",
                recommendation=(
                    f"Verificar mudanças recentes no endpoint "
                    f"{current.test_case.method} {current.test_case.path}"
                ),
            ))

        # 2. Status code mudou
        baseline_status = baseline.get("actual_status", 0)
        if baseline_status and current.actual_status and baseline_status != current.actual_status:
            regressions.append(Regression(
                test_id=test_id,
                test_name=test_name,
                type="contract_change",
                severity="high",
                description=(
                    f"Status code mudou de {baseline_status} para {current.actual_status}. "
                    f"Possível quebra de contrato de API."
                ),
                previous_value=baseline_status,
                current_value=current.actual_status,
                recommendation="Verificar se houve mudança intencional no contrato da API e atualizar os testes.",
            ))

        # 3. Degradação de latência
        baseline_latency = baseline.get("latency_ms", 0)
        if baseline_latency and current.latency_ms:
            ratio = current.latency_ms / baseline_latency
            if ratio >= self.LATENCY_CRITICAL_THRESHOLD:
                regressions.append(Regression(
                    test_id=test_id,
                    test_name=test_name,
                    type="latency_degradation",
                    severity="critical",
                    description=(
                        f"Latência aumentou {ratio:.1f}x: "
                        f"{baseline_latency:.0f}ms → {current.latency_ms:.0f}ms"
                    ),
                    previous_value=f"{baseline_latency:.0f}ms",
                    current_value=f"{current.latency_ms:.0f}ms",
                    recommendation="Investigar gargalos de performance — possível N+1, lock de banco ou memory leak.",
                ))
            elif ratio >= self.latency_threshold:
                regressions.append(Regression(
                    test_id=test_id,
                    test_name=test_name,
                    type="latency_degradation",
                    severity="medium",
                    description=(
                        f"Latência aumentou {ratio:.1f}x: "
                        f"{baseline_latency:.0f}ms → {current.latency_ms:.0f}ms"
                    ),
                    previous_value=f"{baseline_latency:.0f}ms",
                    current_value=f"{current.latency_ms:.0f}ms",
                    recommendation="Monitorar tendência de latência nas próximas execuções.",
                ))

        return regressions

    def _detect_improvements(
        self,
        baseline: Dict[str, Any],
        current: TestResult,
    ) -> List[Dict[str, Any]]:
        """Detecta melhorias em relação ao baseline."""
        improvements = []

        # Falhou → Passou
        if not baseline.get("passed") and current.passed:
            improvements.append({
                "test_id": current.test_case.id,
                "test_name": current.test_case.name,
                "type": "fixed",
                "description": "Teste que falhava no baseline agora passa",
            })

        # Latência melhorou significativamente
        baseline_latency = baseline.get("latency_ms", 0)
        if baseline_latency and current.latency_ms:
            ratio = current.latency_ms / baseline_latency
            if ratio < 0.7:  # 30% mais rápido
                improvements.append({
                    "test_id": current.test_case.id,
                    "test_name": current.test_case.name,
                    "type": "performance_improvement",
                    "description": (
                        f"Latência melhorou {(1-ratio):.0%}: "
                        f"{baseline_latency:.0f}ms → {current.latency_ms:.0f}ms"
                    ),
                })

        return improvements

    def save_baseline(self, suite_result: TestSuiteResult) -> None:
        """Salva os resultados como novo baseline."""
        data = {
            "saved_at": time.time(),
            "pass_rate": suite_result.pass_rate,
            "avg_latency_ms": suite_result.avg_latency_ms,
            "total": suite_result.total,
            "results": [r.to_dict() for r in suite_result.results],
        }
        self.baseline_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _load_baseline(self) -> Optional[Dict[str, Any]]:
        """Carrega o baseline do arquivo JSON."""
        if not self.baseline_file.exists():
            return None
        try:
            return json.loads(self.baseline_file.read_text())
        except Exception:
            return None

    def clear_baseline(self) -> None:
        """Remove o arquivo de baseline."""
        if self.baseline_file.exists():
            self.baseline_file.unlink()
