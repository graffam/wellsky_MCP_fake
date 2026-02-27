from __future__ import annotations

import contextlib
import os
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

from mcp_tools import outreach, census


def _env_csv(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings:
    if os.getenv("MCP_DISABLE_DNS_REBINDING_PROTECTION", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    # Vercel runs behind a proxy and may present varying Host headers.
    # To avoid "Invalid Host header" on Vercel deployments, disable DNS
    # rebinding protection automatically when running on Vercel unless
    # explicitly overridden via MCP_DISABLE_DNS_REBINDING_PROTECTION.
    if os.getenv("VERCEL") or os.getenv("VERCEL_URL"):
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    allowed_hosts = _env_csv("MCP_ALLOWED_HOSTS")
    allowed_origins = _env_csv("MCP_ALLOWED_ORIGINS")

    if not allowed_hosts:
        allowed_hosts = [
            "localhost",
            "localhost:*",
            "127.0.0.1",
            "127.0.0.1:*",
        ]
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            allowed_hosts.append(vercel_url)
        allowed_hosts.extend(
            [
                "*.vercel.app",
                "*.vercel.app:*",
            ]
        )

    if not allowed_origins:
        allowed_origins = [
            "http://localhost",
            "http://localhost:*",
            "http://127.0.0.1",
            "http://127.0.0.1:*",
        ]
        vercel_url = os.getenv("VERCEL_URL")
        if vercel_url:
            allowed_origins.extend(
                [
                    f"https://{vercel_url}",
                    f"http://{vercel_url}",
                ]
            )
        allowed_origins.extend(
            [
                "https://*.vercel.app",
                "http://*.vercel.app",
            ]
        )

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


mcp = FastMCP(
    name="wellsky-outreach-mcp",
    instructions=(
        "WellSky patient outreach workflow interface. Use the reach_out_to_patients tool to register outreach jobs and retrieve a summary report."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    transport_security=_transport_security_settings(),
)

outreach.register(mcp)
census.register(mcp)

_http_app = mcp.streamable_http_app()


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with mcp.session_manager.run():
        yield


asgi_app = Starlette(
    routes=[
        Mount("/mcp", app=_http_app),
    ],
    lifespan=lifespan,
)


class RootMCPCompatMiddleware:
    """Allow clients configured for / to reach the /mcp mount."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive, send):
        if scope.get("type") == "http" and scope.get("path") in {"/", "/mcp"}:
            rewritten = dict(scope)
            rewritten["path"] = "/mcp/"
            rewritten["raw_path"] = b"/mcp/"
            await self.app(rewritten, receive, send)
            return
        await self.app(scope, receive, send)


app = RootMCPCompatMiddleware(asgi_app)
app = CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Mcp-Session-Id"],
    expose_headers=["Mcp-Session-Id"],
)
