"""Panel UI -- connections/connect form + Tags list + center content.

SIDEBAR CONTENT -- NO CARDS, per ~/UI_INTERFACE_STANDARD.md. Every section is
a plain ui.Stack, content stacked vertically and left-aligned, sections
separated by ui.Divider() -- no Card border/background/shadow anywhere.
Disconnect lives in the "App settings" screen (panels_settings.py). The one
secondary "App settings" button is always the LAST element at the bottom.

Form is fully labelled (ui.Text caption + input) and stretched full-width
(align="stretch"). No setup instructions above the form -- that content
lives ONLY in the connect-help overlay, never duplicated in the sidebar.

CORRECTED ui.* usage (learned from Qlik/Looker Connector deploy rejections):
ui.Badge takes label+color (not variant); there is no ui.Column (use
ui.Stack direction="v"); ui.Input has no input_type kwarg; ui.DataTable
only accepts columns/rows/on_row_click/on_cell_edit; @ext.panel slot must be
one of bottom|center|chat-sidebar|left|overlay|right (NOT modal/main).
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__thoughtspot_settings"),
    )


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, children=[ui.Text(label, variant="caption"), node])


def _connect_section() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("How do I set this up?", variant="ghost", size="sm", icon="HelpCircle",
                  on_click=ui.Call("__panel__thoughtspot_connect_help")),
        ui.Form(
            action="connect_thoughtspot",
            submit_label="Verify and connect",
            children=[
                _field("Instance hostname", ui.Input(param_name="instance_hostname", placeholder="e.g. myorg.thoughtspot.cloud")),
                _field("Username", ui.Input(param_name="username", placeholder="Your ThoughtSpot username")),
                _field("Password", ui.Input(param_name="password", placeholder="Your ThoughtSpot password")),
                _field("Label (optional)", ui.Input(param_name="label", placeholder="e.g. Production instance")),
            ],
        ),
    ])


def _tag_row(tag: dict) -> ui.UINode:
    return ui.Button(
        tag.get("name", ""), variant="ghost", size="sm", full_width=True,
        on_click=ui.Call("__panel__thoughtspot_tag", {"tag": tag.get("id", "")}),
    )


def _connect_help_body() -> list[ui.UINode]:
    return [
        ui.Text("Connect ThoughtSpot", variant="heading"),
        ui.Text("1. Use your existing ThoughtSpot username/password, or create a service account.", variant="body"),
        ui.Text("2. Instance hostname is your org's ThoughtSpot Cloud domain, e.g. myorg.thoughtspot.cloud (for self-hosted, use your own domain).", variant="body"),
        ui.Text("3. Imperal validates the credentials by logging in immediately -- nothing is saved until that succeeds.", variant="body"),
    ]


@ext.panel("thoughtspot_connect_help", slot="overlay", title="Connect ThoughtSpot")
async def thoughtspot_connect_help(ctx, **kwargs) -> object:
    return ui.Stack(direction="v", gap=2, children=_connect_help_body())


@ext.panel("thoughtspot_sidebar", slot="left")
async def thoughtspot_sidebar(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", align="stretch", gap=3, children=[_connect_section(), ui.Divider(), _settings_button()])

    result = await h.list_tags(ctx, h.ConnectionScopedParams())
    tags = result.data.items if (result.success and result.data) else []

    children: list[ui.UINode] = [ui.Button(
        "All content", variant="ghost", size="sm", full_width=True,
        on_click=ui.Call("__panel__thoughtspot_tag", {"tag": ""}),
    )]
    if not tags:
        children.append(ui.Text("No tags on this instance yet.", variant="caption"))
    else:
        for i, t in enumerate(tags):
            children.append(_tag_row(t.model_dump()))

    return ui.Stack(direction="v", align="stretch", gap=3, children=[
        ui.Stack(direction="v", gap=1, align="stretch", children=children),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("thoughtspot_tag", slot="center", title="Content", icon="🏷️", center_overlay=True)
async def thoughtspot_tag_panel(ctx, tag: str = "", **kwargs) -> object:
    lb_result = await h.list_liveboards(ctx, h.ListLiveboardsParams(tag=tag))
    liveboards = lb_result.data.items if (lb_result.success and lb_result.data) else []
    ans_result = await h.list_answers(ctx, h.ListAnswersParams(tag=tag))
    answers = ans_result.data.items if (ans_result.success and ans_result.data) else []

    lb_table = ui.DataTable(
        columns=[{"key": "name", "label": "Name"}, {"key": "author_name", "label": "Author"}, {"key": "modified", "label": "Modified"}],
        rows=[l.model_dump() for l in liveboards],
        on_row_click=ui.Call("__panel__thoughtspot_liveboard", {"liveboard_id": "{id}"}),
    ) if liveboards else ui.Text("No Liveboards here.", variant="caption")

    ans_table = ui.DataTable(
        columns=[{"key": "name", "label": "Name"}, {"key": "author_name", "label": "Author"}, {"key": "modified", "label": "Modified"}],
        rows=[a.model_dump() for a in answers],
        on_row_click=ui.Call("__panel__thoughtspot_answer", {"answer_id": "{id}"}),
    ) if answers else ui.Text("No Answers here.", variant="caption")

    return ui.Tabs(tabs=[
        {"label": "Liveboards", "content": lb_table},
        {"label": "Answers", "content": ans_table},
    ])


@ext.panel("thoughtspot_liveboard", slot="center", title="Liveboard", icon="📊", center_overlay=True)
async def thoughtspot_liveboard_panel(ctx, liveboard_id: str = "", **kwargs) -> object:
    result = await h.get_liveboard(ctx, h.LiveboardScopedParams(liveboard_id=liveboard_id))
    if not (result.success and result.data):
        return ui.Text(f"Could not load liveboard: {result.error}", variant="caption")
    d = result.data
    return ui.Stack(direction="v", gap=3, children=[
        ui.Button("← Back", variant="ghost", size="sm", on_click=ui.Call("__panel__thoughtspot_tag", {"tag": ""})),
        ui.Text(d.name, variant="heading"),
        ui.KeyValue(items=[
            {"key": "Author", "value": d.author_name or "—"},
            {"key": "Created", "value": d.created or "—"},
            {"key": "Modified", "value": d.modified or "—"},
        ]),
        ui.Stack(direction="h", gap=2, children=[
            ui.Button("Export as PDF", variant="secondary", size="sm",
                      on_click=ui.Call("export_liveboard", {"liveboard_id": liveboard_id, "file_format": "PDF"})),
            ui.Button("Export as PNG", variant="secondary", size="sm",
                      on_click=ui.Call("export_liveboard", {"liveboard_id": liveboard_id, "file_format": "PNG"})),
            ui.Button("Export as CSV", variant="secondary", size="sm",
                      on_click=ui.Call("export_liveboard", {"liveboard_id": liveboard_id, "file_format": "CSV"})),
        ]),
    ])


@ext.panel("thoughtspot_answer", slot="center", title="Answer", icon="🔎", center_overlay=True)
async def thoughtspot_answer_panel(ctx, answer_id: str = "", **kwargs) -> object:
    result = await h.get_answer(ctx, h.AnswerScopedParams(answer_id=answer_id))
    if not (result.success and result.data):
        return ui.Text(f"Could not load answer: {result.error}", variant="caption")
    d = result.data
    return ui.Stack(direction="v", gap=3, children=[
        ui.Button("← Back", variant="ghost", size="sm", on_click=ui.Call("__panel__thoughtspot_tag", {"tag": ""})),
        ui.Text(d.name, variant="heading"),
        ui.KeyValue(items=[
            {"key": "Author", "value": d.author_name or "—"},
            {"key": "Modified", "value": d.modified or "—"},
        ]),
        ui.Button("Export as CSV", variant="secondary", size="sm",
                  on_click=ui.Call("export_answer", {"answer_id": answer_id, "file_format": "CSV"})),
    ])


@ext.panel("thoughtspot_worksheets", slot="center", title="Worksheets", icon="📐", center_overlay=True)
async def thoughtspot_worksheets_panel(ctx, **kwargs) -> object:
    result = await h.list_worksheets(ctx, h.ConnectionScopedParams())
    items = result.data.items if (result.success and result.data) else []
    if not items:
        return ui.Text("No Worksheets on this instance.", variant="caption")
    return ui.DataTable(
        columns=[{"key": "name", "label": "Name"}, {"key": "description", "label": "Description"}],
        rows=[w.model_dump() for w in items],
    )


@ext.panel("thoughtspot_search", slot="center", title="Search", icon="🔍", center_overlay=True)
async def thoughtspot_search_panel(ctx, **kwargs) -> object:
    ws_result = await h.list_worksheets(ctx, h.ConnectionScopedParams())
    worksheets = ws_result.data.items if (ws_result.success and ws_result.data) else []
    options = [{"label": w.name, "value": w.id} for w in worksheets]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("Ask a question", variant="heading"),
        ui.Form(
            action="search_data",
            submit_label="Search",
            children=[
                _field("Worksheet", ui.Select(param_name="worksheet_id", options=options, placeholder="Choose a Worksheet")),
                _field("Question", ui.Input(param_name="query", placeholder="e.g. total sales by region this year")),
            ],
        ),
    ])


@ext.panel("thoughtspot_users", slot="center", title="Users", icon="👥", center_overlay=True)
async def thoughtspot_users_panel(ctx, **kwargs) -> object:
    result = await h.list_users(ctx, h.ConnectionScopedParams())
    items = result.data.items if (result.success and result.data) else []
    if not items:
        return ui.Text("No users visible to these credentials.", variant="caption")
    return ui.DataTable(
        columns=[{"key": "display_name", "label": "Name"}, {"key": "name", "label": "Username"}, {"key": "email", "label": "Email"}],
        rows=[u.model_dump() for u in items],
    )


@ext.panel("thoughtspot_groups", slot="center", title="Groups", icon="👪", center_overlay=True)
async def thoughtspot_groups_panel(ctx, **kwargs) -> object:
    result = await h.list_groups(ctx, h.ConnectionScopedParams())
    items = result.data.items if (result.success and result.data) else []
    if not items:
        return ui.Text("No groups visible to these credentials.", variant="caption")
    return ui.DataTable(
        columns=[{"key": "display_name", "label": "Display name"}, {"key": "name", "label": "Name"}],
        rows=[g.model_dump() for g in items],
    )
