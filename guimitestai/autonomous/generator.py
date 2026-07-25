"""
Test Generator — Gera casos de teste automaticamente usando LLM-as-Generator.

Para cada endpoint descoberto, gera:
- Casos positivos (happy path)
- Casos negativos (erros esperados)
- Edge cases (limites, valores extremos)
- Casos de segurança (injeção, overflow, PII)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from guimitestai.autonomous.discovery import APIEndpoint, APISpec


@dataclass
class TestCase:
    """Representa um caso de teste gerado automaticamente."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    endpoint: Optional[APIEndpoint] = None
    method: str = "GET"
    path: str = "/"
    path_params: Dict[str, Any] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    expected_status: int = 200
    expected_fields: List[str] = field(default_factory=list)
    expected_not_fields: List[str] = field(default_factory=list)
    category: str = "positive"  # positive | negative | edge | security
    priority: str = "medium"    # critical | high | medium | low
    tags: List[str] = field(default_factory=list)
    generated_by: str = "guimi"

    @property
    def full_path(self) -> str:
        """Retorna o path com path_params substituídos."""
        path = self.path
        for key, value in self.path_params.items():
            path = path.replace(f"{{{key}}}", str(value))
        return path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "method": self.method,
            "path": self.full_path,
            "query_params": self.query_params,
            "headers": self.headers,
            "body": self.body,
            "expected_status": self.expected_status,
            "expected_fields": self.expected_fields,
            "category": self.category,
            "priority": self.priority,
            "tags": self.tags,
        }


class TestGenerator:
    """
    Gera casos de teste automaticamente a partir de um APISpec.

    Modo gratuito: geração baseada em regras (sem LLM).
    Modo premium: geração via LLM-as-Generator com contexto semântico.

    Exemplo:
        spec = await APIDiscovery("http://localhost:8000").discover()
        generator = TestGenerator()
        test_cases = generator.generate(spec)
        print(f"Gerados {len(test_cases)} casos de teste")
    """

    # Valores de exemplo para tipos comuns
    EXAMPLE_VALUES: Dict[str, Any] = {
        "string": "test-string",
        "integer": 1,
        "number": 1.5,
        "boolean": True,
        "array": [],
        "object": {},
        "email": "test@example.com",
        "uuid": "00000000-0000-0000-0000-000000000001",
        "date": "2024-01-01",
        "datetime": "2024-01-01T00:00:00Z",
        "url": "https://example.com",
        "password": "Test@123",
        "phone": "+5511999999999",
        "cpf": "000.000.000-00",
        "cnpj": "00.000.000/0001-00",
    }

    # Payloads de segurança (edge cases)
    SECURITY_PAYLOADS: Dict[str, List[Any]] = {
        "sql_injection": ["' OR '1'='1", "'; DROP TABLE users; --", "1 UNION SELECT * FROM users"],
        "xss": ["<script>alert('xss')</script>", "javascript:alert(1)", "<img src=x onerror=alert(1)>"],
        "path_traversal": ["../../../etc/passwd", "..\\..\\windows\\system32"],
        "overflow": ["A" * 10000, -2147483648, 2147483647],
        "null_byte": ["\x00", "test\x00.txt"],
        "pii_leak": ["João Silva CPF 123.456.789-00", "email: joao@empresa.com.br"],
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_cases_per_endpoint: int = 5,
        include_security: bool = True,
        include_negative: bool = True,
    ):
        """
        Args:
            api_key: API key Guimí para geração via LLM (premium).
            max_cases_per_endpoint: Máximo de casos por endpoint.
            include_security: Incluir casos de segurança.
            include_negative: Incluir casos negativos.
        """
        self.api_key = api_key
        self.max_cases_per_endpoint = max_cases_per_endpoint
        self.include_security = include_security
        self.include_negative = include_negative

    def generate(self, spec: APISpec) -> List[TestCase]:
        """
        Gera casos de teste para todos os endpoints do spec.

        Args:
            spec: APISpec com endpoints descobertos.

        Returns:
            Lista de TestCase gerados.
        """
        all_cases: List[TestCase] = []

        for endpoint in spec.endpoints:
            cases = self._generate_for_endpoint(endpoint, spec.base_url)
            all_cases.extend(cases)

        return all_cases

    def generate_for_endpoint(self, endpoint: APIEndpoint, base_url: str = "") -> List[TestCase]:
        """Gera casos de teste para um único endpoint."""
        return self._generate_for_endpoint(endpoint, base_url)

    def _generate_for_endpoint(self, endpoint: APIEndpoint, base_url: str) -> List[TestCase]:
        """Lógica interna de geração por endpoint."""
        cases: List[TestCase] = []

        # 1. Happy path
        cases.append(self._make_happy_path(endpoint))

        # 2. Casos negativos
        if self.include_negative:
            cases.extend(self._make_negative_cases(endpoint))

        # 3. Edge cases de segurança
        if self.include_security:
            cases.extend(self._make_security_cases(endpoint))

        # 4. Limitar ao máximo configurado
        return cases[:self.max_cases_per_endpoint]

    def _make_happy_path(self, endpoint: APIEndpoint) -> TestCase:
        """Gera o caso de teste positivo (happy path)."""
        path_params = self._extract_path_params(endpoint)
        query_params = self._extract_query_params(endpoint)
        body = self._generate_body(endpoint) if endpoint.has_body else None

        # Status esperado baseado no método
        expected_status_map = {
            "GET": 200,
            "POST": 201,
            "PUT": 200,
            "PATCH": 200,
            "DELETE": 204,
            "HEAD": 200,
        }
        expected_status = expected_status_map.get(endpoint.method, 200)

        return TestCase(
            name=f"[POSITIVE] {endpoint.method} {endpoint.path}",
            description=f"Happy path: {endpoint.full_description}",
            endpoint=endpoint,
            method=endpoint.method,
            path=endpoint.path,
            path_params=path_params,
            query_params=query_params,
            body=body,
            expected_status=expected_status,
            category="positive",
            priority="high",
            tags=endpoint.tags + ["happy-path", "auto-generated"],
        )

    def _make_negative_cases(self, endpoint: APIEndpoint) -> List[TestCase]:
        """Gera casos negativos: 404, 401, 422."""
        cases: List[TestCase] = []

        # 404 — recurso não encontrado (para paths com ID)
        if "{" in endpoint.path and endpoint.method in ("GET", "PUT", "PATCH", "DELETE"):
            path_params = {
                k: "00000000-0000-0000-0000-000000000000"
                for k in self._get_path_param_names(endpoint)
            }
            cases.append(TestCase(
                name=f"[NEGATIVE] {endpoint.method} {endpoint.path} — not found",
                description="Deve retornar 404 para recurso inexistente",
                endpoint=endpoint,
                method=endpoint.method,
                path=endpoint.path,
                path_params=path_params,
                expected_status=404,
                category="negative",
                priority="medium",
                tags=endpoint.tags + ["not-found", "auto-generated"],
            ))

        # 401 — sem autenticação (se endpoint requer auth)
        if endpoint.requires_auth:
            cases.append(TestCase(
                name=f"[NEGATIVE] {endpoint.method} {endpoint.path} — unauthorized",
                description="Deve retornar 401 sem token de autenticação",
                endpoint=endpoint,
                method=endpoint.method,
                path=endpoint.path,
                path_params=self._extract_path_params(endpoint),
                headers={},  # sem Authorization
                expected_status=401,
                category="negative",
                priority="high",
                tags=endpoint.tags + ["unauthorized", "security", "auto-generated"],
            ))

        # 422 — payload inválido (para endpoints com body)
        if endpoint.has_body:
            cases.append(TestCase(
                name=f"[NEGATIVE] {endpoint.method} {endpoint.path} — invalid payload",
                description="Deve retornar 400/422 para payload inválido",
                endpoint=endpoint,
                method=endpoint.method,
                path=endpoint.path,
                path_params=self._extract_path_params(endpoint),
                body={"__invalid__": True, "missing_required_fields": True},
                expected_status=422,
                category="negative",
                priority="medium",
                tags=endpoint.tags + ["validation", "auto-generated"],
            ))

        return cases

    def _make_security_cases(self, endpoint: APIEndpoint) -> List[TestCase]:
        """Gera casos de segurança: SQL injection, XSS, overflow."""
        cases: List[TestCase] = []

        if not endpoint.has_body:
            return cases

        # SQL Injection no body
        cases.append(TestCase(
            name=f"[SECURITY] {endpoint.method} {endpoint.path} — SQL injection",
            description="Não deve ser vulnerável a SQL injection",
            endpoint=endpoint,
            method=endpoint.method,
            path=endpoint.path,
            path_params=self._extract_path_params(endpoint),
            body={"input": self.SECURITY_PAYLOADS["sql_injection"][0]},
            expected_status=400,  # deve rejeitar
            category="security",
            priority="critical",
            tags=endpoint.tags + ["sql-injection", "owasp", "auto-generated"],
        ))

        # XSS no body
        cases.append(TestCase(
            name=f"[SECURITY] {endpoint.method} {endpoint.path} — XSS",
            description="Não deve ser vulnerável a XSS",
            endpoint=endpoint,
            method=endpoint.method,
            path=endpoint.path,
            path_params=self._extract_path_params(endpoint),
            body={"input": self.SECURITY_PAYLOADS["xss"][0]},
            expected_status=400,
            category="security",
            priority="high",
            tags=endpoint.tags + ["xss", "owasp", "auto-generated"],
        ))

        return cases

    def _extract_path_params(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Extrai e preenche parâmetros de path com valores de exemplo."""
        params: Dict[str, Any] = {}
        for name in self._get_path_param_names(endpoint):
            # Tentar inferir tipo pelo nome
            if "id" in name.lower() or "uuid" in name.lower():
                params[name] = "00000000-0000-0000-0000-000000000001"
            elif "slug" in name.lower():
                params[name] = "test-slug"
            elif "version" in name.lower():
                params[name] = "v1"
            else:
                params[name] = "1"
        return params

    def _get_path_param_names(self, endpoint: APIEndpoint) -> List[str]:
        """Extrai nomes dos parâmetros de path do template."""
        import re
        return re.findall(r"\{(\w+)\}", endpoint.path)

    def _extract_query_params(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Extrai parâmetros de query com valores de exemplo."""
        params: Dict[str, Any] = {}
        for param in endpoint.parameters:
            if param.get("in") == "query" and param.get("required", False):
                schema = param.get("schema", {})
                param_type = schema.get("type", "string")
                name = param.get("name", "param")
                params[name] = self.EXAMPLE_VALUES.get(param_type, "test")
        return params

    def _generate_body(self, endpoint: APIEndpoint) -> Optional[Dict[str, Any]]:
        """Gera um body de exemplo baseado no schema do request body."""
        if not endpoint.request_body:
            return None

        # Tentar extrair schema do request body (OpenAPI 3.x)
        content = endpoint.request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if not schema:
            return {"data": "test"}

        return self._schema_to_example(schema)

    def _schema_to_example(self, schema: Dict[str, Any]) -> Any:
        """Converte um JSON Schema em um valor de exemplo."""
        schema_type = schema.get("type", "object")

        if schema_type == "object":
            result: Dict[str, Any] = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Preencher campos obrigatórios primeiro
            for prop_name in required:
                if prop_name in properties:
                    result[prop_name] = self._schema_to_example(properties[prop_name])

            # Preencher campos opcionais
            for prop_name, prop_schema in properties.items():
                if prop_name not in result:
                    result[prop_name] = self._schema_to_example(prop_schema)

            return result or {"data": "test"}

        elif schema_type == "array":
            items_schema = schema.get("items", {"type": "string"})
            return [self._schema_to_example(items_schema)]

        elif schema_type == "string":
            fmt = schema.get("format", "")
            return self.EXAMPLE_VALUES.get(fmt, self.EXAMPLE_VALUES["string"])

        elif schema_type == "integer":
            minimum = schema.get("minimum", 1)
            return max(1, minimum)

        elif schema_type == "number":
            return 1.0

        elif schema_type == "boolean":
            return True

        else:
            return None

    def export_to_csv(self, cases: List[TestCase], output_file: str) -> None:
        """Exporta casos de teste para CSV (compatível com guimi eval --dataset)."""
        import csv
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "method", "path", "body", "expected_status", "category", "priority"])
            writer.writeheader()
            for case in cases:
                writer.writerow({
                    "id": case.id,
                    "name": case.name,
                    "method": case.method,
                    "path": case.full_path,
                    "body": json.dumps(case.body) if case.body else "",
                    "expected_status": case.expected_status,
                    "category": case.category,
                    "priority": case.priority,
                })

    def export_to_json(self, cases: List[TestCase], output_file: str) -> None:
        """Exporta casos de teste para JSON."""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in cases], f, indent=2, ensure_ascii=False)
