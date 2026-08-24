"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK. ThoughtSpot lives inside the user's own Cloud org or self-hosted
instance -- Imperal cannot and should not broker access centrally.

WHY BEARER TOKEN VIA LOGIN, NOT OAUTH. ThoughtSpot REST API v2 exchanges
username+password (or a service account secret_key) via POST
/auth/token/full for a Bearer token with an instance-configured TTL -- no
refresh token, so on expiry the client transparently re-logs-in with the
same credentials. Confirmed in CONNECTOR_DISCOVERY.md section 3. Same
transparent re-auth pattern as Google Looker Connector.

WHY ONE SECRET HOLDING A JSON ARRAY, SAME PRECEDENT AS Power BI/Tableau/
Qlik/Looker Connector. A user may have several instances connected, so
connections are stored as a JSON array of {id, label, instance_hostname,
username, password} objects under one declared secret. The live Bearer
token is cached separately per connection id in thoughtspot_client.py,
never persisted here.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "thoughtspot-connector",
    version="0.1.0",
    display_name="ThoughtSpot",
    description=(
        "Connect your own ThoughtSpot instance to manage Liveboards, "
        "Answers, Worksheets and run natural-language search queries "
        "from Imperal -- export reports, monitor content by tag, and "
        "get instance health at a glance. Nothing is hosted or proxied "
        "by Imperal beyond the request itself."
    ),
    icon="icon.svg",
    capabilities=["thoughtspot:read", "thoughtspot:write"],
)

chat = ChatExtension(ext)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one ThoughtSpot instance is connected."""
    raw = await ctx.secrets.get("thoughtspot_connections")
    import json
    connections = json.loads(raw) if raw else []
    return {
        "healthy": True,
        "connections": len(connections),
        "detail": f"{len(connections)} ThoughtSpot instance(s) connected." if connections else "No ThoughtSpot instance connected yet.",
    }
