"""Pydantic parameter/result schemas for ThoughtSpot Connector tools."""
from __future__ import annotations

from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


# ---- Connection management ----

class ConnectThoughtSpotParams(BaseModel):
    instance_hostname: str = Field(..., description="ThoughtSpot instance hostname, e.g. myorg.thoughtspot.cloud")
    username: str = Field(..., description="ThoughtSpot username (or service account username).")
    password: str = Field(..., description="ThoughtSpot password (or service account secret).")
    label: str = Field("", description="Optional friendly label, e.g. 'Production instance'.")


class DisconnectThoughtSpotParams(BaseModel):
    connection_id: str = Field(..., description="Connection id from list_connections.")


class ConnectionInfo(BaseModel):
    id: str
    label: str
    instance_hostname: str


class ListConnectionsResult(BaseModel):
    items: list[ConnectionInfo] = Field(default_factory=list)


class ConnectionScopedParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")


# ---- Tags ----

class TagItem(BaseModel):
    id: str
    name: str


class ListTagsResult(BaseModel):
    items: list[TagItem] = Field(default_factory=list)


# ---- Liveboards ----

class ListLiveboardsParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    tag: str = Field("", description="Filter to one tag id; omit for all Liveboards visible to the credentials.")


class LiveboardItem(BaseModel):
    id: str
    name: str
    author_name: str = ""
    modified: str = ""


class ListLiveboardsResult(BaseModel):
    items: list[LiveboardItem] = Field(default_factory=list)


class LiveboardScopedParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    liveboard_id: str = Field(..., description="Liveboard id from list_liveboards.")


class LiveboardDetail(BaseModel):
    id: str
    name: str
    description: str = ""
    author_name: str = ""
    created: str = ""
    modified: str = ""


class ExportLiveboardParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    liveboard_id: str = Field(..., description="Liveboard id from list_liveboards.")
    file_format: str = Field("PDF", description="PDF, PNG, or CSV.")


class ExportResult(BaseModel):
    file_format: str
    content_base64: str


# ---- Answers ----

class ListAnswersParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    tag: str = Field("", description="Filter to one tag id; omit for all Answers visible to the credentials.")


class AnswerItem(BaseModel):
    id: str
    name: str
    author_name: str = ""
    modified: str = ""


class ListAnswersResult(BaseModel):
    items: list[AnswerItem] = Field(default_factory=list)


class AnswerScopedParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    answer_id: str = Field(..., description="Answer id from list_answers.")


class AnswerDetail(BaseModel):
    id: str
    name: str
    description: str = ""
    author_name: str = ""
    modified: str = ""


class ExportAnswerParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    answer_id: str = Field(..., description="Answer id from list_answers.")
    file_format: str = Field("CSV", description="CSV, PDF, or PNG.")


# ---- Worksheets ----

class ListWorksheetsResult(BaseModel):
    items: list["WorksheetItem"] = Field(default_factory=list)


class WorksheetItem(BaseModel):
    id: str
    name: str
    description: str = ""


class WorksheetScopedParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    worksheet_id: str = Field(..., description="Worksheet id from list_worksheets.")


class WorksheetDetail(BaseModel):
    id: str
    name: str
    description: str = ""


# ---- Search ----

class SearchDataParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")
    worksheet_id: str = Field(..., description="Worksheet id to run the natural-language query against.")
    query: str = Field(..., description="Natural-language search query, e.g. 'total sales by region this year'.")


class SearchDataResult(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict] = Field(default_factory=list)
    row_count: int = 0


# ---- Users / Groups ----

class ListUsersResult(BaseModel):
    items: list["ThoughtSpotUserItem"] = Field(default_factory=list)


class ThoughtSpotUserItem(BaseModel):
    id: str
    name: str
    display_name: str = ""
    email: str = ""


class ListGroupsResult(BaseModel):
    items: list["ThoughtSpotGroupItem"] = Field(default_factory=list)


class ThoughtSpotGroupItem(BaseModel):
    id: str
    name: str
    display_name: str = ""


# ---- Health audit ----

class AuditHealthParams(BaseModel):
    connection_id: str = Field("", description="Connection id; omit to use the first connected instance.")


class HealthAudit(BaseModel):
    liveboard_count: int = 0
    answer_count: int = 0
    worksheet_count: int = 0
    user_count: int = 0
    tag_count: int = 0
