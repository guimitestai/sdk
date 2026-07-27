"""Cliente HTTP para a API Guimí Test AI.

Toda a inteligência (scoring, compliance, red teaming avançado, relatórios PDF)
reside no servidor da API Guimí. Este cliente é apenas o canal de comunicação.

Funcionalidades GRATUITAS (sem API key):
  - evaluate() com critérios: correctness, helpfulness
  - trace() e get_traces()
  - red_team() com perfil 'quick' (3 ataques básicos)

Funcionalidades PREMIUM (requerem API key — guimitestai.com/upgrade):
  - evaluate() com critérios: faithfulness, safety, lgpd_compliance, safety_advanced
  - compliance_report() — LGPD, EU AI Act, NIST, OWASP, ISO 42001
  - red_team() com perfis avançados — OWASP LLM Top 10 completo
  - generate_pdf_report() — relatório PDF de compliance
  - garak_scan() — integração Garak com perfis avançados
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from guimitestai.core.config import GuimiConfig
from guimitestai.core.models import (
    ComplianceFramework,
    ComplianceReport,
    EvaluationResult,
    SecurityAlert,
    TraceEvent,
)

# Critérios gratuitos — lógica básica no servidor
_FREE_CRITERIA = {"correctness", "helpfulness"}
# Critérios premium — algoritmos proprietários no servidor
_PREMIUM_CRITERIA = {"faithfulness", "safety", "lgpd_compliance", "safety_advanced", "relevance", "coherence"}
# Perfis de red teaming gratuitos
_FREE_RT_PROFILES = {"quick"}
# Perfis premium — payloads e lógica nunca expostos no SDK
_PREMIUM_RT_PROFILES = {"owasp_llm_top10", "security", "lgpd", "eu_ai_act", "full"}


class GuimiClient:
    """Cliente principal do Guimí Test AI.

    Integra avaliação LLM-as-Judge, observabilidade, red teaming e
    compliance em uma única interface unificada.

    Exemplo:
        >>> import asyncio
        >>> from guimitestai import GuimiClient
        >>>
        >>> async def main():
        ...     client = GuimiClient(api_url="http://localhost:3000")
        ...     result = await client.evaluate(
        ...         input="Qual é a capital do Brasil?",
        ...         output="Brasília",
        ...         criteria="correctness"
        ...     )
        ...     print(f"Score: {result.score} | Passou: {result.passed}")
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[GuimiConfig] = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("GUIMI_API_KEY")
        self.config = config or GuimiConfig(
            api_url=api_url or "https://guimitestai.com",
            api_key=resolved_key,
        )
        self._http = httpx.AsyncClient(
            base_url=self.config.api_url,
            timeout=self.config.timeout,
            headers=self._build_headers(),
        )

    def _is_premium(self) -> bool:
        """Verifica se a API key está configurada (plano premium)."""
        return bool(self.config.api_key)

    def _require_premium(self, feature: str) -> None:
        """Lança PermissionError com mensagem clara se não for premium."""
        if not self._is_premium():
            raise PermissionError(
                f"\n\n\U0001f512 '{feature}' é uma funcionalidade premium do Guimí Test AI.\n\n"
                f"   Para desbloquear:\n"
                f"   1. Acesse https://guimitestai.com/upgrade\n"
                f"   2. Obtenha sua API key (sk-guimi-...)\n"
                f"   3. Configure: export GUIMI_API_KEY='sk-guimi-sua-chave'\n\n"
                f"   Dúvidas: contato@guimitestai.com\n"
            )

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "guimitestai-python/0.1.0",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    # ─── Avaliação ────────────────────────────────────────────────────────────

    async def evaluate(
        self,
        input: str,
        output: str,
        expected: Optional[str] = None,
        criteria: str = "correctness",
        model: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Avalia uma resposta de LLM usando LLM-as-Judge.

        Args:
            input: Pergunta ou prompt enviado ao modelo.
            output: Resposta gerada pelo modelo a ser avaliada.
            expected: Resposta esperada (ground truth), se disponível.
            criteria: Critério de avaliação (correctness, helpfulness, safety, etc.).
            model: Identificador do modelo avaliado.
            trace_id: ID do trace associado para correlação.
            metadata: Metadados adicionais.

        Returns:
            EvaluationResult com score, passed e reasoning.
        """
        # Verificar se o critério é premium
        if criteria in _PREMIUM_CRITERIA:
            self._require_premium(f"evaluate(criteria='{criteria}')")

        payload = {
            "input": input,
            "output": output,
            "expected": expected,
            "criteria": criteria,
            "model": model,
            "traceId": trace_id,
            "metadata": metadata or {},
        }
        response = await self._http.post("/api/evaluations", json=payload)
        response.raise_for_status()
        return EvaluationResult(**response.json())

    async def batch_evaluate(
        self,
        items: List[Dict[str, Any]],
        criteria: str = "correctness",
    ) -> List[EvaluationResult]:
        """Avalia um lote de respostas em paralelo.

        Args:
            items: Lista de dicts com keys: input, output, expected (opcional).
            criteria: Critério de avaliação aplicado a todos os itens.

        Returns:
            Lista de EvaluationResult na mesma ordem dos itens.
        """
        import asyncio
        tasks = [
            self.evaluate(
                input=item["input"],
                output=item["output"],
                expected=item.get("expected"),
                criteria=criteria,
            )
            for item in items
        ]
        return await asyncio.gather(*tasks)

    # ─── Observabilidade ──────────────────────────────────────────────────────

    async def trace(
        self,
        name: str,
        input: Optional[str] = None,
        output: Optional[str] = None,
        model: Optional[str] = None,
        latency_ms: Optional[int] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        error: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TraceEvent:
        """Registra um evento de trace para observabilidade.

        Args:
            name: Nome da operação (ex: "chat_completion", "rag_retrieval").
            input: Entrada da operação.
            output: Saída da operação.
            model: Modelo utilizado.
            latency_ms: Latência em milissegundos.
            tokens_input: Número de tokens de entrada.
            tokens_output: Número de tokens de saída.
            error: Mensagem de erro, se houver.
            tags: Tags para categorização.
            metadata: Metadados adicionais.

        Returns:
            TraceEvent registrado com ID único.
        """
        payload = {
            "name": name,
            "input": input,
            "output": output,
            "model": model,
            "latencyMs": latency_ms,
            "tokensInput": tokens_input,
            "tokensOutput": tokens_output,
            "error": error,
            "tags": tags or [],
            "metadata": metadata or {},
        }
        response = await self._http.post("/api/traces", json=payload)
        response.raise_for_status()
        return TraceEvent(**response.json())

    async def get_traces(
        self,
        limit: int = 50,
        model: Optional[str] = None,
        has_error: Optional[bool] = None,
    ) -> List[TraceEvent]:
        """Busca traces registrados com filtros opcionais."""
        params: Dict[str, Any] = {"limit": limit}
        if model:
            params["model"] = model
        if has_error is not None:
            params["hasError"] = has_error
        response = await self._http.get("/api/traces", params=params)
        response.raise_for_status()
        return [TraceEvent(**t) for t in response.json().get("traces", [])]

    # ─── Segurança / Red Teaming ──────────────────────────────────────────────

    async def red_team(
        self,
        target_model: str,
        attack_types: Optional[List[str]] = None,
        num_attacks: int = 10,
    ) -> List[SecurityAlert]:
        """Executa red teaming automatizado contra um modelo.

        Args:
            target_model: Identificador do modelo alvo.
            attack_types: Tipos de ataque (prompt_injection, jailbreak, pii_leak, etc.).
                          Se None, usa todos os tipos disponíveis.
            num_attacks: Número de ataques por tipo.

        Returns:
            Lista de SecurityAlert com vulnerabilidades encontradas.
        """
        # Verificar perfil de red teaming
        profile = (attack_types[0] if attack_types and len(attack_types) == 1 else "quick")
        if profile in _PREMIUM_RT_PROFILES:
            self._require_premium(f"red_team(profile='{profile}')")

        payload = {
            "targetModel": target_model,
            "attackTypes": attack_types,
            "numAttacks": num_attacks,
            "profile": profile,
        }
        response = await self._http.post("/api/security/red-team", json=payload)
        response.raise_for_status()
        return [SecurityAlert(**a) for a in response.json().get("alerts", [])]

    # ─── Compliance ───────────────────────────────────────────────────────────

    async def compliance_report(
        self,
        organization: str,
        frameworks: Optional[List[ComplianceFramework]] = None,
        period_days: int = 30,
    ) -> ComplianceReport:
        # Compliance é sempre premium — toda a lógica está no servidor
        self._require_premium("compliance_report()")
        """Gera relatório de conformidade regulatória.

        Args:
            organization: Nome da organização.
            frameworks: Frameworks a analisar. Se None, analisa todos.
            period_days: Período de análise em dias.

        Returns:
            ComplianceReport com score, gaps e recomendações.
        """
        payload = {
            "organization": organization,
            "frameworks": [f.value for f in (frameworks or list(ComplianceFramework))],
            "periodDays": period_days,
        }
        response = await self._http.post("/api/compliance/report-json", json=payload)
        response.raise_for_status()
        return ComplianceReport(**response.json())

    # ─── Utilitários ──────────────────────────────────────────────────────────

    async def health(self) -> Dict[str, Any]:
        """Verifica o status da API Guimí Test AI."""
        response = await self._http.get("/api/health")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        await self._http.aclose()

    async def __aenter__(self) -> "GuimiClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
