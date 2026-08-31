"""Chat tool handlers for ThoughtSpot Connector.

Connection storage follows the Power BI/Tableau/Qlik/Looker precedent: one
secret holding a JSON array of connection records. The live Bearer token is
cached separately in thoughtspot_client.py, never persisted here.
"""
from __future__ import annotations

import base64
import json
import uuid

from imperal_sdk import ActionResult

import thoughtspot_client as tc
from app import chat
from schemas import (
    NoParams, ConnectThoughtSpotParams, DisconnectThoughtSpotParams, ConnectionInfo, ListConnectionsResult,
    ConnectionScopedParams, TagItem, ListTagsResult,
    ListLiveboardsParams, LiveboardItem, ListLiveboardsResult, LiveboardScopedParams, LiveboardDetail,
    ExportLiveboardParams, ExportResult,
    ListAnswersParams, AnswerItem, ListAnswersResult, AnswerScopedParams, AnswerDetail, ExportAnswerParams,
    ListWorksheetsResult, WorksheetItem, WorksheetScopedParams, WorksheetDetail,
    SearchDataParams, SearchDataResult,
    ListUsersResult, ThoughtSpotUserItem, ListGroupsResult, ThoughtSpotGroupItem,
    AuditHealthParams, HealthAudit,
)

SECRET_NAME = "thoughtspot_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(SECRET_NAME)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(SECRET_NAME, json.dumps(connections))


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise ValueError("No ThoughtSpot instance connected yet. Run connect_thoughtspot first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise ValueError(f"Connection '{connection_id}' not found.")
    return connections[0]


@chat.function("connect_thoughtspot", "Connect a ThoughtSpot instance via username/password, after validating the credentials actually work (logs in).", action_type="write", chain_callable=True, data_model=ConnectionInfo, event="thoughtspot-connector.connected", effects=["create:connection"])
async def connect_thoughtspot(ctx, params: ConnectThoughtSpotParams) -> ActionResult:
    """Imperal action: connect_thoughtspot."""
    conn = {"id": str(uuid.uuid4()), "label": params.label, "instance_hostname": params.instance_hostname, "username": params.username, "password": params.password}
    try:
        await tc.verify_connection(conn)
    except tc.ClientFail as e:
        return ActionResult.error(str(e.message), code="THOUGHTSPOT_CONNECT_FAILED")
    connections = await _load_connections(ctx)
    connections.append({k: v for k, v in conn.items() if not k.startswith("_")})
    await _save_connections(ctx, connections)
    return ActionResult.success(data=ConnectionInfo(id=conn["id"], label=conn["label"], instance_hostname=conn["instance_hostname"]), summary="Thoughtspot connected.")


@chat.function("disconnect_thoughtspot", "Disconnect a ThoughtSpot instance: deletes only the saved credentials. Nothing in ThoughtSpot itself is changed.", action_type="write", chain_callable=True, data_model=NoParams, event="thoughtspot-connector.disconnected", effects=["delete:connection"])
async def disconnect_thoughtspot(ctx, params: DisconnectThoughtSpotParams) -> ActionResult:
    """Imperal action: disconnect_thoughtspot."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"Connection '{params.connection_id}' not found.", code="THOUGHTSPOT_CONNECTION_NOT_FOUND")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data=NoParams(), summary="Thoughtspot disconnected.")


@chat.function("list_connections", "List the connected ThoughtSpot instances.", action_type="read", chain_callable=True, data_model=ListConnectionsResult, event="thoughtspot-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """Imperal action: list_connections."""
    connections = await _load_connections(ctx)
    items = [ConnectionInfo(id=c["id"], label=c.get("label", ""), instance_hostname=c.get("instance_hostname", "")) for c in connections]
    return ActionResult.success(data=ListConnectionsResult(items=items), summary="Connections listed.")


@chat.function("list_tags", "List tags configured on the connected ThoughtSpot instance -- ThoughtSpot's flat content organization scheme (no folders).", action_type="read", chain_callable=True, data_model=ListTagsResult, event="thoughtspot-connector.list_tags")
async def list_tags(ctx, params: ConnectionScopedParams) -> ActionResult:
    """Imperal action: list_tags."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.list_tags(conn)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_LIST_TAGS_FAILED")
    items = [TagItem(id=t.get("id", ""), name=t.get("name", "")) for t in raw]
    return ActionResult.success(data=ListTagsResult(items=items), summary="Tags listed.")


@chat.function("list_liveboards", "List Liveboards on the connected ThoughtSpot instance, optionally filtered to one tag.", action_type="read", chain_callable=True, data_model=ListLiveboardsResult, event="thoughtspot-connector.list_liveboards")
async def list_liveboards(ctx, params: ListLiveboardsParams) -> ActionResult:
    """Imperal action: list_liveboards."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.list_liveboards(conn, params.tag)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_LIST_LIVEBOARDS_FAILED")
    items = [LiveboardItem(id=l.get("id", ""), name=l.get("name", ""), author_name=l.get("author_name", "") or "", modified=str(l.get("modified", "") or "")) for l in raw]
    return ActionResult.success(data=ListLiveboardsResult(items=items), summary="Liveboards listed.")


@chat.function("get_liveboard", "Read one Liveboard's metadata in full by id.", action_type="read", chain_callable=True, data_model=LiveboardDetail, event="thoughtspot-connector.get_liveboard")
async def get_liveboard(ctx, params: LiveboardScopedParams) -> ActionResult:
    """Imperal action: get_liveboard."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        l = await tc.get_liveboard(conn, params.liveboard_id)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_GET_LIVEBOARD_FAILED")
    return ActionResult.success(data=LiveboardDetail(
        id=l.get("id", ""), name=l.get("name", ""), description=l.get("description", "") or "",
        author_name=l.get("author_name", "") or "", created=str(l.get("created", "") or ""), modified=str(l.get("modified", "") or ""),
    ), summary="Liveboard retrieved.")


@chat.function("export_liveboard", "Export a Liveboard as PDF, PNG, or CSV.", action_type="read", chain_callable=True, data_model=ExportResult, event="thoughtspot-connector.export_liveboard")
async def export_liveboard(ctx, params: ExportLiveboardParams) -> ActionResult:
    """Imperal action: export_liveboard."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        content = await tc.export_liveboard(conn, params.liveboard_id, params.file_format)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_EXPORT_LIVEBOARD_FAILED")
    return ActionResult.success(data=ExportResult(file_format=params.file_format, content_base64=base64.b64encode(content).decode()), summary="Export liveboard done.")


@chat.function("list_answers", "List Answers on the connected ThoughtSpot instance, optionally filtered to one tag.", action_type="read", chain_callable=True, data_model=ListAnswersResult, event="thoughtspot-connector.list_answers")
async def list_answers(ctx, params: ListAnswersParams) -> ActionResult:
    """Imperal action: list_answers."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.list_answers(conn, params.tag)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_LIST_ANSWERS_FAILED")
    items = [AnswerItem(id=a.get("id", ""), name=a.get("name", ""), author_name=a.get("author_name", "") or "", modified=str(a.get("modified", "") or "")) for a in raw]
    return ActionResult.success(data=ListAnswersResult(items=items), summary="Answers listed.")


@chat.function("get_answer", "Read one Answer's metadata in full by id.", action_type="read", chain_callable=True, data_model=AnswerDetail, event="thoughtspot-connector.get_answer")
async def get_answer(ctx, params: AnswerScopedParams) -> ActionResult:
    """Imperal action: get_answer."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        a = await tc.get_answer(conn, params.answer_id)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_GET_ANSWER_FAILED")
    return ActionResult.success(data=AnswerDetail(
        id=a.get("id", ""), name=a.get("name", ""), description=a.get("description", "") or "",
        author_name=a.get("author_name", "") or "", modified=str(a.get("modified", "") or ""),
    ), summary="Answer retrieved.")


@chat.function("export_answer", "Export an Answer's result as CSV, PDF, or PNG.", action_type="read", chain_callable=True, data_model=ExportResult, event="thoughtspot-connector.export_answer")
async def export_answer(ctx, params: ExportAnswerParams) -> ActionResult:
    """Imperal action: export_answer."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        content = await tc.export_answer(conn, params.answer_id, params.file_format)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_EXPORT_ANSWER_FAILED")
    return ActionResult.success(data=ExportResult(file_format=params.file_format, content_base64=base64.b64encode(content).decode()), summary="Export answer done.")


@chat.function("list_worksheets", "List Worksheets (semantic models) on the connected ThoughtSpot instance.", action_type="read", chain_callable=True, data_model=ListWorksheetsResult, event="thoughtspot-connector.list_worksheets")
async def list_worksheets(ctx, params: ConnectionScopedParams) -> ActionResult:
    """Imperal action: list_worksheets."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.list_worksheets(conn)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_LIST_WORKSHEETS_FAILED")
    items = [WorksheetItem(id=w.get("id", ""), name=w.get("name", ""), description=w.get("description", "") or "") for w in raw]
    return ActionResult.success(data=ListWorksheetsResult(items=items), summary="Worksheets listed.")


@chat.function("get_worksheet", "Read one Worksheet's metadata in full by id.", action_type="read", chain_callable=True, data_model=WorksheetDetail, event="thoughtspot-connector.get_worksheet")
async def get_worksheet(ctx, params: WorksheetScopedParams) -> ActionResult:
    """Imperal action: get_worksheet."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        w = await tc.get_worksheet(conn, params.worksheet_id)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_GET_WORKSHEET_FAILED")
    return ActionResult.success(data=WorksheetDetail(id=w.get("id", ""), name=w.get("name", ""), description=w.get("description", "") or ""), summary="Worksheet retrieved.")


@chat.function("search_data", "Run a natural-language search query against a Worksheet -- ThoughtSpot's Search & AI-driven analytics core feature.", action_type="read", chain_callable=True, data_model=SearchDataResult, event="thoughtspot-connector.search_data")
async def search_data(ctx, params: SearchDataParams) -> ActionResult:
    """Imperal action: search_data."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.search_data(conn, params.worksheet_id, params.query)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_SEARCH_DATA_FAILED")
    columns = [c.get("name", "") for c in (raw.get("column_names") or raw.get("columns") or [])] if isinstance(raw.get("column_names") or raw.get("columns"), list) and raw.get("column_names") and isinstance(raw.get("column_names", [{}])[0], dict) else (raw.get("column_names") or [])
    rows = raw.get("data") or raw.get("rows") or []
    return ActionResult.success(data=SearchDataResult(columns=columns if isinstance(columns, list) else [], rows=rows if isinstance(rows, list) else [], row_count=len(rows) if isinstance(rows, list) else 0), summary="Search data done.")


@chat.function("list_users", "List users on the connected ThoughtSpot instance.", action_type="read", chain_callable=True, data_model=ListUsersResult, event="thoughtspot-connector.list_users")
async def list_users(ctx, params: ConnectionScopedParams) -> ActionResult:
    """Imperal action: list_users."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.list_users(conn)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_LIST_USERS_FAILED")
    items = [ThoughtSpotUserItem(id=u.get("id", ""), name=u.get("name", ""), display_name=u.get("display_name", "") or "", email=u.get("email", "") or "") for u in raw]
    return ActionResult.success(data=ListUsersResult(items=items), summary="Users listed.")


@chat.function("list_groups", "List groups on the connected ThoughtSpot instance.", action_type="read", chain_callable=True, data_model=ListGroupsResult, event="thoughtspot-connector.list_groups")
async def list_groups(ctx, params: ConnectionScopedParams) -> ActionResult:
    """Imperal action: list_groups."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        raw = await tc.list_groups(conn)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_LIST_GROUPS_FAILED")
    items = [ThoughtSpotGroupItem(id=g.get("id", ""), name=g.get("name", ""), display_name=g.get("display_name", "") or "") for g in raw]
    return ActionResult.success(data=ListGroupsResult(items=items), summary="Groups listed.")


@chat.function("audit_instance_health", "Build one aggregated health report across the connected ThoughtSpot instance: Liveboard/Answer/Worksheet/user/tag counts.", action_type="read", chain_callable=True, data_model=HealthAudit, event="thoughtspot-connector.audit_instance_health")
async def audit_instance_health(ctx, params: AuditHealthParams) -> ActionResult:
    """Imperal action: audit_instance_health."""
    try:
        conn = await _resolve_connection(ctx, params.connection_id)
        liveboards = await tc.list_liveboards(conn)
        answers = await tc.list_answers(conn)
        worksheets = await tc.list_worksheets(conn)
        users = await tc.list_users(conn)
        tags = await tc.list_tags(conn)
    except (tc.ClientFail, ValueError) as e:
        return ActionResult.error(str(getattr(e, "message", e)), code="THOUGHTSPOT_AUDIT_FAILED")
    return ActionResult.success(data=HealthAudit(
        liveboard_count=len(liveboards), answer_count=len(answers), worksheet_count=len(worksheets),
        user_count=len(users), tag_count=len(tags),
    ), summary="Instance health audit ready.")
