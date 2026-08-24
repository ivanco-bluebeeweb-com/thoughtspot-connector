"""The single 'App settings' screen (center slot) -- connection management
and health snapshot for ThoughtSpot Connector."""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h
from schemas import AuditHealthParams


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or c.get("instance_hostname", "")
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(label, variant="body"),
        ui.Text(f"Instance: {c.get('instance_hostname', '')}", variant="caption"),
        ui.Button("Disconnect", variant="danger", size="sm",
                  on_click=ui.Call("disconnect_thoughtspot", {"connection_id": c.get("id")})),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Stack(direction="v", gap=1, children=[
            ui.Text("Connections", variant="heading"),
            ui.Text("No instances connected yet.", variant="caption"),
        ])
    children: list[ui.UINode] = [ui.Text("Connections", variant="heading")]
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, align="start", children=children)


@ext.panel("thoughtspot_settings", slot="center", title="App settings", icon="⚙️", center_overlay=True)
async def thoughtspot_settings_panel(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    audit_children: list[ui.UINode] = [ui.Text("Health snapshot", variant="heading")]
    if connections:
        result = await h.audit_instance_health(ctx, AuditHealthParams(connection_id=connections[0].get("id", "")))
        if result.success and result.data:
            a = result.data
            audit_children.append(ui.Stats(children=[
                {"label": "Liveboards", "value": str(a.liveboard_count)},
                {"label": "Answers", "value": str(a.answer_count)},
                {"label": "Worksheets", "value": str(a.worksheet_count)},
                {"label": "Users", "value": str(a.user_count)},
                {"label": "Tags", "value": str(a.tag_count)},
            ]))
        else:
            audit_children.append(ui.Text("Could not compute health snapshot.", variant="caption"))
    else:
        audit_children.append(ui.Text("Connect an instance to see its health snapshot.", variant="caption"))

    return ui.Stack(direction="v", gap=4, align="stretch", children=[
        _connections_section(connections),
        ui.Divider(),
        ui.Stack(direction="v", gap=2, align="stretch", children=audit_children),
    ])
