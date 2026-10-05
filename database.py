"""Acceso a datos MySQL para la mesa de ayuda FaroNexo TI."""

from __future__ import annotations

from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from config import database_settings


def connect() -> pymysql.Connection:
    return pymysql.connect(**database_settings(), cursorclass=DictCursor)


def fetch_catalogs() -> dict[str, list[dict[str, Any]]]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, nombre FROM fn_empleados WHERE activo = 1 ORDER BY nombre")
        employees = cur.fetchall()
        cur.execute(
            "SELECT e.id, e.nombre FROM fn_empleados e "
            "JOIN fn_empleado_especialidad ee ON ee.empleado_id = e.id "
            "WHERE e.activo = 1 AND e.rol IN ('tecnico', 'ambos') ORDER BY e.nombre"
        )
        technicians = cur.fetchall()
        cur.execute("SELECT id, nombre FROM fn_especialidades ORDER BY nombre")
        specialties = cur.fetchall()
    return {"employees": employees, "technicians": technicians, "specialties": specialties}


def list_tickets(search: str = "", status: str = "Todos") -> list[dict[str, Any]]:
    query = """
        SELECT t.id, t.asunto, t.descripcion, t.estado, t.prioridad,
               t.creado_en, t.actualizado_en, t.solicitante_id,
               t.tecnico_id, t.resolucion,
               solicitante.nombre AS solicitante,
               tecnico.nombre AS tecnico,
               COALESCE(GROUP_CONCAT(DISTINCT esp.nombre ORDER BY esp.nombre SEPARATOR ', '), '')
                   AS especialidades
        FROM fn_tickets t
        JOIN fn_empleados solicitante ON solicitante.id = t.solicitante_id
        LEFT JOIN fn_empleados tecnico ON tecnico.id = t.tecnico_id
        LEFT JOIN fn_ticket_especialidad te ON te.ticket_id = t.id
        LEFT JOIN fn_especialidades esp ON esp.id = te.especialidad_id
        WHERE (%s = '' OR t.asunto LIKE %s OR t.descripcion LIKE %s
               OR solicitante.nombre LIKE %s OR COALESCE(tecnico.nombre, '') LIKE %s)
          AND (%s = 'Todos' OR t.estado = %s)
        GROUP BY t.id, solicitante.nombre, tecnico.nombre
        ORDER BY CASE t.prioridad WHEN 'Urgente' THEN 0 WHEN 'Alta' THEN 1
                  WHEN 'Media' THEN 2 ELSE 3 END, t.creado_en DESC
    """
    term = f"%{search.strip()}%"
    with connect() as conn, conn.cursor() as cur:
        cur.execute(query, (search.strip(), term, term, term, term, status, status))
        return cur.fetchall()


def ticket_summary() -> dict[str, int]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT estado, COUNT(*) AS cantidad FROM fn_tickets GROUP BY estado")
        rows = cur.fetchall()
    return {row["estado"]: row["cantidad"] for row in rows}


def save_ticket(
    ticket_id: int | None, asunto: str, descripcion: str, prioridad: str,
    solicitante_id: int, tecnico_id: int | None, especialidad_ids: list[int],
) -> None:
    conn = connect()
    try:
        with conn.cursor() as cur:
            if ticket_id is None:
                cur.execute(
                    "INSERT INTO fn_tickets (asunto, descripcion, prioridad, solicitante_id, tecnico_id) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (asunto, descripcion, prioridad, solicitante_id, tecnico_id),
                )
                ticket_id = cur.lastrowid
            else:
                cur.execute(
                    "UPDATE fn_tickets SET asunto = %s, descripcion = %s, prioridad = %s, "
                    "solicitante_id = %s, tecnico_id = %s WHERE id = %s",
                    (asunto, descripcion, prioridad, solicitante_id, tecnico_id, ticket_id),
                )
                if cur.rowcount != 1:
                    raise ValueError("El ticket ya no existe.")
                cur.execute("DELETE FROM fn_ticket_especialidad WHERE ticket_id = %s", (ticket_id,))
            cur.executemany(
                "INSERT INTO fn_ticket_especialidad (ticket_id, especialidad_id) VALUES (%s, %s)",
                [(ticket_id, specialty_id) for specialty_id in especialidad_ids],
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_ticket(ticket_id: int) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM fn_tickets WHERE id = %s", (ticket_id,))
        if cur.rowcount != 1:
            raise ValueError("El ticket ya no existe.")
        conn.commit()


def close_ticket(ticket_id: int, resolution: str) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.callproc("fn_cerrar_ticket", (ticket_id, resolution.strip()))
        conn.commit()


def ticket_history(ticket_id: int) -> list[dict[str, Any]]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT estado_anterior, estado_nuevo, cambiado_en "
            "FROM fn_historial_ticket WHERE ticket_id = %s ORDER BY cambiado_en",
            (ticket_id,),
        )
        return cur.fetchall()
