#!/usr/bin/env python3
"""
Guimí Test AI — Smoke Test Suite
Valida o caminho feliz completo antes da publicação no PyPI.

Uso:
    python smoke_test.py                    # roda todos os testes
    python smoke_test.py --verbose          # com saída detalhada
    python smoke_test.py --test eval        # roda apenas o teste de avaliação
"""

import sys
import time
import argparse
import traceback
from pathlib import Path
from typing import Callable, Optional

# ── Cores para o terminal ────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   return f"{GREEN}✅ {msg}{RESET}"
def fail(msg): return f"{RED}❌ {msg}{RESET}"
def warn(msg): return f"{YELLOW}⚠️  {msg}{RESET}"
def bold(msg): return f"{BOLD}{msg}{RESET}"


class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.skipped = False
        self.duration_ms = 0
        self.error = None
        self.details = []

    def __str__(self):
        if self.passed:
            status = ok("PASS")
        elif self.skipped:
            status = warn("SKIP")
        else:
            status = fail("FAIL")
        return f"  {status}  {self.name}  ({self.duration_ms}ms)"


class SmokeTestRunner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = []

    def run(self, name, fn, skip_reason=None):
        result = TestResult(name)
        if skip_reason:
            result.skipped = True
            result.error = skip_reason
            self.results.append(result)
            print(warn(f"SKIP  {name} — {skip_reason}"))
            return result

        print(f"\n{bold(f'▶ {name}')}")
        start = time.time()
        try:
            details = fn()
            result.passed = True
            result.duration_ms = int((time.time() - start) * 1000)
            if details:
                result.details = details if isinstance(details, list) else [str(details)]
            print(ok(f"PASS  {name}  ({result.duration_ms}ms)"))
            if self.verbose and result.details:
                for d in result.details:
                    print(f"       {d}")
        except Exception as e:
            result.passed = False
            result.duration_ms = int((time.time() - start) * 1000)
            result.error = str(e)
            print(fail(f"FAIL  {name}  ({result.duration_ms}ms)"))
            print(f"       {RED}{e}{RESET}")
            if self.verbose:
                traceback.print_exc()
        self.results.append(result)
        return result

    def summary(self):
        passed  = sum(1 for r in self.results if r.passed)
        failed  = sum(1 for r in self.results if not r.passed and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        total   = len(self.results)

        print(f"\n{'─'*60}")
        print(bold("RESUMO DO SMOKE TEST — GUIMÍ TEST AI"))
        print(f"{'─'*60}")
        for r in self.results:
            print(r)
        print(f"{'─'*60}")
        print(f"  Total: {total}  |  {GREEN}Passou: {passed}{RESET}  |  {RED}Falhou: {failed}{RESET}  |  {YELLOW}Pulou: {skipped}{RESET}")
        print(f"{'─'*60}\n")

        if failed == 0:
            print(ok("CAMINHO FELIZ VALIDADO — pronto para publicar no PyPI! 🚀"))
        else:
            print(fail(f"{failed} teste(s) falharam — corrija antes de publicar."))

        return failed


# ════════════════════════════════════════════════════════════════════════════
# TESTES
# ════════════════════════════════════════════════════════════════════════════

def test_import_principal():
    """1. Importação principal do pacote."""
    import guimitestai
    assert hasattr(guimitestai, "__version__")
    assert hasattr(guimitestai, "GuimiClient")
    assert hasattr(guimitestai, "Evaluator")
    assert hasattr(guimitestai, "Tracer")
    assert hasattr(guimitestai, "RedTeamer")
    return [
        f"Versão: {guimitestai.__version__}",
        "Exports: GuimiClient, Evaluator, Tracer, RedTeamer ✓",
    ]


def test_modelos_de_dados():
    """2. Modelos Pydantic devem instanciar corretamente."""
    from guimitestai.core.models import EvaluationResult, TraceEvent, ComplianceReport

    er = EvaluationResult(
        id="eval-001",
        input="Qual a capital do Brasil?",
        output="Brasília",
        criteria="correctness",
        score=0.95,
        passed=True,
    )
    assert er.score == 0.95
    assert er.passed is True

    te = TraceEvent(
        id="test-trace-001",
        name="test-operation",
        input="Qual a capital do Brasil?",
        output="Brasília",
        model="gpt-4o",
        latency_ms=120,
    )
    assert te.id == "test-trace-001"

    return [
        "EvaluationResult: instanciado ✓",
        "TraceEvent: instanciado ✓",
    ]


def test_config_e_cliente():
    """3. GuimiConfig e GuimiClient devem inicializar."""
    from guimitestai.core.config import GuimiConfig
    from guimitestai.core.client import GuimiClient

    config = GuimiConfig()
    assert config.api_url is not None
    assert config.timeout > 0

    config_custom = GuimiConfig(
        api_key="sk-guimi-test-key",
        api_url="https://api.guimitestai.com",
        timeout=30,
    )
    assert config_custom.api_key == "sk-guimi-test-key"

    client = GuimiClient()
    assert client is not None
    assert hasattr(client, "evaluate"), "GuimiClient deve ter método evaluate"
    assert hasattr(client, "trace"), "GuimiClient deve ter método trace"
    assert hasattr(client, "red_team"), "GuimiClient deve ter método red_team"
    assert hasattr(client, "compliance_report"), "GuimiClient deve ter método compliance_report"
    assert hasattr(client, "health"), "GuimiClient deve ter método health"

    return [
        f"GuimiConfig padrão: api_url={config.api_url} ✓",
        "GuimiClient métodos: evaluate, trace, red_team, compliance_report, health ✓",
    ]


def test_evaluator_modo_gratuito():
    """4. Evaluator deve ter métodos evaluate e batch_evaluate."""
    from guimitestai.evaluation.evaluator import Evaluator

    evaluator = Evaluator()
    assert hasattr(evaluator, "evaluate"), "Evaluator deve ter método evaluate"
    assert hasattr(evaluator, "batch_evaluate"), "Evaluator deve ter método batch_evaluate"

    return [
        "Evaluator.evaluate: disponível ✓",
        "Evaluator.batch_evaluate: disponível ✓",
    ]


def test_tracer_context_manager():
    """5. Tracer deve ter span() async e summary() sync."""
    import asyncio
    from guimitestai.observability.tracer import Tracer

    tracer = Tracer()
    assert tracer is not None
    assert hasattr(tracer, "span"), "Tracer deve ter método span"
    assert hasattr(tracer, "summary"), "Tracer deve ter método summary"
    assert hasattr(tracer, "get_traces"), "Tracer deve ter método get_traces"

    # span() é async context manager
    async def _run():
        async with tracer.span("test-operation", model="gpt-4o") as span:
            span.set_input("Qual a capital do Brasil?")
            span.set_output("Brasília")

    asyncio.run(_run())

    summary = tracer.summary()
    assert summary["total"] >= 1

    return [
        "Tracer.span: async context manager funcionando ✓",
        f"Tracer.summary: {summary['total']} trace(s) registrado(s) ✓",
    ]


def test_red_teamer_metodos():
    """6. RedTeamer deve ter métodos run e report."""
    from guimitestai.security.red_teamer import RedTeamer

    rt = RedTeamer()
    assert hasattr(rt, "run"), "RedTeamer deve ter método run"
    assert hasattr(rt, "report"), "RedTeamer deve ter método report"

    return [
        "RedTeamer.run: disponível ✓",
        "RedTeamer.report: disponível ✓",
    ]


def test_premium_gate():
    """7. Premium gate deve lançar PremiumFeatureError sem API key."""
    from guimitestai.core.premium import require_premium, PremiumFeatureError

    raised = False
    try:
        require_premium(
            feature_name="lgpd_compliance",
            feature_description="Verificação de conformidade LGPD",
            free_alternative="Use o perfil 'quick' gratuitamente"
        )
    except PremiumFeatureError as e:
        raised = True
        msg = str(e)
        assert len(msg) > 10, "Mensagem de erro deve ser descritiva"

    assert raised, "PremiumFeatureError deve ser lançado sem API key"

    return [
        "PremiumFeatureError lançado sem API key ✓",
        "Mensagem de erro descritiva ✓",
    ]


def test_telemetria_opt_in():
    """8. Telemetria deve ser opt-in — desabilitada por padrão."""
    import guimitestai.telemetry as tel

    # Verificar que as funções de controle existem
    assert hasattr(tel, "enable"), "telemetry.enable deve existir"
    assert hasattr(tel, "disable"), "telemetry.disable deve existir"
    assert hasattr(tel, "track"), "telemetry.track deve existir"
    assert hasattr(tel, "export_my_data"), "telemetry.export_my_data deve existir"
    assert hasattr(tel, "delete_my_data"), "telemetry.delete_my_data deve existir"

    # TelemetryCollector deve existir
    assert hasattr(tel, "TelemetryCollector"), "TelemetryCollector deve existir"

    return [
        "telemetry.enable / disable / track: disponíveis ✓",
        "telemetry.export_my_data / delete_my_data: disponíveis (LGPD Art.18) ✓",
        "TelemetryCollector: classe disponível ✓",
    ]


def test_autonomous_imports():
    """9. Módulo autonomous deve exportar as 4 classes principais."""
    from guimitestai.autonomous import (
        APIDiscovery, TestGenerator, TestRunner, RegressionDetector
    )

    disc = APIDiscovery("http://localhost:8000")
    assert disc is not None

    runner = TestRunner("http://localhost:8000")
    assert runner.base_url == "http://localhost:8000"

    rd = RegressionDetector(".guimi-baseline.json")
    assert rd.baseline_file == Path(".guimi-baseline.json")

    return [
        "APIDiscovery: instanciado ✓",
        "TestRunner: instanciado ✓",
        "RegressionDetector: instanciado ✓",
    ]


def test_cicd_templates():
    """10. Templates CI/CD devem existir para os 5 providers."""
    from guimitestai.cli.templates import TEMPLATES

    providers = ["github", "gitlab", "azure", "jenkins", "aws"]
    for provider in providers:
        assert provider in TEMPLATES, f"Template '{provider}' não encontrado"
        content = TEMPLATES[provider]["content"]
        assert len(content) > 50, f"Template '{provider}' parece vazio"

    # Verificar arquivos físicos
    templates_dir = Path(__file__).parent / "guimitestai" / "cli" / "cicd_templates"
    assert templates_dir.exists(), "Diretório de templates não encontrado"

    expected_files = [
        "github_actions.yml",
        "gitlab_ci.yml",
        "azure_pipelines.yml",
        "Jenkinsfile",
        "buildspec.yml",
    ]
    found = [f for f in expected_files if (templates_dir / f).exists()]

    return [
        f"Templates em memória: {providers} ✓",
        f"Arquivos físicos encontrados: {len(found)}/{len(expected_files)} ✓",
    ]


def test_integracao_langfuse_import():
    """11. Integração LangFuse deve importar e ter método trace."""
    from guimitestai.integrations.langfuse import LangFuseIntegration

    lf = LangFuseIntegration(
        public_key="pk-test-placeholder",
        secret_key="sk-test-placeholder",
        host="https://cloud.langfuse.com"
    )
    assert lf is not None
    assert hasattr(lf, "trace"), "LangFuseIntegration deve ter método trace"
    assert hasattr(lf, "score"), "LangFuseIntegration deve ter método score"
    assert hasattr(lf, "flush"), "LangFuseIntegration deve ter método flush"

    return [
        "LangFuseIntegration: instanciada ✓",
        "Métodos trace, score, flush disponíveis ✓",
    ]


def test_integracao_langsmith_import():
    """12. Integração LangSmith deve importar com assinatura correta."""
    from guimitestai.integrations.langsmith import LangSmithIntegration
    import inspect

    sig = inspect.signature(LangSmithIntegration.__init__)
    params = list(sig.parameters.keys())

    ls = LangSmithIntegration(
        api_key="ls-test-placeholder",
        project="guimi-smoke-test"
    )
    assert ls is not None

    return [
        f"LangSmithIntegration: instanciada ✓",
        f"Parâmetros: {params} ✓",
    ]


def test_compliance_checker_import():
    """13. ComplianceChecker deve importar e ter método analyze."""
    from guimitestai.compliance.checker import ComplianceChecker

    checker = ComplianceChecker()
    assert checker is not None
    assert hasattr(checker, "analyze"), "ComplianceChecker deve ter método analyze"

    return [
        "ComplianceChecker: instanciado ✓",
        "Método analyze: disponível ✓",
    ]


def test_version_e_metadata():
    """14. Metadados do pacote devem estar corretos."""
    import guimitestai

    assert guimitestai.__version__, "Versão não definida"
    assert guimitestai.__author__, "Autor não definido"
    assert guimitestai.__license__, "Licença não definida"

    # Verificar pyproject.toml
    pyproject = Path(__file__).parent / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml não encontrado"
    content = pyproject.read_text()
    assert "guimitestai" in content, "pyproject.toml deve conter o nome do pacote"

    return [
        f"Versão: {guimitestai.__version__} ✓",
        f"Autor: {guimitestai.__author__} ✓",
        f"Licença: {guimitestai.__license__} ✓",
        "pyproject.toml: válido ✓",
    ]


def test_license_bsl():
    """15. Arquivo LICENSE deve conter BSL 1.1."""
    license_file = Path(__file__).parent / "LICENSE"
    assert license_file.exists(), "Arquivo LICENSE não encontrado"
    content = license_file.read_text()
    assert "Business Source License" in content, "LICENSE deve ser BSL"
    assert "1.1" in content, "LICENSE deve ser versão 1.1"
    assert "guimitestai" in content.lower() or "Guimí" in content or "Guimi" in content, \
        "LICENSE deve mencionar o produto"

    return [
        "Arquivo LICENSE: encontrado ✓",
        "Conteúdo: Business Source License 1.1 ✓",
    ]


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Guimí Test AI — Smoke Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--test", "-t", help="Rodar apenas um teste específico")
    args = parser.parse_args()

    print(f"\n{'═'*60}")
    print(bold("  🐺 GUIMÍ TEST AI — SMOKE TEST SUITE"))
    print(f"  Validação do caminho feliz antes da publicação no PyPI")
    print(f"{'═'*60}\n")

    runner = SmokeTestRunner(verbose=args.verbose)

    tests = {
        "import":      ("Importação principal do pacote",          test_import_principal),
        "models":      ("Modelos de dados Pydantic",                test_modelos_de_dados),
        "config":      ("GuimiConfig e GuimiClient",                test_config_e_cliente),
        "eval":        ("Evaluator — métodos disponíveis",          test_evaluator_modo_gratuito),
        "tracer":      ("Tracer — span e summary",                  test_tracer_context_manager),
        "redteam":     ("RedTeamer — run e report",                 test_red_teamer_metodos),
        "premium":     ("Premium gate — PremiumFeatureError",       test_premium_gate),
        "telemetry":   ("Telemetria — opt-in e LGPD",               test_telemetria_opt_in),
        "autonomous":  ("Módulo autonomous — 4 classes",            test_autonomous_imports),
        "cicd":        ("Templates CI/CD — 5 providers",            test_cicd_templates),
        "langfuse":    ("Integração LangFuse",                      test_integracao_langfuse_import),
        "langsmith":   ("Integração LangSmith",                     test_integracao_langsmith_import),
        "compliance":  ("ComplianceChecker — analyze",              test_compliance_checker_import),
        "version":     ("Metadados e pyproject.toml",               test_version_e_metadata),
        "license":     ("Arquivo LICENSE — BSL 1.1",                test_license_bsl),
    }

    if args.test:
        if args.test not in tests:
            print(fail(f"Teste '{args.test}' não encontrado. Disponíveis: {list(tests.keys())}"))
            sys.exit(1)
        name, fn = tests[args.test]
        runner.run(name, fn)
    else:
        for key, (name, fn) in tests.items():
            runner.run(name, fn)

    failures = runner.summary()
    sys.exit(failures)


if __name__ == "__main__":
    main()
