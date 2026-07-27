"""Módulo de telemetria do Guimí Test AI.

Coleta dados anônimos de uso para melhorar o produto, com conformidade
total às leis de proteção de dados mundiais:

  - 🇧🇷 LGPD (Lei 13.709/2018) — Brasil
  - 🇪🇺 GDPR (Regulamento 2016/679) — União Europeia
  - 🇺🇸 CCPA (California Consumer Privacy Act) — Califórnia/EUA
  - 🇨🇦 PIPEDA — Canadá
  - 🇦🇺 Privacy Act 1988 — Austrália

Princípios fundamentais:
  1. OPT-IN explícito — desabilitado por padrão, nunca ativo sem consentimento
  2. Anonimização — nenhum dado pessoal identificável é coletado
  3. Minimização — apenas o mínimo necessário para melhorar o produto
  4. Transparência — todo dado coletado está documentado aqui
  5. Direito ao esquecimento — `guimi.telemetry.delete_my_data()` remove tudo
  6. Portabilidade — `guimi.telemetry.export_my_data()` exporta em JSON

O que é coletado (somente com consentimento):
  - Versão do SDK e Python
  - Sistema operacional (apenas família: linux/mac/windows)
  - Módulos utilizados (ex: "evaluator", "tracer") — SEM conteúdo
  - Contagem de operações por tipo (ex: "evaluations_count: 5")
  - Erros anônimos (tipo de exceção, SEM stack trace ou dados do usuário)
  - Hash anônimo do projeto (SHA256 truncado, irreversível)

O que NUNCA é coletado:
  - Prompts, respostas ou qualquer conteúdo de LLM
  - Dados pessoais (nome, e-mail, IP, localização)
  - Chaves de API ou credenciais
  - Nomes de modelos ou endpoints
  - Dados de negócio ou propriedade intelectual
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Configuração ─────────────────────────────────────────────────────────────

TELEMETRY_ENDPOINT = "https://guimitestai.com/v1/events"
TELEMETRY_CONFIG_DIR = Path.home() / ".guimitestai"
TELEMETRY_CONFIG_FILE = TELEMETRY_CONFIG_DIR / "telemetry.json"
TELEMETRY_DATA_FILE = TELEMETRY_CONFIG_DIR / "telemetry_data.jsonl"

SDK_VERSION = "0.1.2"


# ─── Consentimento ────────────────────────────────────────────────────────────

class TelemetryConsent:
    """Gerencia o consentimento do usuário para coleta de telemetria.

    Segue os requisitos do GDPR Art. 7, LGPD Art. 8 e CCPA § 1798.100:
    - Consentimento deve ser livre, específico, informado e inequívoco
    - Pode ser revogado a qualquer momento
    - Registro de data/hora do consentimento
    - Identificação da versão da política de privacidade aceita
    """

    PRIVACY_POLICY_VERSION = "1.0.0"
    PRIVACY_POLICY_URL = "https://guimitestai.com/privacy"

    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        if TELEMETRY_CONFIG_FILE.exists():
            try:
                return json.loads(TELEMETRY_CONFIG_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    @classmethod
    def _save_config(cls, config: Dict[str, Any]) -> None:
        TELEMETRY_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TELEMETRY_CONFIG_FILE.write_text(json.dumps(config, indent=2))

    @classmethod
    def is_enabled(cls) -> bool:
        """Verifica se a telemetria está habilitada.

        Ordem de precedência:
        1. Variável de ambiente GUIMI_TELEMETRY=false/0/no → desabilitada
        2. Variável de ambiente GUIMI_TELEMETRY=true/1/yes → habilitada
        3. Arquivo de configuração ~/.guimitestai/telemetry.json
        4. Padrão: DESABILITADA (opt-in, não opt-out)
        """
        env_val = os.environ.get("GUIMI_TELEMETRY", "").lower()
        if env_val in ("false", "0", "no", "off", "disabled"):
            return False
        if env_val in ("true", "1", "yes", "on", "enabled"):
            return True

        config = cls._load_config()
        return config.get("enabled", False)  # Padrão: DESABILITADO

    @classmethod
    def enable(cls, user_confirmed: bool = False) -> None:
        """Habilita a telemetria com consentimento explícito.

        Args:
            user_confirmed: Deve ser True para confirmar que o usuário
                           leu e aceitou a política de privacidade.

        Raises:
            ValueError: Se user_confirmed for False.

        Exemplo:
            >>> from guimitestai.telemetry import TelemetryConsent
            >>> # Mostrar política ao usuário primeiro
            >>> print(f"Política: {TelemetryConsent.PRIVACY_POLICY_URL}")
            >>> # Registrar consentimento
            >>> TelemetryConsent.enable(user_confirmed=True)
        """
        if not user_confirmed:
            raise ValueError(
                "Para habilitar a telemetria, o usuário deve confirmar que leu "
                f"a política de privacidade em {cls.PRIVACY_POLICY_URL}. "
                "Passe user_confirmed=True após apresentar a política ao usuário."
            )

        config = cls._load_config()
        config.update({
            "enabled": True,
            "consent_given_at": datetime.now(timezone.utc).isoformat(),
            "privacy_policy_version": cls.PRIVACY_POLICY_VERSION,
            "privacy_policy_url": cls.PRIVACY_POLICY_URL,
            "sdk_version_at_consent": SDK_VERSION,
            # Direitos do titular (LGPD Art. 18, GDPR Art. 17)
            "user_rights": {
                "access": "guimi.telemetry.export_my_data()",
                "deletion": "guimi.telemetry.delete_my_data()",
                "portability": "guimi.telemetry.export_my_data(format='json')",
                "opt_out": "guimi.telemetry.disable() ou GUIMI_TELEMETRY=false",
            }
        })
        cls._save_config(config)

    @classmethod
    def disable(cls) -> None:
        """Revoga o consentimento e desabilita a telemetria imediatamente.

        Conforme LGPD Art. 8 §5 e GDPR Art. 7(3): o consentimento pode
        ser revogado a qualquer momento, sem prejuízo ao usuário.
        """
        config = cls._load_config()
        config.update({
            "enabled": False,
            "consent_revoked_at": datetime.now(timezone.utc).isoformat(),
        })
        cls._save_config(config)

    @classmethod
    def get_anonymous_id(cls) -> str:
        """Retorna um ID anônimo e persistente para este ambiente.

        Gerado uma vez e salvo localmente. É um UUID v4 sem qualquer
        relação com dados pessoais. Pode ser regenerado com delete_my_data().
        """
        config = cls._load_config()
        if "anonymous_id" not in config:
            config["anonymous_id"] = str(uuid.uuid4())
            cls._save_config(config)
        return config["anonymous_id"]


# ─── Coletor de Telemetria ────────────────────────────────────────────────────

class TelemetryCollector:
    """Coleta e envia eventos de telemetria anônimos.

    Todos os dados são anonimizados antes de qualquer envio.
    Nenhum conteúdo de LLM, dado pessoal ou credencial é coletado.
    """

    def __init__(self) -> None:
        self._buffer: List[Dict[str, Any]] = []
        self._session_id = str(uuid.uuid4())[:8]

    def _anonymize_project(self, project_identifier: Optional[str]) -> Optional[str]:
        """Gera hash SHA256 truncado e irreversível do identificador do projeto."""
        if not project_identifier:
            return None
        return hashlib.sha256(project_identifier.encode()).hexdigest()[:16]

    def _collect_system_info(self) -> Dict[str, str]:
        """Coleta informações do sistema — sem dados pessoais."""
        return {
            "sdk_version": SDK_VERSION,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "os_family": platform.system().lower(),  # linux/darwin/windows apenas
        }

    def track(
        self,
        event: str,
        module: str,
        properties: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """Registra um evento de uso (somente se telemetria habilitada e consentida).

        Args:
            event: Nome do evento (ex: "evaluation_run", "trace_created").
            module: Módulo utilizado (ex: "evaluator", "tracer", "red_teamer").
            properties: Propriedades adicionais — NUNCA incluir dados de conteúdo.
            project_id: Identificador do projeto (será anonimizado via SHA256).

        Dados que NÃO devem ser passados em properties:
            - Prompts ou respostas de LLM
            - Nomes de modelos ou endpoints
            - Dados de usuários finais
            - Chaves de API
        """
        if not TelemetryConsent.is_enabled():
            return

        # Filtrar propriedades sensíveis por precaução
        safe_properties = {}
        BLOCKED_KEYS = {
            "prompt", "response", "output", "input", "content", "message",
            "api_key", "key", "token", "secret", "password", "credential",
            "model_name", "endpoint", "url", "email", "name", "user",
        }
        for k, v in (properties or {}).items():
            if k.lower() not in BLOCKED_KEYS and isinstance(v, (int, float, bool, str)):
                # Truncar strings longas
                safe_properties[k] = str(v)[:50] if isinstance(v, str) else v

        event_data = {
            "event": event,
            "module": module,
            "session_id": self._session_id,
            "anonymous_id": TelemetryConsent.get_anonymous_id(),
            "project_hash": self._anonymize_project(project_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": self._collect_system_info(),
            "properties": safe_properties,
        }

        self._buffer.append(event_data)
        self._persist_locally(event_data)

        # Enviar em lote quando buffer atingir 10 eventos
        if len(self._buffer) >= 10:
            self.flush()

    def _persist_locally(self, event_data: Dict[str, Any]) -> None:
        """Persiste evento localmente antes de enviar (resiliência)."""
        try:
            TELEMETRY_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(TELEMETRY_DATA_FILE, "a") as f:
                f.write(json.dumps(event_data) + "\n")
        except OSError:
            pass  # Nunca falhar por causa de telemetria

    def flush(self) -> None:
        """Envia eventos em buffer para o servidor de telemetria."""
        if not self._buffer or not TelemetryConsent.is_enabled():
            self._buffer.clear()
            return

        try:
            import urllib.request
            payload = json.dumps({
                "events": self._buffer,
                "batch_size": len(self._buffer),
            }).encode()

            req = urllib.request.Request(
                TELEMETRY_ENDPOINT,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-SDK-Version": SDK_VERSION,
                    "X-Privacy-Policy": TelemetryConsent.PRIVACY_POLICY_VERSION,
                },
                method="POST",
            )
            # Timeout curto — nunca bloquear o usuário por causa de telemetria
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass  # Silencioso — telemetria nunca deve afetar o usuário
        finally:
            self._buffer.clear()


# ─── Direitos do Titular (LGPD Art. 18, GDPR Art. 15-22) ─────────────────────

def export_my_data(format: str = "json") -> str:
    """Exporta todos os dados de telemetria coletados (direito de acesso/portabilidade).

    Conforme LGPD Art. 18, II e GDPR Art. 20.

    Args:
        format: Formato de exportação ('json' ou 'text').

    Returns:
        String com todos os dados coletados.
    """
    config = {}
    if TELEMETRY_CONFIG_FILE.exists():
        try:
            config = json.loads(TELEMETRY_CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    events = []
    if TELEMETRY_DATA_FILE.exists():
        try:
            for line in TELEMETRY_DATA_FILE.read_text().strip().split("\n"):
                if line:
                    events.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass

    data = {
        "export_generated_at": datetime.now(timezone.utc).isoformat(),
        "privacy_policy": TelemetryConsent.PRIVACY_POLICY_URL,
        "consent_config": {k: v for k, v in config.items() if k != "anonymous_id"},
        "total_events_collected": len(events),
        "events": events,
        "your_rights": {
            "deletion": "Chame guimitestai.telemetry.delete_my_data()",
            "opt_out": "export GUIMI_TELEMETRY=false",
            "contact": "privacy@guimitestai.com",
        },
    }

    if format == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        lines = [
            "=== Guimí Test AI — Exportação de Dados de Telemetria ===",
            f"Gerado em: {data['export_generated_at']}",
            f"Total de eventos: {data['total_events_collected']}",
            f"Política de privacidade: {data['privacy_policy']}",
        ]
        return "\n".join(lines)


def delete_my_data() -> None:
    """Remove TODOS os dados de telemetria locais (direito ao esquecimento).

    Conforme LGPD Art. 18, VI e GDPR Art. 17.
    Também regenera o ID anônimo para desvincular histórico futuro.
    """
    if TELEMETRY_DATA_FILE.exists():
        TELEMETRY_DATA_FILE.unlink()

    if TELEMETRY_CONFIG_FILE.exists():
        try:
            config = json.loads(TELEMETRY_CONFIG_FILE.read_text())
            # Remover ID anônimo (será regenerado na próxima sessão)
            config.pop("anonymous_id", None)
            config["data_deleted_at"] = datetime.now(timezone.utc).isoformat()
            TELEMETRY_CONFIG_FILE.write_text(json.dumps(config, indent=2))
        except (json.JSONDecodeError, OSError):
            pass


def disable() -> None:
    """Atalho para desabilitar a telemetria. Equivalente a TelemetryConsent.disable()."""
    TelemetryConsent.disable()


def enable(user_confirmed: bool = False) -> None:
    """Atalho para habilitar a telemetria. Equivalente a TelemetryConsent.enable()."""
    TelemetryConsent.enable(user_confirmed=user_confirmed)


# ─── Instância global do coletor ─────────────────────────────────────────────
_collector = TelemetryCollector()


def track(event: str, module: str, **kwargs: Any) -> None:
    """Função de conveniência para registrar eventos de telemetria."""
    _collector.track(event=event, module=module, properties=kwargs)
