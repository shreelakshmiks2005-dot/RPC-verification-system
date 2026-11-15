import pytest


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    from app.config import Settings
    settings = Settings()

    assert settings.database_url == "postgresql+asyncpg://test"
    assert settings.github_token == "ghp_test"
    assert settings.redis_url == "redis://localhost:6379"
