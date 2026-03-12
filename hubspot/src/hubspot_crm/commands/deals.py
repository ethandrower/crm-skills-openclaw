"""HubSpot Deals commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from hubspot.crm.deals import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from hubspot.crm.deals.exceptions import ApiException
from hubspot.crm.associations.v4 import AssociationSpec

from hubspot_crm.client import get_client, ok, err, handle_api_exception

app = typer.Typer(help="Manage HubSpot deals.")

ASSOCIATION_TYPE_IDS = {
    "contacts": 3,    # deal -> contact
    "companies": 5,   # deal -> company
    "line_items": 19, # deal -> line item
}


def _output(data: dict) -> None:
    print(json.dumps(data, indent=2))


@app.command()
def list(
    limit: int = typer.Option(20, help="Number of deals to return."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
    properties: Optional[str] = typer.Option(None, help="Comma-separated properties."),
) -> None:
    """List deals."""
    client = get_client()
    props = properties.split(",") if properties else ["dealname", "dealstage", "amount", "closedate", "pipeline"]
    try:
        kwargs: dict = {"limit": limit, "properties": props}
        if after:
            kwargs["after"] = after
        page = client.crm.deals.basic_api.get_page(**kwargs)
        results = [{"id": d.id, "properties": d.properties} for d in page.results]
        paging = None
        if page.paging and page.paging.next:
            paging = {"next": {"after": page.paging.next.after}}
        _output(ok({"results": results, "paging": paging}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def get(deal_id: str = typer.Argument(..., help="Deal ID.")) -> None:
    """Get a deal by ID."""
    client = get_client()
    try:
        deal = client.crm.deals.basic_api.get_by_id(
            deal_id=deal_id,
            properties=["dealname", "dealstage", "amount", "closedate", "pipeline", "hubspot_owner_id"],
        )
        _output(ok({"id": deal.id, "properties": deal.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Deal name."),
    stage: str = typer.Option(..., "--stage", help="Deal stage (e.g. appointmentscheduled)."),
    amount: Optional[float] = typer.Option(None, help="Deal amount."),
    closedate: Optional[str] = typer.Option(None, help="Close date (YYYY-MM-DD)."),
    pipeline: Optional[str] = typer.Option(None, help="Pipeline ID (default: 'default')."),
) -> None:
    """Create a new deal."""
    client = get_client()
    props: dict = {"dealname": name, "dealstage": stage}
    if amount is not None:
        props["amount"] = str(amount)
    if closedate:
        props["closedate"] = closedate
    if pipeline:
        props["pipeline"] = pipeline
    try:
        deal = client.crm.deals.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            )
        )
        _output(ok({"id": deal.id, "properties": deal.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def update(
    deal_id: str = typer.Argument(..., help="Deal ID."),
    name: Optional[str] = typer.Option(None, "--name", help="Deal name."),
    stage: Optional[str] = typer.Option(None, "--stage", help="Deal stage."),
    amount: Optional[float] = typer.Option(None, help="Deal amount."),
    closedate: Optional[str] = typer.Option(None, help="Close date (YYYY-MM-DD)."),
) -> None:
    """Update a deal."""
    client = get_client()
    props: dict = {}
    if name:
        props["dealname"] = name
    if stage:
        props["dealstage"] = stage
    if amount is not None:
        props["amount"] = str(amount)
    if closedate:
        props["closedate"] = closedate
    if not props:
        _output(err("No properties provided to update."))
        raise typer.Exit(1)
    try:
        deal = client.crm.deals.basic_api.update(
            deal_id=deal_id,
            simple_public_object_input=SimplePublicObjectInput(properties=props),
        )
        _output(ok({"id": deal.id, "properties": deal.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def delete(deal_id: str = typer.Argument(..., help="Deal ID.")) -> None:
    """Delete a deal."""
    client = get_client()
    try:
        client.crm.deals.basic_api.archive(deal_id=deal_id)
        _output(ok({"id": deal_id, "deleted": True}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def associate(
    deal_id: str = typer.Argument(..., help="Deal ID."),
    to: str = typer.Option(..., "--to", help="Object type: contacts, companies, or line_items."),
    object_id: str = typer.Option(..., "--id", help="ID of the object to associate."),
) -> None:
    """Associate a deal with a contact, company, or line item."""
    client = get_client()
    type_id = ASSOCIATION_TYPE_IDS.get(to)
    if type_id is None:
        _output(err(f"Unknown object type '{to}'. Choose from: {list(ASSOCIATION_TYPE_IDS.keys())}"))
        raise typer.Exit(1)
    try:
        client.crm.associations.v4.basic_api.create(
            object_type="deals",
            object_id=deal_id,
            to_object_type=to,
            to_object_id=object_id,
            association_spec=[
                AssociationSpec(association_category="HUBSPOT_DEFINED", association_type_id=type_id)
            ],
        )
        _output(ok({"deal_id": deal_id, "associated_to": to, "object_id": object_id}))
    except Exception as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def search(
    name: Optional[str] = typer.Option(None, help="Search by deal name."),
    stage: Optional[str] = typer.Option(None, help="Filter by deal stage."),
    limit: int = typer.Option(10, help="Max results."),
) -> None:
    """Search deals by name or stage."""
    from hubspot.crm.deals import PublicObjectSearchRequest, Filter, FilterGroup

    client = get_client()
    filters: list = []
    if name:
        filters.append(Filter(property_name="dealname", operator="CONTAINS_TOKEN", value=name))
    if stage:
        filters.append(Filter(property_name="dealstage", operator="EQ", value=stage))
    if not filters:
        _output(err("Provide at least --name or --stage."))
        raise typer.Exit(1)
    try:
        results = client.crm.deals.search_api.do_search(
            public_object_search_request=PublicObjectSearchRequest(
                filter_groups=[FilterGroup(filters=filters)],
                properties=["dealname", "dealstage", "amount", "closedate"],
                limit=limit,
            )
        )
        _output(ok({"results": [{"id": d.id, "properties": d.properties} for d in results.results]}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)
