"""
Test Runner — Executa casos de teste gerados contra APIs reais.

Coleta métricas de latência, status, validação de resposta
e integra com o Tracer de observabilidade do Guimí.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from guimitestai.autonomous.generator import TestCase

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@dataclass
class TestResult:
    """Resultado da execução de um caso de teste."""
    test_case: TestCase
    passed: bool = False
    actual_status: int = 0
    expected_status: int = 200
    latency_ms: float = 0.0
    response_body: Optional[Any] = None
    error: Optional[str] = None
    missing_fields: List[str] = field(default_factory=list)
    unexpected_fields: List[str] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def status_passed(self) -> bool:
        return self.actual_status == self.expected_status

    @property
    def category(self) -> str:
        return self.test_case.category

    @property
    def priority(self) -> str:
        return self.test_case.priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_case.id,
            "test_name": self.test_case.name,
            "passed": self.passed,
            "actual_status": self.actual_status,
            "expected_status": self.expected_status,
            "latency_ms": round(self.latency_ms, 2),
            "error": self.error,
            "missing_fields": self.missing_fields,
            "category": self.category,
            "priority": self.priority,
        }


@dataclass
class TestSuiteResult:
    """Resultado de uma suíte completa de testes."""
    results: List[TestResult] = field(default_factory=list)
    base_url: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        latencies = [r.latency_ms for r in self.results if r.latency_ms > 0]
        return sum(latencies) / len(latencies) if latencies else 0.0

    @property
    def duration_seconds(self) -> float:
        return self.finished_at - self.started_at

    @property
    def critical_failures(self) -> List[TestResult]:
        return [r for r in self.results if not r.passed and r.priority == "critical"]

    @property
    def security_failures(self) -> List[TestResult]:
        return [r for r in self.results if not r.passed and r.category == "security"]

    def summary(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate * 100, 1),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "critical_failures": len(self.critical_failures),
            "security_failures": len(self.security_failures),
        }


class TestRunner:
    """
    Executa casos de teste gerados contra APIs reais.

    Suporta execução paralela, retry automático e integração
    com o sistema de observabilidade do Guimí.

    Exemplo:
        spec = await APIDiscovery("http://localhost:8000").discover()
        cases = TestGenerator().generate(spec)
        runner = TestRunner(base_url="http://localhost:8000")
        suite_result = await runner.run(cases)
        print(f"Taxa de aprovação: {suite_result.pass_rate:.0%}")
    """

    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        max_concurrent: int = 5,
        retry_on_failure: int = 1,
        fail_fast: bool = False,
    ):
        """
        Args:
            base_url: URL base da API.
            auth_token: Token Bearer para autenticação.
            timeout: Timeout em segundos por requisição.
            max_concurrent: Máximo de requisições paralelas.
            retry_on_failure: Número de retentativas em caso de falha.
            fail_fast: Parar na primeira falha crítica.
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.retry_on_failure = retry_on_failure
        self.fail_fast = fail_fast

        self._default_headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "guimitestai-runner/1.0",
        }
        if auth_token:
            self._default_headers["Authorization"] = f"Bearer {auth_token}"

    async def run(self, cases: List[TestCase]) -> TestSuiteResult:
        """
        Executa todos os casos de teste.

        Args:
            cases: Lista de TestCase a executar.

        Returns:
            TestSuiteResult com todos os resultados.
        """
        if not HAS_HTTPX:
            raise ImportError(
                "httpx é necessário para o TestRunner. "
                "Instale com: pip install guimitestai[autonomous]"
            )

        suite = TestSuiteResult(base_url=self.base_url)
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_with_semaphore(case: TestCase) -> TestResult:
            async with semaphore:
                return await self._run_case(case)

        tasks = [run_with_semaphore(case) for case in cases]

        if self.fail_fast:
            for task in asyncio.as_completed(tasks):
                result = await task
                suite.results.append(result)
                if not result.passed and result.priority == "critical":
                    break
        else:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, TestResult):
                    suite.results.append(result)
                elif isinstance(result, Exception):
                    # Criar resultado de falha para exceções não tratadas
                    suite.results.append(TestResult(
                        test_case=TestCase(name="Unknown"),
                        passed=False,
                        error=str(result),
                    ))

        suite.finished_at = time.time()
        return suite

    async def run_single(self, case: TestCase) -> TestResult:
        """Executa um único caso de teste."""
        return await self._run_case(case)

    async def _run_case(self, case: TestCase, attempt: int = 0) -> TestResult:
        """Executa um caso de teste com retry automático."""
        url = f"{self.base_url}{case.full_path}"
        headers = {**self._default_headers, **case.headers}

        # Remover Authorization se o caso testa 401
        if case.expected_status == 401 and "Authorization" in headers:
            del headers["Authorization"]

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                request_kwargs: Dict[str, Any] = {
                    "method": case.method,
                    "url": url,
                    "headers": headers,
                    "params": case.query_params or None,
                }

                if case.body is not None:
                    request_kwargs["json"] = case.body

                response = await client.request(**request_kwargs)
                latency_ms = (time.time() - start_time) * 1000

                # Parsear resposta
                response_body = None
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text[:500] if response.text else None

                # Validar status
                status_passed = response.status_code == case.expected_status

                # Validar campos esperados na resposta
                missing_fields: List[str] = []
                if case.expected_fields and isinstance(response_body, dict):
                    missing_fields = [
                        f for f in case.expected_fields
                        if f not in response_body
                    ]

                # Verificar campos que NÃO devem estar na resposta (ex: senhas, tokens)
                unexpected_fields: List[str] = []
                if case.expected_not_fields and isinstance(response_body, dict):
                    unexpected_fields = [
                        f for f in case.expected_not_fields
                        if f in response_body
                    ]

                passed = status_passed and not missing_fields and not unexpected_fields

                # Retry em caso de erro de servidor (5xx) e não for o último attempt
                if not passed and response.status_code >= 500 and attempt < self.retry_on_failure:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    return await self._run_case(case, attempt + 1)

                return TestResult(
                    test_case=case,
                    passed=passed,
                    actual_status=response.status_code,
                    expected_status=case.expected_status,
                    latency_ms=latency_ms,
                    response_body=response_body,
                    missing_fields=missing_fields,
                    unexpected_fields=unexpected_fields,
                    assertions=[
                        {"name": "status_code", "passed": status_passed,
                         "expected": case.expected_status, "actual": response.status_code},
                        {"name": "required_fields", "passed": not missing_fields,
                         "missing": missing_fields},
                    ],
                )

        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                test_case=case,
                passed=False,
                latency_ms=latency_ms,
                error=f"Timeout após {self.timeout}s",
            )
        except httpx.ConnectError as e:
            return TestResult(
                test_case=case,
                passed=False,
                error=f"Falha de conexão: {e}",
            )
        except Exception as e:
            return TestResult(
                test_case=case,
                passed=False,
                error=f"Erro inesperado: {e}",
            )
