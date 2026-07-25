"""
🐺 Guimí Test AI
================
Plataforma unificada de testes, observabilidade e compliance para sistemas de IA.

Inspirado no lobo-guará (Chrysocyon brachyurus) — espécie-chave do Cerrado brasileiro
que regula e protege o ecossistema. Assim como o guará, esta biblioteca monitora,
detecta anomalias e protege o ecossistema de IA da sua organização.

Módulos GRATUITOS (open source):
  - GuimiClient: cliente para a plataforma guimitestai.com
  - Tracer: observabilidade básica com context manager
  - Evaluator: avaliação LLM com critérios correctness e helpfulness
  - RedTeamer: red teaming básico (3 ataques: prompt_injection, jailbreak, hallucination)
  - GarakIntegration: perfil 'quick' gratuito (3 probes: dan, encoding, promptinject)
  - LangFuseIntegration + LangSmithIntegration: conectores de observabilidade

Módulos PREMIUM (requerem API key — guimitestai.com/upgrade):
  - ComplianceChecker: LGPD, EU AI Act, NIST AI RMF, OWASP LLM Top 10, ISO 42001
  - RedTeamer avançado: OWASP LLM Top 10 completo (15+ ataques)
  - GarakIntegration perfis avançados: security, owasp_llm_top10, lgpd, eu_ai_act, full
  - Evaluator critérios avançados: faithfulness, lgpd_compliance, safety_advanced
  - Relatórios PDF de compliance

Uso rápido:
    >>> from guimitestai import GuimiClient
    >>> client = GuimiClient(api_url="http://localhost:3000")
    >>> result = await client.evaluate("Qual é a capital do Brasil?", "Brasília")
    >>> print(result.score)

Para funcionalidades premium:
    >>> import guimitestai
    >>> guimitestai.configure(api_key="sk-guimi-sua-chave")

Privacidade e telemetria (LGPD/GDPR compliant — opt-in):
    >>> guimitestai.telemetry.enable(user_confirmed=True)   # habilitar
    >>> guimitestai.telemetry.disable()                     # desabilitar
    >>> guimitestai.telemetry.export_my_data()              # seus dados
    >>> guimitestai.telemetry.delete_my_data()              # apagar tudo

Documentação: https://docs.guimitestai.com
Repositório:  https://github.com/EmersonGuilherme/guimitestai
Privacidade:  https://guimitestai.com/privacy
"""

from __future__ import annotations

import os
from typing import Optional

from guimitestai.core.client import GuimiClient
from guimitestai.core.config import GuimiConfig
from guimitestai.core.models import (
    EvaluationResult,
    TraceEvent,
    ComplianceReport,
    SecurityAlert,
)
from guimitestai.core.premium import (
    PremiumFeatureError,
    is_premium_enabled,
    require_premium,
)
from guimitestai.evaluation.evaluator import Evaluator
from guimitestai.observability.tracer import Tracer
from guimitestai.security.red_teamer import RedTeamer
from guimitestai import telemetry

# ComplianceChecker é premium — importar mas bloquear uso sem API key
from guimitestai.compliance.checker import ComplianceChecker

__version__ = "0.1.0"
__author__ = "Emerson Guilherme"
__license__ = "MIT"
__url__ = "https://guimitestai.com"
__docs__ = "https://docs.guimitestai.com"

__all__ = [
    # Cliente principal
    "GuimiClient",
    "GuimiConfig",
    "configure",
    # Modelos de dados
    "EvaluationResult",
    "TraceEvent",
    "ComplianceReport",
    "SecurityAlert",
    # Módulos gratuitos
    "Evaluator",
    "Tracer",
    "RedTeamer",
    # Módulo premium (requer API key)
    "ComplianceChecker",
    # Premium gate
    "PremiumFeatureError",
    "is_premium_enabled",
    # Telemetria (opt-in, LGPD/GDPR compliant)
    "telemetry",
    # Metadados
    "__version__",
]

# ─── Configuração global ──────────────────────────────────────────────────────

_global_config: Optional[GuimiConfig] = None


def configure(
    api_key: Optional[str] = None,
    api_url: str = "https://api.guimitestai.com",
    telemetry_enabled: Optional[bool] = None,
) -> GuimiConfig:
    """Configura o SDK globalmente.

    Args:
        api_key: API key da plataforma Guimí (sk-guimi-...).
                 Desbloqueia funcionalidades premium.
                 Também pode ser definida via env: GUIMI_API_KEY
        api_url: URL da API. Padrão: https://api.guimitestai.com
        telemetry_enabled: Habilitar/desabilitar telemetria.
                           None = respeitar configuração existente (padrão: desabilitada).
                           True = habilita (requer que o usuário tenha visto a política).
                           False = desabilita explicitamente.

    Returns:
        GuimiConfig configurado.

    Exemplo:
        >>> import guimitestai
        >>> guimitestai.configure(api_key="sk-guimi-sua-chave")
        >>> # Agora funcionalidades premium estão disponíveis
    """
    global _global_config

    resolved_key = api_key or os.environ.get("GUIMI_API_KEY")
    if resolved_key:
        os.environ["GUIMI_API_KEY"] = resolved_key

    _global_config = GuimiConfig(
        api_key=resolved_key,
        api_url=api_url,
    )

    if telemetry_enabled is True:
        # Telemetria só pode ser habilitada com consentimento explícito
        telemetry.TelemetryConsent.enable(user_confirmed=True)
    elif telemetry_enabled is False:
        telemetry.disable()

    return _global_config


def get_config() -> Optional[GuimiConfig]:
    """Retorna a configuração global atual."""
    return _global_config
