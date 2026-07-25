"""Testes da CLI guimi e do módulo de testes autônomos."""

import os
import pytest
import yaml


# ─────────────────────────────────────────────────────────────
# Testes: CLI
# ─────────────────────────────────────────────────────────────

class TestCLI:
    """Testes da CLI guimi."""

    def test_cli_app_importable(self):
        """CLI deve ser importável sem erros."""
        from guimitestai.cli.main import app
        assert app is not None

    def test_cli_templates_module_importable(self):
        """Módulo de templates deve ser importável."""
        from guimitestai.cli import templates
        assert templates is not None

    def test_cli_cicd_templates_exist(self):
        """Todos os templates CI/CD devem existir como arquivos."""
        templates_dir = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli", "cicd_templates"
        )
        expected = [
            "github_actions.yml",
            "gitlab_ci.yml",
            "azure_pipelines.yml",
            "Jenkinsfile",
            "buildspec.yml",
        ]
        for fname in expected:
            fpath = os.path.join(templates_dir, fname)
            assert os.path.exists(fpath), f"Template {fname} não encontrado"

    def test_github_actions_template_valid_yaml(self):
        """Template GitHub Actions deve ser YAML válido com jobs obrigatórios."""
        fpath = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli",
            "cicd_templates", "github_actions.yml"
        )
        with open(fpath) as f:
            content = yaml.safe_load(f)
        assert "jobs" in content
        assert "security-scan" in content["jobs"]
        assert "compliance-audit" in content["jobs"]
        assert "autonomous-tests" in content["jobs"]
        assert "llm-evaluation" in content["jobs"]

    def test_gitlab_ci_template_valid_yaml(self):
        """Template GitLab CI deve ser YAML válido com stages obrigatórios."""
        fpath = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli",
            "cicd_templates", "gitlab_ci.yml"
        )
        with open(fpath) as f:
            content = yaml.safe_load(f)
        assert "stages" in content
        assert "security-scan" in content
        assert "compliance-audit" in content
        assert "autonomous-tests" in content

    def test_azure_pipelines_template_valid_yaml(self):
        """Template Azure DevOps deve ser YAML válido com stages."""
        fpath = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli",
            "cicd_templates", "azure_pipelines.yml"
        )
        with open(fpath) as f:
            content = yaml.safe_load(f)
        assert "stages" in content
        stage_names = [s.get("stage") for s in content["stages"]]
        assert "SecurityScan" in stage_names
        assert "ComplianceAudit" in stage_names

    def test_buildspec_valid_yaml(self):
        """Template AWS CodeBuild deve existir e conter as seções obrigatórias."""
        fpath = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli",
            "cicd_templates", "buildspec.yml"
        )
        assert os.path.exists(fpath)
        with open(fpath) as f:
            content = f.read()
        assert "phases:" in content
        assert "build:" in content
        assert "post_build:" in content
        assert "artifacts:" in content
        assert "guimi" in content.lower()

    def test_jenkinsfile_exists_with_pipeline_syntax(self):
        """Jenkinsfile deve existir e conter sintaxe de pipeline declarativo."""
        fpath = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli",
            "cicd_templates", "Jenkinsfile"
        )
        assert os.path.exists(fpath)
        with open(fpath) as f:
            content = f.read()
        assert "pipeline {" in content
        assert "stages {" in content
        assert "stage(" in content
        assert "guimi" in content.lower()
        assert "GUIMI_API_KEY" in content

    def test_all_templates_mention_guimi(self):
        """Todos os templates devem referenciar o comando guimi."""
        templates_dir = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli", "cicd_templates"
        )
        for fname in ["github_actions.yml", "gitlab_ci.yml", "azure_pipelines.yml", "buildspec.yml"]:
            fpath = os.path.join(templates_dir, fname)
            with open(fpath) as f:
                content = f.read()
            assert "guimi" in content.lower(), f"{fname} não menciona guimi"

    def test_all_templates_mention_lgpd(self):
        """Todos os templates devem referenciar LGPD."""
        templates_dir = os.path.join(
            os.path.dirname(__file__), "..", "guimitestai", "cli", "cicd_templates"
        )
        for fname in ["github_actions.yml", "gitlab_ci.yml", "azure_pipelines.yml", "buildspec.yml"]:
            fpath = os.path.join(templates_dir, fname)
            with open(fpath) as f:
                content = f.read()
            assert "lgpd" in content.lower(), f"{fname} não menciona LGPD"


# ─────────────────────────────────────────────────────────────
# Testes: Módulo Autonomous
# ─────────────────────────────────────────────────────────────

class TestAutonomous:
    """Testes do módulo de testes autônomos de integração."""

    def test_autonomous_modules_importable(self):
        """Todos os módulos autonomous devem ser importáveis."""
        from guimitestai.autonomous import (
            APIDiscovery, TestGenerator, TestRunner, RegressionDetector
        )
        assert APIDiscovery is not None
        assert TestGenerator is not None
        assert TestRunner is not None
        assert RegressionDetector is not None

    def test_api_discovery_init(self):
        """APIDiscovery deve inicializar com a URL base correta."""
        from guimitestai.autonomous.discovery import APIDiscovery
        d = APIDiscovery("http://localhost:8000")
        assert d.base_url == "http://localhost:8000"

    def test_api_discovery_strips_trailing_slash(self):
        """APIDiscovery deve normalizar a URL removendo barra final."""
        from guimitestai.autonomous.discovery import APIDiscovery
        d = APIDiscovery("http://localhost:8000/")
        assert not d.base_url.endswith("/")

    def test_test_generator_init_defaults(self):
        """TestGenerator deve inicializar com parâmetros padrão razoáveis."""
        from guimitestai.autonomous.generator import TestGenerator
        g = TestGenerator()
        assert g.max_cases_per_endpoint >= 1
        assert g.max_cases_per_endpoint <= 20

    def test_test_generator_custom_params(self):
        """TestGenerator deve aceitar parâmetros customizados."""
        from guimitestai.autonomous.generator import TestGenerator
        g = TestGenerator(max_cases_per_endpoint=3)
        assert g.max_cases_per_endpoint == 3

    def test_test_runner_init(self):
        """TestRunner deve inicializar com a URL base correta."""
        from guimitestai.autonomous.runner import TestRunner
        r = TestRunner("http://localhost:8000")
        assert r.base_url == "http://localhost:8000"

    def test_regression_detector_init(self):
        """RegressionDetector deve inicializar com o caminho do baseline."""
        from pathlib import Path
        from guimitestai.autonomous.regression import RegressionDetector
        rd = RegressionDetector(".guimi-baseline.json")
        assert rd.baseline_file == Path(".guimi-baseline.json")

    def test_regression_detector_no_baseline_no_error(self):
        """RegressionDetector sem baseline existente não deve lançar erro."""
        from guimitestai.autonomous.regression import RegressionDetector
        from pathlib import Path
        rd = RegressionDetector("/tmp/nonexistent-baseline-guimi-xyz-12345.json")
        assert rd.baseline_file == Path("/tmp/nonexistent-baseline-guimi-xyz-12345.json")
        assert rd is not None

    def test_autonomous_init_exports(self):
        """Pacote autonomous deve exportar as 4 classes principais."""
        import guimitestai.autonomous as auto
        assert hasattr(auto, "APIDiscovery")
        assert hasattr(auto, "TestGenerator")
        assert hasattr(auto, "TestRunner")
        assert hasattr(auto, "RegressionDetector")
