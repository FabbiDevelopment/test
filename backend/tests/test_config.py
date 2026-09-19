import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_loads_required_environment_values(monkeypatch):
    configured_values = {
        "DATABASE_URL": "sqlite+aiosqlite:///./configured-test.db",
        "REDIS_URL": "redis://localhost:6379/5",
        "JWT_SECRET": "configured-test-jwt-secret",
        "CORS_ORIGINS": "http://localhost:3000",
    }
    for setting, value in configured_values.items():
        monkeypatch.setenv(setting, value)

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL == configured_values["DATABASE_URL"]
    assert settings.REDIS_URL == configured_values["REDIS_URL"]
    assert settings.JWT_SECRET == configured_values["JWT_SECRET"]
    assert settings.DB_ECHO is False
    assert settings.cors_origins == ["http://localhost:3000"]


def test_settings_parse_and_validate_cors_origins(monkeypatch):
    configured_values = {
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/0",
        "JWT_SECRET": "test-only-jwt-secret",
        "CORS_ORIGINS": "https://app.example.com, https://admin.example.com/",
    }
    for setting, value in configured_values.items():
        monkeypatch.setenv(setting, value)

    settings = Settings(_env_file=None)

    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]

    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("missing_setting", ["DATABASE_URL", "REDIS_URL", "JWT_SECRET"])
def test_sensitive_settings_are_required(monkeypatch, missing_setting):
    configured_values = {
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/0",
        "JWT_SECRET": "test-only-jwt-secret",
    }
    for setting, value in configured_values.items():
        monkeypatch.setenv(setting, value)
    monkeypatch.delenv(missing_setting)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
