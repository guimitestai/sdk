"""Gate de funcionalidades premium do Guimí Test AI.

Módulos open source (gratuitos):
  - Tracer básico (observabilidade)
  - Evaluator com critérios: correctness, helpfulness
  - RedTeamer com 3 ataques básicos
  - GarakIntegration com perfil 'quick' (3 probes)
  - LangFuse + LangSmith connectors

Módulos premium (requerem API key da plataforma guimitestai.com):
  - ComplianceChecker completo (LGPD, EU AI Act, NIST, ISO 42001)
  - RedTeamer avançado (OWASP LLM Top 10 completo, 15+ ataques)
  - GarakIntegration perfis: security, owasp_llm_top10, lgpd, eu_ai_act, full
  - Evaluator critérios avançados: faithfulness, lgpd_compliance, safety_advanced
  - Relatórios PDF de compliance
  - Histórico e comparação de relatórios
  - Telemetria avançada e dashboards
"""

from __future__ import annotations

import os
from typing import Optional

PREMIUM_UPGRADE_URL = "https://guimitestai.com/upgrade"
DOCS_URL = "https://docs.guimitestai.com"


class PremiumFeatureError(Exception):
    """Levantada quando uma funcionalidade premium é acessada sem API key válida.

    Exemplo de mensagem:
        GuimiPremiumError: 'owasp_llm_top10' é um perfil premium.
        Para usar perfis avançados do Garak, obtenha sua API key em:
        https://guimitestai.com/upgrade

        Perfis gratuitos disponíveis: quick
        Documentação: https://docs.guimitestai.com/garak
    """
    pass


def require_premium(
    feature_name: str,
    feature_description: str,
    free_alternative: Optional[str] = None,
    docs_path: str = "",
) -> None:
    """Verifica se a API key premium está configurada.

    Levanta PremiumFeatureError com mensagem clara de upgrade se não estiver.

    Args:
        feature_name: Nome da funcionalidade premium.
        feature_description: Descrição do que a funcionalidade faz.
        free_alternative: Alternativa gratuita disponível, se houver.
        docs_path: Caminho na documentação para mais detalhes.
    """
    api_key = (
        os.environ.get("GUIMI_API_KEY")
        or os.environ.get("GUIMITESTAI_API_KEY")
    )

    if not api_key or not api_key.startswith("sk-guimi-"):
        free_msg = f"\n        Alternativa gratuita: {free_alternative}" if free_alternative else ""
        docs_url = f"{DOCS_URL}/{docs_path}" if docs_path else DOCS_URL

        raise PremiumFeatureError(
            f"\n\n"
            f"  🔒 '{feature_name}' é uma funcionalidade premium do Guimí Test AI.\n\n"
            f"  {feature_description}\n"
            f"{free_msg}\n\n"
            f"  Para desbloquear, obtenha sua API key em:\n"
            f"  👉 {PREMIUM_UPGRADE_URL}\n\n"
            f"  Configure com:\n"
            f"  export GUIMI_API_KEY='sk-guimi-sua-chave-aqui'\n\n"
            f"  Documentação: {docs_url}\n"
        )


def is_premium_enabled() -> bool:
    """Retorna True se uma API key premium válida está configurada."""
    api_key = (
        os.environ.get("GUIMI_API_KEY")
        or os.environ.get("GUIMITESTAI_API_KEY")
    )
    return bool(api_key and api_key.startswith("sk-guimi-"))


# ─── Decorador para métodos premium ──────────────────────────────────────────

def premium_feature(
    feature_name: str,
    description: str,
    free_alternative: Optional[str] = None,
    docs_path: str = "",
):
    """Decorador que bloqueia acesso a funcionalidades premium sem API key.

    Uso:
        @premium_feature(
            feature_name="owasp_llm_top10",
            description="Scan completo OWASP LLM Top 10 com 9 categorias de ataque.",
            free_alternative="perfil 'quick' com 3 probes básicos",
            docs_path="garak/profiles",
        )
        async def scan_owasp(self, ...):
            ...
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            require_premium(feature_name, description, free_alternative, docs_path)
            return func(*args, **kwargs)

        async def async_wrapper(*args, **kwargs):
            require_premium(feature_name, description, free_alternative, docs_path)
            return await func(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
