"""HubSpot Subscriptions commands.

HubSpot does not have a dedicated "Subscriptions" CRM object in the standard API.
This module manages subscription-like data using HubSpot's custom objects or
the Billing/Commerce subscription endpoints if available. For accounts without
Commerce Hub, it falls back to a note on the limitation.

The implementation targets the HubSpot Subscriptions API (Commerce Hub):
  GET  /crm/v3/objects/subscriptions
  POST /crm/v3/objects/subscriptions
  etc.
"""

from __future__ import annotations

import json
from typing import Optional

import typer

from hubspot_crm.client import get_client, ok, err, handle_api_exception

app = typer.Typer(help="Manage HubSpot subscriptions (Commerce Hub).")

OBJECT_TYPE = "subscriptions"
DEFAULT_PROPERTIES = ["hs_subscription_name", "hs_mrr", "hs_status", "hs_start_date", "hs_end_date"]


def _output(data: dict) -> None:
    print(json.dumps(data, indent=2))


def _generic_get_page(client, limit: int, after: Optional[str], props: list[str]) -> dict:
    """Generic list using the CRM objects API."""
    from hubspot.crm.objects import ApiException
    try:
        kwargs: dict = {"limit": limit, "properties": props, "object_type": OBJECT_TYPE}
        if after:
            kwargs["after"] = after
        page = client.crm.objects.basic_api.get_page(**kwargs)
        results = [{"id": s.id, "properties": s.properties} for s in page.results]
        paging = None
        if page.paging and page.paging.next:
            paging = {"next": {"after": page.paging.next.after}}
        return ok({"results": results, "paging": paging})
    except ApiException as e:
        return handle_api_exception(e)


@app.command()
def list(
    limit: int = typer.Option(20, help="Number of subscriptions to return."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
    properties: Optional[str] = typer.Option(None, help="Comma-separated properties."),
) -> None:
    """List subscriptions."""
    client = get_client()
    props = properties.split(",") if properties else DEFAULT_PROPERTIES
    result = _generic_get_page(client, limit, after, props)
    _output(result)
    if not result.get("ok"):
        raise typer.Exit(1)


@app.command()
def get(subscription_id: str = typer.Argument(..., help="Subscription ID.")) -> None:
    """Get a subscription by ID."""
    from hubspot.crm.objects import ApiException
    client = get_client()
    try:
        sub = client.crm.objects.basic_api.get_by_id(
            object_type=OBJECT_TYPE,
            object_id=subscription_id,
            properties=DEFAULT_PROPERTIES,
        )
        _output(ok({"id": sub.id, "properties": sub.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Subscription name."),
    mrr: Optional[float] = typer.Option(None, "--mrr", help="Monthly recurring revenue."),
    status: Optional[str] = typer.Option(None, "--status", help="Subscription status."),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)."),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)."),
) -> None:
    """Create a new subscription."""
    from hubspot.crm.objects import ApiException, SimplePublicObjectInputForCreate
    client = get_client()
    props: dict = {"hs_subscription_name": name}
    if mrr is not None:
        props["hs_mrr"] = str(mrr)
    if status:
        props["hs_status"] = status
    if start_date:
        props["hs_start_date"] = start_date
    if end_date:
        props["hs_end_date"] = end_date
    try:
        sub = client.crm.objects.basic_api.create(
            object_type=OBJECT_TYPE,
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            ),
        )
        _output(ok({"id": sub.id, "properties": sub.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def update(
    subscription_id: str = typer.Argument(..., help="Subscription ID."),
    name: Optional[str] = typer.Option(None, "--name", help="Subscription name."),
    mrr: Optional[float] = typer.Option(None, "--mrr", help="Monthly recurring revenue."),
    status: Optional[str] = typer.Option(None, "--status", help="Subscription status."),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)."),
) -> None:
    """Update a subscription."""
    from hubspot.crm.objects import ApiException, SimplePublicObjectInput
    client = get_client()
    props: dict = {}
    if name:
        props["hs_subscription_name"] = name
    if mrr is not None:
        props["hs_mrr"] = str(mrr)
    if status:
        props["hs_status"] = status
    if end_date:
        props["hs_end_date"] = end_date
    if not props:
        _output(err("No properties provided to update."))
        raise typer.Exit(1)
    try:
        sub = client.crm.objects.basic_api.update(
            object_type=OBJECT_TYPE,
            object_id=subscription_id,
            simple_public_object_input=SimplePublicObjectInput(properties=props),
        )
        _output(ok({"id": sub.id, "properties": sub.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def delete(subscription_id: str = typer.Argument(..., help="Subscription ID.")) -> None:
    """Delete a subscription."""
    from hubspot.crm.objects import ApiException
    client = get_client()
    try:
        client.crm.objects.basic_api.archive(
            object_type=OBJECT_TYPE,
            object_id=subscription_id,
        )
        _output(ok({"id": subscription_id, "deleted": True}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)
