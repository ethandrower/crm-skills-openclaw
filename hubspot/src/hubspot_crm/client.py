"""HubSpot API client wrapper with standardized error handling."""

from __future__ import annotations

import os
import sys
from typing import Any

import hubspot
from hubspot.crm.contacts import ApiException as ContactsApiException
from hubspot.crm.deals import ApiException as DealsApiException
from hubspot.crm.companies import ApiException as CompaniesApiException
from hubspot.crm.products import ApiException as ProductsApiException
from hubspot.crm.line_items import ApiException as LineItemsApiException


def get_client() -> hubspot.Client:
    """Return an authenticated HubSpot client, failing fast if token is missing."""
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")
    if not token:
        print(
            '{"ok": false, "error": "HUBSPOT_ACCESS_TOKEN environment variable is not set. '
            'Export your HubSpot Private App token: export HUBSPOT_ACCESS_TOKEN=<token>"}',
            file=sys.stderr,
        )
        raise SystemExit(1)
    return hubspot.Client.create(access_token=token)


def ok(data: Any) -> dict[str, Any]:
    """Wrap a successful result."""
    return {"ok": True, "data": data}


def err(message: str) -> dict[str, Any]:
    """Wrap an error result."""
    return {"ok": False, "error": message}


def handle_api_exception(e: Exception) -> dict[str, Any]:
    """Convert any hubspot ApiException to a standardized error dict."""
    body = getattr(e, "body", None)
    if body:
        try:
            import json
            parsed = json.loads(body)
            msg = parsed.get("message", str(e))
        except Exception:
            msg = str(body)
    else:
        msg = str(e)
    return err(msg)
