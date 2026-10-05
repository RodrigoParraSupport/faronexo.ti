"""Aplica el esquema y datos iniciales MySQL desde los archivos sql/."""

from pathlib import Path

import pymysql

from config import database_settings

ROOT = Path(__file__).resolve().parent
SCRIPTS = (
    "01_esquema.sql",
    "02_triggers.sql",
    "03_procedimiento.sql",
    "04_datos_iniciales.sql",
)


def sql_statements(script: str):
    """Separa sentencias y respeta DELIMITER para los cuerpos de rutinas."""
    delimiter = ";"
    buffer = ""
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(maxsplit=1)[1]
            continue
        buffer += line + "\n"
        while delimiter in buffer:
            statement, buffer = buffer.split(delimiter, 1)
            if statement.strip():
                yield statement.strip()
    if buffer.strip():
        yield buffer.strip()


def main() -> None:
    settings = database_settings()
    print(f"Destino MySQL: {settings['host']}:{settings['port']} / {settings['database']}")
    is_production = "prod" in str(settings["database"]).lower()
    if is_production:
        warning = "Se detectó una base cuyo nombre indica producción."
        print(warning)
        if input("Para autorizar explícitamente, escribe AUTORIZO-PRODUCCION: ").strip() != "AUTORIZO-PRODUCCION":
            print("Operación cancelada. No se modificó la base de datos.")
            return

    print("Este asistente creará las tablas, rutinas y registros de ejemplo.")
    if input("Escribe APLICAR para continuar: ").strip() != "APLICAR":
        print("Operación cancelada. No se modificó la base de datos.")
        return

    conn = pymysql.connect(**settings)
    try:
        for filename in SCRIPTS:
            source = (ROOT / "sql" / filename).read_text(encoding="utf-8")
            with conn.cursor() as cur:
                for statement in sql_statements(source):
                    cur.execute(statement)
            conn.commit()
            print(f"Aplicado: {filename}")
    finally:
        conn.close()
    print("Esquema listo. Inicia la interfaz con: python app.py")


if __name__ == "__main__":
    try:
        main()
    except (pymysql.MySQLError, OSError, RuntimeError, ValueError) as exc:
        print(f"No se pudo preparar la base de datos: {exc}")
        raise SystemExit(1) from None
