"""Integrações com plataformas externas de observabilidade e segurança."""

from guimitestai.integrations.langfuse import LangFuseIntegration
from guimitestai.integrations.langsmith import LangSmithIntegration

try:
    from guimitestai.integrations.garak import (
        GarakIntegration,
        GarakScanResult,
        GarakProbeResult,
        GARAK_PROFILES,
        GARAK_PROBE_CATEGORIES,
    )
except ImportError:
    pass  # Garak é opcional: pip install guimitestai[garak]

__all__ = [
    # Observabilidade (gratuito)
    "LangFuseIntegration",
    "LangSmithIntegration",
    # Red teaming NVIDIA (gratuito: perfil quick; premium: demais perfis)
    "GarakIntegration",
    "GarakScanResult",
    "GarakProbeResult",
    "GARAK_PROFILES",
    "GARAK_PROBE_CATEGORIES",
]
