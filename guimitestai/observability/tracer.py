"""Tracer de observabilidade do Guimí Test AI."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from guimitestai.core.models import TraceEvent


class Tracer:
    """Tracer de observabilidade para operações de LLM.

    Registra traces localmente e pode sincronizar com LangFuse/LangSmith.

    Exemplo:
        >>> from guimitestai.observability import Tracer
        >>> tracer = Tracer()
        >>>
        >>> async with tracer.span("chat_completion") as span:
        ...     response = await llm.invoke("Olá!")
        ...     span.set_output(response.content)
    """

    def __init__(self) -> None:
        self._traces: List[TraceEvent] = []

    @asynccontextmanager
    async def span(
        self,
        name: str,
        model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator["SpanContext", None]:
        """Context manager para rastrear uma operação."""
        ctx = SpanContext(name=name, model=model, tags=tags or [], metadata=metadata or {})
        start = time.monotonic()
        try:
            yield ctx
            ctx._latency_ms = int((time.monotonic() - start) * 1000)
        except Exception as e:
            ctx._error = str(e)
            ctx._latency_ms = int((time.monotonic() - start) * 1000)
            raise
        finally:
            event = TraceEvent(
                id=ctx._id,
                name=name,
                input=ctx._input,
                output=ctx._output,
                model=model,
                latency_ms=ctx._latency_ms,
                tokens_input=ctx._tokens_input,
                tokens_output=ctx._tokens_output,
                error=ctx._error,
                tags=ctx._tags,
                created_at=datetime.utcnow(),
                metadata=ctx._metadata,
            )
            self._traces.append(event)

    def get_traces(self) -> List[TraceEvent]:
        """Retorna todos os traces registrados."""
        return list(self._traces)

    def clear(self) -> None:
        """Limpa todos os traces registrados."""
        self._traces.clear()

    def summary(self) -> Dict[str, Any]:
        """Retorna um resumo estatístico dos traces."""
        if not self._traces:
            return {"total": 0}
        latencies = [t.latency_ms for t in self._traces if t.latency_ms is not None]
        errors = [t for t in self._traces if t.error]
        return {
            "total": len(self._traces),
            "errors": len(errors),
            "error_rate": len(errors) / len(self._traces),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
        }


class SpanContext:
    """Contexto de um span de trace."""

    def __init__(
        self,
        name: str,
        model: Optional[str],
        tags: List[str],
        metadata: Dict[str, Any],
    ) -> None:
        self._id = str(uuid.uuid4())
        self._name = name
        self._model = model
        self._tags = tags
        self._metadata = metadata
        self._input: Optional[str] = None
        self._output: Optional[str] = None
        self._latency_ms: Optional[int] = None
        self._tokens_input: Optional[int] = None
        self._tokens_output: Optional[int] = None
        self._error: Optional[str] = None

    def set_input(self, value: str) -> None:
        self._input = value

    def set_output(self, value: str) -> None:
        self._output = value

    def set_tokens(self, input_tokens: int, output_tokens: int) -> None:
        self._tokens_input = input_tokens
        self._tokens_output = output_tokens

    @property
    def trace_id(self) -> str:
        return self._id
