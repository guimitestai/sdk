"""Regression checks for canonical SDK configuration and metadata."""
import guimitestai
from guimitestai.cli.main import GUIMI_BRANDING, _get_client
from guimitestai.core.client import GuimiClient
from guimitestai.core.config import GuimiConfig
from guimitestai.core.constants import DEFAULT_API_URL, SDK_LICENSE, SDK_VERSION


def test_metadata_consistency():
    assert guimitestai.__version__ == SDK_VERSION
    assert guimitestai.__license__ == SDK_LICENSE == "BSL-1.1"
    assert GUIMI_BRANDING["_guimi"]["sdk_version"] == SDK_VERSION


def test_default_url(monkeypatch):
    monkeypatch.delenv("GUIMI_API_URL", raising=False)
    assert GuimiConfig().api_url == DEFAULT_API_URL
    client = GuimiClient()
    try:
        assert str(client._http.base_url).rstrip("/") == DEFAULT_API_URL
        assert client._http.headers["user-agent"] == f"guimitestai-python/{SDK_VERSION}"
    finally:
        import asyncio
        asyncio.run(client.close())


def test_environment_url(monkeypatch):
    monkeypatch.setenv("GUIMI_API_URL", "http://localhost:8765")
    client = GuimiClient()
    cli_client = _get_client()
    try:
        assert GuimiConfig().api_url == "http://localhost:8765"
        assert str(client._http.base_url).rstrip("/") == "http://localhost:8765"
        assert str(cli_client._http.base_url).rstrip("/") == "http://localhost:8765"
    finally:
        import asyncio
        asyncio.run(client.close())
        asyncio.run(cli_client.close())


def test_explicit_url_overrides_environment(monkeypatch):
    monkeypatch.setenv("GUIMI_API_URL", "http://localhost:8765")
    client = GuimiClient(api_url="http://localhost:9000")
    try:
        assert str(client._http.base_url).rstrip("/") == "http://localhost:9000"
    finally:
        import asyncio
        asyncio.run(client.close())


def test_global_config_uses_canonical_url(monkeypatch):
    monkeypatch.delenv("GUIMI_API_URL", raising=False)
    assert guimitestai.configure().api_url == DEFAULT_API_URL
