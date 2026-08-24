"""Thin async HTTP client for the ThoughtSpot REST API v2.

Auth: POST /api/rest/2.0/auth/token/full with username+password, get back a
Bearer token. No refresh token -- transparent re-login on 401, same pattern
as Google Looker Connector.
"""
from __future__ import annotations

from typing import Any

import httpx


class ClientFail(Exception):
    def __init__(self, message: str, status: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.retryable = retryable


def _base(instance_hostname: str) -> str:
    host = instance_hostname.strip().rstrip("/")
    if host.startswith("http"):
        host = host.split("://", 1)[1]
    host = host.split(":")[0]
    return f"https://{host}"


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {}


async def login(instance_hostname: str, username: str, password: str) -> dict:
    """Exchange username/password for a Bearer token."""
    url = f"{_base(instance_hostname)}/api/rest/2.0/auth/token/full"
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(url, json={"username": username, "password": password, "validity_time_in_sec": 3600})
    if resp.status_code != 200:
        body = _safe_json(resp)
        detail = body.get("message", resp.text[:200]) if isinstance(body, dict) else resp.text[:200]
        raise ClientFail(f"Login failed: {detail}", status=resp.status_code, retryable=resp.status_code >= 500)
    data = _safe_json(resp)
    token = data.get("token") if isinstance(data, dict) else None
    if not token:
        raise ClientFail("Login succeeded but no token returned.", status=200)
    return {"token": token}


def _headers(conn: dict) -> dict:
    return {"Authorization": f"Bearer {conn['_token']}", "Accept": "application/json", "Content-Type": "application/json"}


async def _ensure_token(conn: dict) -> None:
    if not conn.get("_token"):
        result = await login(conn["instance_hostname"], conn["username"], conn["password"])
        conn["_token"] = result["token"]


async def _request(method: str, conn: dict, path: str, retry: bool = True, **kwargs) -> httpx.Response:
    await _ensure_token(conn)
    url = f"{_base(conn['instance_hostname'])}/api/rest/2.0{path}"
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.request(method, url, headers=_headers(conn), **kwargs)
    if resp.status_code == 401 and retry:
        conn["_token"] = None
        return await _request(method, conn, path, retry=False, **kwargs)
    return resp


def _raise_for_error(resp: httpx.Response, action: str) -> None:
    if resp.status_code >= 400:
        body = _safe_json(resp)
        detail = body.get("message", resp.text[:200]) if isinstance(body, dict) else resp.text[:200]
        raise ClientFail(f"{action} failed: {detail}", status=resp.status_code, retryable=resp.status_code >= 500 or resp.status_code == 429)


async def verify_connection(conn: dict) -> dict:
    """Validate credentials by logging in."""
    result = await login(conn["instance_hostname"], conn["username"], conn["password"])
    conn["_token"] = result["token"]
    return {}


async def list_liveboards(conn: dict, tag: str = "") -> list[dict]:
    body: dict[str, Any] = {"record_size": 200}
    if tag:
        body["tag_identifiers"] = [tag]
    resp = await _request("POST", conn, "/metadata/liveboard/search", json=body)
    _raise_for_error(resp, "List liveboards")
    data = _safe_json(resp)
    return data if isinstance(data, list) else []


async def get_liveboard(conn: dict, liveboard_id: str) -> dict:
    resp = await _request("POST", conn, "/metadata/liveboard/search", json={"liveboard_identifiers": [liveboard_id]})
    _raise_for_error(resp, "Get liveboard")
    data = _safe_json(resp)
    return data[0] if isinstance(data, list) and data else {}


async def export_liveboard(conn: dict, liveboard_id: str, file_format: str = "PDF") -> bytes:
    resp = await _request("POST", conn, "/report/liveboard", json={"metadata_identifier": liveboard_id, "file_format": file_format})
    _raise_for_error(resp, "Export liveboard")
    return resp.content


async def list_answers(conn: dict, tag: str = "") -> list[dict]:
    body: dict[str, Any] = {"record_size": 200}
    if tag:
        body["tag_identifiers"] = [tag]
    resp = await _request("POST", conn, "/metadata/answer/search", json=body)
    _raise_for_error(resp, "List answers")
    data = _safe_json(resp)
    return data if isinstance(data, list) else []


async def get_answer(conn: dict, answer_id: str) -> dict:
    resp = await _request("POST", conn, "/metadata/answer/search", json={"answer_identifiers": [answer_id]})
    _raise_for_error(resp, "Get answer")
    data = _safe_json(resp)
    return data[0] if isinstance(data, list) and data else {}


async def export_answer(conn: dict, answer_id: str, file_format: str = "CSV") -> bytes:
    resp = await _request("POST", conn, "/report/answer", json={"metadata_identifier": answer_id, "file_format": file_format})
    _raise_for_error(resp, "Export answer")
    return resp.content


async def list_worksheets(conn: dict) -> list[dict]:
    resp = await _request("POST", conn, "/metadata/worksheet/search", json={"record_size": 200})
    _raise_for_error(resp, "List worksheets")
    data = _safe_json(resp)
    return data if isinstance(data, list) else []


async def get_worksheet(conn: dict, worksheet_id: str) -> dict:
    resp = await _request("POST", conn, "/metadata/worksheet/search", json={"worksheet_identifiers": [worksheet_id]})
    _raise_for_error(resp, "Get worksheet")
    data = _safe_json(resp)
    return data[0] if isinstance(data, list) and data else {}


async def search_data(conn: dict, worksheet_id: str, query: str) -> dict:
    resp = await _request("POST", conn, "/searchdata", json={"query_string": query, "metadata_identifier": worksheet_id, "record_size": 100})
    _raise_for_error(resp, "Search data")
    return _safe_json(resp) if isinstance(_safe_json(resp), dict) else {}


async def list_tags(conn: dict) -> list[dict]:
    resp = await _request("POST", conn, "/tag/search", json={"record_size": 200})
    _raise_for_error(resp, "List tags")
    data = _safe_json(resp)
    return data if isinstance(data, list) else []


async def list_users(conn: dict) -> list[dict]:
    resp = await _request("POST", conn, "/user/search", json={"record_size": 200})
    _raise_for_error(resp, "List users")
    data = _safe_json(resp)
    return data if isinstance(data, list) else []


async def list_groups(conn: dict) -> list[dict]:
    resp = await _request("POST", conn, "/group/search", json={"record_size": 200})
    _raise_for_error(resp, "List groups")
    data = _safe_json(resp)
    return data if isinstance(data, list) else []
