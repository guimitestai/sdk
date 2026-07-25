"""Integração com LangFuse para observabilidade de LLMs."""

from __future__ import annotations

from typing import Any, Dict, Optional


class LangFuseIntegration:
    """Integração com LangFuse para observabilidade unificada.

    Sincroniza traces e avaliações do Guimí Test AI com o LangFuse,
    permitindo visualização centralizada de métricas de LLM.

    Exemplo:
        >>> from guimitestai.integrations import LangFuseIntegration
        >>> lf = LangFuseIntegration(
        ...     public_key="pk-lf-...",
        ...     secret_key="sk-lf-...",
        ... )
        >>> # Usar como callback em chains LangChain
        >>> callbacks = [lf.callback_handler]
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: str = "https://cloud.langfuse.com",
    ) -> None:
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host
        self._client: Any = None

    def _get_client(self) -> Any:
        """Inicializa o cliente LangFuse sob demanda."""
        if self._client is None:
            try:
                from langfuse import Langfuse  # type: ignore
                self._client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
            except ImportError:
                raise ImportError(
                    "LangFuse não instalado. Execute: pip install guimitestai[langfuse]"
                )
        return self._client

    @property
    def callback_handler(self) -> Any:
        """Retorna o handler de callback para uso com LangChain."""
        try:
            from langfuse.callback import CallbackHandler  # type: ignore
            return CallbackHandler(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
            )
        except ImportError:
            raise ImportError(
                "LangFuse não instalado. Execute: pip install guimitestai[langfuse]"
            )

    def trace(
        self,
        name: str,
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Cria um trace no LangFuse."""
        client = self._get_client()
        return client.trace(
            name=name,
            input=input,
            output=output,
            metadata=metadata or {},
        )

    def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ) -> None:
        """Registra um score de avaliação no LangFuse."""
        client = self._get_client()
        client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )

    def flush(self) -> None:
        """Força o envio de todos os eventos pendentes."""
        if self._client:
            self._client.flush()
