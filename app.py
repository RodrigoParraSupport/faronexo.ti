"""Interfaz de FaroNexo TI, una mesa de ayuda clara y cercana."""

from __future__ import annotations

from datetime import datetime

import flet as ft

import database

TEAL = "#147D7A"
INK = "#15283F"
STATUSES = ["Todos", "Abierto", "En progreso", "En espera", "Cerrado"]
PRIORITIES = ["Baja", "Media", "Alta", "Urgente"]


def main(page: ft.Page) -> None:
    page.title = "FaroNexo TI | Mesa de ayuda"
    page.theme = ft.Theme(color_scheme_seed=TEAL, use_material3=True)
    page.bgcolor = "#F3F7F6"
    page.padding = 26
    page.window_min_width = 970
    page.window_min_height = 650

    notice = ft.Text(size=13)
    search = ft.TextField(
        hint_text="Buscar por asunto, persona o técnico",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_submit=lambda _: refresh(),
    )
    status_filter = ft.Dropdown(
        label="Estado", value="Todos", width=175,
        options=[ft.dropdown.Option(key=s, text=s) for s in STATUSES],
        on_change=lambda _: refresh(),
    )
    summary = ft.Row(spacing=12, wrap=True)
    ticket_list = ft.Column(spacing=10)

    def message(value: str, color: str = TEAL) -> None:
        notice.value, notice.color = value, color
        page.update()

    def panel(label: str, count: int, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=12, color="#526477"),
                ft.Text(str(count), size=25, weight=ft.FontWeight.BOLD, color=color),
            ], spacing=2),
            padding=14, width=150, bgcolor="white", border_radius=13,
            border=ft.border.all(1, "#E2EAE8"),
        )

    def tag(label: str, color: str, background: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=11, color=color, weight=ft.FontWeight.W_600),
            padding=ft.padding.symmetric(horizontal=9, vertical=5),
            bgcolor=background, border_radius=18,
        )

    def timestamp(value: datetime) -> str:
        return value.astimezone().strftime("%d-%m-%Y %H:%M")

    def history(ticket: dict) -> None:
        try:
            entries = database.ticket_history(ticket["id"])
            controls = [ft.ListTile(
                leading=ft.Icon(ft.Icons.HISTORY, color=TEAL),
                title=ft.Text(f"{row['estado_anterior'] or 'Creado'} → {row['estado_nuevo']}"),
                subtitle=ft.Text(timestamp(row["cambiado_en"])),
            ) for row in entries]
            if not controls:
                controls = [ft.Text("Todavía no hay movimientos registrados.")]
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Actividad · FN-{ticket['id']:04d}"),
                content=ft.Column(controls, tight=True, scroll=ft.ScrollMode.AUTO),
                actions=[ft.TextButton("Cerrar", on_click=lambda _: page.close(dialog))],
            )
            page.open(dialog)
        except Exception as exc:
            message(f"No se pudo cargar el historial: {exc}", "#A33A32")

    def edit_form(ticket: dict | None = None) -> None:
        try:
            catalogs = database.fetch_catalogs()
        except Exception as exc:
            message(f"No se pudieron cargar los catálogos: {exc}", "#A33A32")
            return

        subject = ft.TextField(label="Asunto", max_length=140, value=ticket["asunto"] if ticket else "")
        description = ft.TextField(
            label="Describe el problema", multiline=True, min_lines=3, max_lines=5,
            value=ticket["descripcion"] if ticket else "",
        )
        priority = ft.Dropdown(
            label="Prioridad", expand=True,
            value=ticket["prioridad"] if ticket else "Media",
            options=[ft.dropdown.Option(key=x, text=x) for x in PRIORITIES],
        )
        requester = ft.Dropdown(
            label="Solicitante", expand=True,
            value=str(ticket["solicitante_id"]) if ticket else None,
            options=[ft.dropdown.Option(key=str(x["id"]), text=x["nombre"])
                     for x in catalogs["employees"]],
        )
        technician_options = [ft.dropdown.Option(key="", text="Sin asignar")]
        technician_options.extend(ft.dropdown.Option(key=str(x["id"]), text=x["nombre"])
                                  for x in catalogs["technicians"])
        technician = ft.Dropdown(
            label="Técnico responsable", expand=True,
            value=str(ticket["tecnico_id"]) if ticket and ticket["tecnico_id"] else "",
            options=technician_options,
        )
        chosen = set(ticket["especialidades"].split(", ")) if ticket else set()
        specialty_controls = [
            ft.Checkbox(label=x["nombre"], value=x["nombre"] in chosen, data=x["id"])
            for x in catalogs["specialties"]
        ]
        specialties = ft.Column(specialty_controls, spacing=0)
        dialog = ft.AlertDialog(modal=True, title=ft.Text("Actualizar solicitud" if ticket else "Nueva solicitud"))

        def save(_: ft.ControlEvent) -> None:
            if len((subject.value or "").strip()) < 5 or len((description.value or "").strip()) < 10:
                message("Usa un asunto de 5 caracteres y una descripción de 10.", "#A76B12")
                return
            if requester.value is None:
                message("Selecciona quién solicita el soporte.", "#A76B12")
                return
            try:
                database.save_ticket(
                    ticket["id"] if ticket else None,
                    subject.value.strip(), description.value.strip(), priority.value,
                    int(requester.value), int(technician.value) if technician.value else None,
                    [int(c.data) for c in specialties.controls if c.value],
                )
                page.close(dialog)
                message("Solicitud guardada.")
                refresh()
            except Exception as exc:
                message(f"No se pudo guardar la solicitud: {exc}", "#A33A32")

        dialog.content = ft.Column(
            [subject, description, ft.Row([priority, requester]), technician,
             ft.Text("Áreas de apoyo", weight=ft.FontWeight.W_600), specialties],
            width=530, tight=True, scroll=ft.ScrollMode.AUTO, spacing=11,
        )
        dialog.actions = [
            ft.TextButton("Cancelar", on_click=lambda _: page.close(dialog)),
            ft.FilledButton("Guardar solicitud", icon=ft.Icons.SAVE, on_click=save),
        ]
        page.open(dialog)

    def close_form(ticket: dict) -> None:
        resolution = ft.TextField(
            label="Resolución aplicada", multiline=True, min_lines=3, max_lines=5,
            hint_text="Explica qué se hizo para resolver el caso.",
        )
        dialog = ft.AlertDialog(modal=True, title=ft.Text(f"Cerrar FN-{ticket['id']:04d}"), content=resolution)

        def close(_: ft.ControlEvent) -> None:
            if len((resolution.value or "").strip()) < 10:
                message("Explica la resolución con al menos 10 caracteres.", "#A76B12")
                return
            try:
                database.close_ticket(ticket["id"], resolution.value)
                page.close(dialog)
                message("Ticket cerrado y su historial actualizado.")
                refresh()
            except Exception as exc:
                message(f"No se pudo cerrar: {exc}", "#A33A32")

        dialog.actions = [
            ft.TextButton("Volver", on_click=lambda _: page.close(dialog)),
            ft.FilledButton("Confirmar cierre", icon=ft.Icons.CHECK, on_click=close),
        ]
        page.open(dialog)

    def delete_form(ticket: dict) -> None:
        dialog = ft.AlertDialog(
            modal=True, title=ft.Text("Eliminar solicitud"),
            content=ft.Text(f"Se eliminará FN-{ticket['id']:04d} y su historial. ¿Continuar?"),
        )

        def remove(_: ft.ControlEvent) -> None:
            try:
                database.delete_ticket(ticket["id"])
                page.close(dialog)
                message("Solicitud eliminada.")
                refresh()
            except Exception as exc:
                message(f"No se pudo eliminar: {exc}", "#A33A32")

        dialog.actions = [
            ft.TextButton("Cancelar", on_click=lambda _: page.close(dialog)),
            ft.FilledButton("Eliminar", icon=ft.Icons.DELETE_OUTLINE, on_click=remove),
        ]
        page.open(dialog)

    def make_ticket_card(ticket: dict) -> ft.Container:
        states = {
            "Abierto": ("#8A4511", "#FFF2DD"),
            "En progreso": ("#155CA1", "#E7F1FC"),
            "En espera": ("#65519A", "#F0EBFB"),
            "Cerrado": ("#17634C", "#E4F4ED"),
        }
        priorities = {
            "Urgente": ("#A33A32", "#FCE9E7"),
            "Alta": ("#A45B12", "#FFF1DF"),
            "Media": ("#375878", "#EAF1F6"),
            "Baja": ("#526477", "#F0F3F5"),
        }
        state_color, state_bg = states[ticket["estado"]]
        priority_color, priority_bg = priorities[ticket["prioridad"]]
        actions = [
            ft.IconButton(ft.Icons.HISTORY, tooltip="Ver historial", on_click=lambda _: history(ticket)),
            ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Editar", on_click=lambda _: edit_form(ticket)),
        ]
        if ticket["estado"] != "Cerrado":
            actions.append(ft.IconButton(ft.Icons.TASK_ALT, tooltip="Cerrar", on_click=lambda _: close_form(ticket)))
        actions.append(ft.IconButton(
            ft.Icons.DELETE_OUTLINE, tooltip="Eliminar", icon_color="#A33A32",
            on_click=lambda _: delete_form(ticket),
        ))
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"FN-{ticket['id']:04d}", color=TEAL, weight=ft.FontWeight.BOLD),
                    ft.Text(ticket["asunto"], size=16, weight=ft.FontWeight.W_600, expand=True),
                    *actions,
                ]),
                ft.Text(ticket["descripcion"], color="#526477", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Row([
                    tag(ticket["estado"], state_color, state_bg),
                    tag(ticket["prioridad"], priority_color, priority_bg),
                    ft.Text(f"Solicita {ticket['solicitante']}", size=11, color="#526477"),
                    ft.Text(f"Técnico: {ticket['tecnico'] or 'Por asignar'}", size=11, color="#526477"),
                    ft.Text(f"Áreas: {ticket['especialidades'] or 'Sin clasificar'}", size=11, color="#526477", expand=True),
                    ft.Text(timestamp(ticket["creado_en"]), size=10, color="#748393"),
                ], wrap=True, spacing=7),
            ], spacing=8),
            padding=15, bgcolor="white", border_radius=14,
            border=ft.border.all(1, "#E2EAE8"),
        )

    def refresh(_: ft.ControlEvent | None = None) -> None:
        try:
            totals = database.ticket_summary()
            summary.controls = [
                panel("Solicitudes", sum(totals.values()), INK),
                panel("Abiertas", totals.get("Abierto", 0), "#8A4511"),
                panel("En progreso", totals.get("En progreso", 0), "#155CA1"),
                panel("En espera", totals.get("En espera", 0), "#65519A"),
                panel("Resueltas", totals.get("Cerrado", 0), "#17634C"),
            ]
            tickets = database.list_tickets(search.value or "", status_filter.value or "Todos")
            ticket_list.controls = [make_ticket_card(t) for t in tickets]
            if not tickets:
                ticket_list.controls = [ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX_OUTLINED, size=34, color=TEAL),
                        ft.Text("No encontramos solicitudes", size=17, weight=ft.FontWeight.W_600),
                        ft.Text("Prueba otra búsqueda o registra un ticket nuevo.", color="#526477"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=34, alignment=ft.alignment.center,
                )]
            page.update()
        except Exception as exc:
            ticket_list.controls = [ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CLOUD_OFF_OUTLINED, size=32, color="#A33A32"),
                    ft.Text("No hay conexión con la base de datos", size=17, weight=ft.FontWeight.BOLD),
                    ft.Text("Revisa .env y ejecuta setup_database.py en una base de desarrollo.", color="#526477"),
                    ft.Text(str(exc), size=11, color="#748393"),
                ], spacing=9),
                padding=24, bgcolor="white", border_radius=14,
            )]
            page.update()

    page.add(ft.Column([
        ft.Row([
            ft.Container(ft.Icon(ft.Icons.HUB_OUTLINED, size=27, color="white"),
                         padding=11, bgcolor=TEAL, border_radius=13),
            ft.Column([
                ft.Text("FaroNexo TI", size=24, weight=ft.FontWeight.BOLD, color=INK),
                ft.Text("Mesa de ayuda · Servicio que conecta", size=12, color="#526477"),
            ], spacing=1, expand=True),
            ft.FilledButton("Nueva solicitud", icon=ft.Icons.ADD, on_click=lambda _: edit_form()),
        ]),
        summary,
        ft.Row([search, status_filter], spacing=11),
        notice,
        ft.Text("Bandeja de solicitudes", size=18, weight=ft.FontWeight.BOLD, color=INK),
        ft.Container(content=ticket_list, expand=True),
    ], spacing=16, expand=True))
    refresh()


if __name__ == "__main__":
    ft.app(target=main)
