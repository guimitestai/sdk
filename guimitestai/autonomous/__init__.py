"""
Módulo de Testes Autônomos de Integração — Guimí Test AI.

Descobre APIs automaticamente, gera casos de teste via LLM,
executa e detecta regressões sem intervenção humana.
"""

from guimitestai.autonomous.discovery import APIDiscovery, APIEndpoint, APISpec
from guimitestai.autonomous.generator import TestCase, TestGenerator
from guimitestai.autonomous.runner import TestResult, TestRunner
from guimitestai.autonomous.regression import RegressionDetector, RegressionReport

__all__ = [
    "APIDiscovery",
    "APIEndpoint",
    "APISpec",
    "TestCase",
    "TestGenerator",
    "TestResult",
    "TestRunner",
    "RegressionDetector",
    "RegressionReport",
]
