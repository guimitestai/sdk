"""
API Discovery — Descobre endpoints automaticamente a partir de OpenAPI/Swagger
ou por crawling de APIs REST.

Suporta:
- OpenAPI 3.x (JSON/YAML)
- Swagger 2.0 (JSON/YAML)
- Crawling automático de endpoints REST
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class APIEndpoint:
    """Representa um endpoint descoberto na API."""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    security: List[Dict[str, Any]] = field(default_factory=list)
    requires_auth: bool = False

    def __post_init__(self):
        self.method = self.method.upper()
        self.requires_auth = bool(self.security)

    @property
    def full_description(self) -> str:
        return self.description or self.summary or f"{self.method} {self.path}"

    @property
    def has_body(self) -> bool:
        return self.method in ("POST", "PUT", "PATCH") or self.request_body is not None


@dataclass
class APISpec:
    """Especificação completa de uma API descoberta."""
    base_url: str
    title: str = "API"
    version: str = "1.0.0"
    description: str = ""
    endpoints: List[APIEndpoint] = field(default_factory=list)
    auth_schemes: List[str] = field(default_factory=list)
    source: str = "openapi"  # openapi | swagger | crawl | manual

    @property
    def endpoint_count(self) -> int:
        return len(self.endpoints)

    @property
    def methods_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for ep in self.endpoints:
            summary[ep.method] = summary.get(ep.method, 0) + 1
        return summary

    def get_endpoints_by_tag(self, tag: str) -> List[APIEndpoint]:
        return [ep for ep in self.endpoints if tag in ep.tags]

    def get_endpoints_by_method(self, method: str) -> List[APIEndpoint]:
        return [ep for ep in self.endpoints if ep.method == method.upper()]


class APIDiscovery:
    """
    Descobre e mapeia APIs automaticamente.

    Suporta OpenAPI 3.x, Swagger 2.0 e crawling básico de REST APIs.
    Não usa gRPC — apenas HTTP/REST conforme requisito do projeto.

    Exemplo:
        discovery = APIDiscovery(base_url="http://localhost:8000")
        spec = await discovery.discover()
        print(f"Encontrados {spec.endpoint_count} endpoints")
    """

    COMMON_SPEC_PATHS = [
        "/openapi.json",
        "/openapi.yaml",
        "/swagger.json",
        "/swagger.yaml",
        "/api/openapi.json",
        "/api/swagger.json",
        "/docs/openapi.json",
        "/v1/openapi.json",
        "/v2/openapi.json",
        "/api-docs",
        "/api-docs.json",
        "/.well-known/openapi.json",
    ]

    def __init__(
        self,
        base_url: str,
        spec_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Args:
            base_url: URL base da API (ex: http://localhost:8000).
            spec_url: URL direta do spec OpenAPI/Swagger (opcional).
            auth_token: Token Bearer para autenticação (opcional).
            timeout: Timeout em segundos para requisições HTTP.
        """
        self.base_url = base_url.rstrip("/")
        self.spec_url = spec_url
        self.auth_token = auth_token
        self.timeout = timeout
        self._headers: Dict[str, str] = {"Accept": "application/json"}
        if auth_token:
            self._headers["Authorization"] = f"Bearer {auth_token}"

    async def discover(self) -> APISpec:
        """
        Descobre a API automaticamente.

        Tenta em ordem:
        1. URL de spec fornecida explicitamente
        2. Caminhos comuns de OpenAPI/Swagger
        3. Crawling básico de endpoints REST

        Returns:
            APISpec com todos os endpoints descobertos.
        """
        if not HAS_HTTPX:
            raise ImportError(
                "httpx é necessário para API Discovery. "
                "Instale com: pip install guimitestai[autonomous]"
            )

        # 1. Tentar spec_url explícita
        if self.spec_url:
            spec = await self._load_spec_from_url(self.spec_url)
            if spec:
                return spec

        # 2. Tentar caminhos comuns
        for path in self.COMMON_SPEC_PATHS:
            url = urljoin(self.base_url + "/", path.lstrip("/"))
            spec = await self._load_spec_from_url(url)
            if spec:
                return spec

        # 3. Fallback: crawling básico
        return await self._crawl_basic(self.base_url)

    async def _load_spec_from_url(self, url: str) -> Optional[APISpec]:
        """Tenta carregar e parsear um spec OpenAPI/Swagger de uma URL."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=self._headers)
                if resp.status_code != 200:
                    return None

                content_type = resp.headers.get("content-type", "")
                text = resp.text

                # Parsear JSON ou YAML
                if "yaml" in content_type or url.endswith(".yaml") or url.endswith(".yml"):
                    if not HAS_YAML:
                        return None
                    data = yaml.safe_load(text)
                else:
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        if HAS_YAML:
                            data = yaml.safe_load(text)
                        else:
                            return None

                if not isinstance(data, dict):
                    return None

                # Detectar versão
                if "openapi" in data and data["openapi"].startswith("3"):
                    return self._parse_openapi3(data)
                elif "swagger" in data and data["swagger"].startswith("2"):
                    return self._parse_swagger2(data)

                return None
        except Exception:
            return None

    def _parse_openapi3(self, data: Dict[str, Any]) -> APISpec:
        """Parseia um spec OpenAPI 3.x."""
        info = data.get("info", {})
        servers = data.get("servers", [])
        base_url = servers[0].get("url", self.base_url) if servers else self.base_url

        # Resolver URL relativa
        if base_url.startswith("/"):
            parsed = urlparse(self.base_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}{base_url}"

        # Extrair esquemas de autenticação
        security_schemes = list(data.get("components", {}).get("securitySchemes", {}).keys())

        endpoints: List[APIEndpoint] = []
        paths = data.get("paths", {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "patch", "delete", "head", "options"):
                op = path_item.get(method)
                if not op or not isinstance(op, dict):
                    continue

                # Parâmetros (path + query + header)
                params = list(path_item.get("parameters", []))
                params.extend(op.get("parameters", []))

                # Request body
                request_body = op.get("requestBody")

                # Segurança
                security = op.get("security", data.get("security", []))

                endpoints.append(APIEndpoint(
                    path=path,
                    method=method,
                    summary=op.get("summary", ""),
                    description=op.get("description", ""),
                    parameters=params,
                    request_body=request_body,
                    responses=op.get("responses", {}),
                    tags=op.get("tags", []),
                    security=security,
                ))

        return APISpec(
            base_url=base_url,
            title=info.get("title", "API"),
            version=info.get("version", "1.0.0"),
            description=info.get("description", ""),
            endpoints=endpoints,
            auth_schemes=security_schemes,
            source="openapi",
        )

    def _parse_swagger2(self, data: Dict[str, Any]) -> APISpec:
        """Parseia um spec Swagger 2.0."""
        info = data.get("info", {})
        host = data.get("host", urlparse(self.base_url).netloc)
        schemes = data.get("schemes", ["https"])
        base_path = data.get("basePath", "/")
        base_url = f"{schemes[0]}://{host}{base_path}".rstrip("/")

        security_defs = list(data.get("securityDefinitions", {}).keys())

        endpoints: List[APIEndpoint] = []
        paths = data.get("paths", {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "patch", "delete"):
                op = path_item.get(method)
                if not op or not isinstance(op, dict):
                    continue

                params = list(path_item.get("parameters", []))
                params.extend(op.get("parameters", []))

                # Converter body param do Swagger 2 para request_body
                body_params = [p for p in params if p.get("in") == "body"]
                request_body = body_params[0] if body_params else None
                params = [p for p in params if p.get("in") != "body"]

                security = op.get("security", data.get("security", []))

                endpoints.append(APIEndpoint(
                    path=path,
                    method=method,
                    summary=op.get("summary", ""),
                    description=op.get("description", ""),
                    parameters=params,
                    request_body=request_body,
                    responses=op.get("responses", {}),
                    tags=op.get("tags", []),
                    security=security,
                ))

        return APISpec(
            base_url=base_url,
            title=info.get("title", "API"),
            version=info.get("version", "1.0.0"),
            description=info.get("description", ""),
            endpoints=endpoints,
            auth_schemes=security_defs,
            source="swagger",
        )

    async def _crawl_basic(self, base_url: str) -> APISpec:
        """Crawling básico: tenta endpoints REST comuns."""
        common_paths = [
            "/health", "/healthz", "/ping", "/status",
            "/api/v1", "/api/v2", "/api",
            "/users", "/products", "/orders", "/items",
            "/auth/login", "/auth/token",
        ]

        endpoints: List[APIEndpoint] = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for path in common_paths:
                url = f"{base_url}{path}"
                try:
                    resp = await client.get(url, headers=self._headers)
                    if resp.status_code < 500:
                        endpoints.append(APIEndpoint(
                            path=path,
                            method="GET",
                            summary=f"Descoberto por crawling — status {resp.status_code}",
                        ))
                except Exception:
                    pass

        return APISpec(
            base_url=base_url,
            title="API (descoberta por crawling)",
            endpoints=endpoints,
            source="crawl",
        )

    @classmethod
    def from_file(cls, spec_file: str, base_url: str = "http://localhost") -> "APIDiscovery":
        """Cria um APIDiscovery a partir de um arquivo local de spec."""
        instance = cls(base_url=base_url)
        instance._local_spec_file = spec_file
        return instance

    async def discover_from_file(self, spec_file: str) -> APISpec:
        """Carrega spec de um arquivo local JSON ou YAML."""
        from pathlib import Path
        content = Path(spec_file).read_text()

        if spec_file.endswith((".yaml", ".yml")):
            if not HAS_YAML:
                raise ImportError("PyYAML necessário: pip install pyyaml")
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        if "openapi" in data:
            return self._parse_openapi3(data)
        elif "swagger" in data:
            return self._parse_swagger2(data)
        else:
            raise ValueError("Formato de spec não reconhecido (esperado OpenAPI 3.x ou Swagger 2.0)")
