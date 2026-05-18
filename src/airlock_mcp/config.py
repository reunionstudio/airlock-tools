from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


@dataclass(frozen=True)
class AirlockConfig:
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    application_name: str | None = None
    private_key_path: str | None = None
    private_key_passphrase: str | None = None
    password: str | None = None
    connection_name: str | None = None
    admin_tools_enabled: bool = False
    default_airlock_role: str | None = None
    max_inline_bytes: int = 1_048_576

    @classmethod
    def from_env(cls) -> "AirlockConfig":
        return cls(
            snowflake_account=os.getenv("AIRLOCK_SNOWFLAKE_ACCOUNT"),
            snowflake_user=os.getenv("AIRLOCK_SNOWFLAKE_USER"),
            snowflake_role=os.getenv("AIRLOCK_SNOWFLAKE_ROLE"),
            snowflake_warehouse=os.getenv("AIRLOCK_SNOWFLAKE_WAREHOUSE"),
            application_name=os.getenv("AIRLOCK_APPLICATION_NAME"),
            private_key_path=os.getenv("AIRLOCK_PRIVATE_KEY_PATH"),
            private_key_passphrase=os.getenv("AIRLOCK_PRIVATE_KEY_PASSPHRASE"),
            password=os.getenv("AIRLOCK_SNOWFLAKE_PASSWORD"),
            connection_name=os.getenv("AIRLOCK_SNOWFLAKE_CONNECTION_NAME"),
            admin_tools_enabled=_env_bool("AIRLOCK_MCP_ADMIN_TOOLS"),
            default_airlock_role=os.getenv("AIRLOCK_MCP_DEFAULT_AIRLOCK_ROLE"),
            max_inline_bytes=_env_int("AIRLOCK_MCP_MAX_INLINE_BYTES", 1_048_576),
        )

    def connection_parameters(self) -> dict[str, Any]:
        if self.connection_name:
            return {"connection_name": self.connection_name}

        params: dict[str, Any] = {}
        if self.snowflake_account:
            params["account"] = self.snowflake_account
        if self.snowflake_user:
            params["user"] = self.snowflake_user
        if self.snowflake_role:
            params["role"] = self.snowflake_role
        if self.snowflake_warehouse:
            params["warehouse"] = self.snowflake_warehouse
        if self.application_name:
            params["database"] = self.application_name
        if self.password:
            params["password"] = self.password
        if self.private_key_path:
            params["private_key"] = load_private_key_der(
                Path(self.private_key_path), self.private_key_passphrase
            )
            params.setdefault("authenticator", "SNOWFLAKE_JWT")
        return params


def load_private_key_der(path: Path, passphrase: str | None) -> bytes:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
    except ImportError as exc:  # pragma: no cover - dependency comes from Snowflake connector
        raise RuntimeError("cryptography is required for key-pair authentication") from exc

    password = passphrase.encode("utf-8") if passphrase else None
    private_key = serialization.load_pem_private_key(
        path.read_bytes(),
        password=password,
        backend=default_backend(),
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
