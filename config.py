"""Configuración central de FaroNexo TI."""

import os

from dotenv import load_dotenv

load_dotenv()


def database_settings() -> dict[str, str | int]:
    """Lee la conexión MySQL desde variables de entorno."""
    required = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError("Faltan variables en .env: " + ", ".join(missing))

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "connect_timeout": 8,
        "charset": "utf8mb4",
    }
