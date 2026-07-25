"""Configuração do cliente Guimí Test AI."""

from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseModel, Field


class GuimiConfig(BaseModel):
    """Configuração do SDK Guimí Test AI.

    Exemplo:
        >>> config = GuimiConfig(api_url="http://localhost:3000", api_key="sk-...")
        >>> # Ou via variáveis de ambiente:
        >>> # GUIMI_API_URL=http://localhost:3000
        >>> # GUIMI_API_KEY=sk-...
    """

    api_url: str = Field(
        default_factory=lambda: os.getenv("GUIMI_API_URL", "http://localhost:3000"),
        description="URL base da API Guimí Test AI",
    )
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GUIMI_API_KEY"),
        description="Chave de API para autenticação",
    )
    timeout: int = Field(
        default=30,
        description="Timeout em segundos para requisições HTTP",
    )
    langfuse_public_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY"),
        description="Chave pública do LangFuse para observabilidade",
    )
    langfuse_secret_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY"),
        description="Chave secreta do LangFuse",
    )
    langfuse_host: str = Field(
        default_factory=lambda: os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        description="Host do LangFuse",
    )
    langsmith_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_API_KEY"),
        description="Chave de API do LangSmith",
    )
    langsmith_project: Optional[str] = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_PROJECT", "guimitestai"),
        description="Projeto do LangSmith",
    )

    class Config:
        env_prefix = "GUIMI_"
