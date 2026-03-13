"""HubSpot Line Items commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from hubspot.crm.line_items import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from hubspot.crm.line_items.exceptions import ApiException
from hubspot.crm.associations.v4 import AssociationSpec

from hubspot_crm.client import get_client, ok, err, handle_api_exception

app = typer.Typer(help="Manage HubSpot line items.")

# line_item -> deal association type
LINE_ITEM_TO_DEAL_TYPE_ID = 20


def _output(data: dict) -> None:
    print(json.dumps(data, indent=2))


@app.command()
def list(
    limit: int = typer.Option(20, help="Number of line items to return."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
    properties: Optional[str] = typer.Option(None, help="Comma-separated properties."),
) -> None:
    """List line items."""
    client = get_client()
    props = properties.split(",") if properties else ["name", "quantity", "price", "hs_product_id"]
    try:
        kwargs: dict = {"limit": limit, "properties": props}
        if after:
            kwargs["after"] = after
        page = client.crm.line_items.basic_api.get_page(**kwargs)
        results = [{"id": li.id, "properties": li.properties} for li in page.results]
        paging = None
        if page.paging and page.paging.next:
            paging = {"next": {"after": page.paging.next.after}}
        _output(ok({"results": results, "paging": paging}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def get(line_item_id: str = typer.Argument(..., help="Line item ID.")) -> None:
    """Get a line item by ID."""
    client = get_client()
    try:
        li = client.crm.line_items.basic_api.get_by_id(
            line_item_id=line_item_id,
            properties=["name", "quantity", "price", "hs_product_id", "amount", "discount"],
        )
        _output(ok({"id": li.id, "properties": li.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Line item name."),
    quantity: float = typer.Option(..., help="Quantity."),
    price: float = typer.Option(..., help="Unit price."),
    product_id: Optional[str] = typer.Option(None, "--product-id", help="HubSpot product ID to link."),
) -> None:
    """Create a new line item."""
    client = get_client()
    props: dict = {"name": name, "quantity": str(quantity), "price": str(price)}
    if product_id:
        props["hs_product_id"] = product_id
    try:
        li = client.crm.line_items.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            )
        )
        _output(ok({"id": li.id, "properties": li.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def update(
    line_item_id: str = typer.Argument(..., help="Line item ID."),
    name: Optional[str] = typer.Option(None, "--name", help="Line item name."),
    quantity: Optional[float] = typer.Option(None, help="Quantity."),
    price: Optional[float] = typer.Option(None, help="Unit price."),
) -> None:
    """Update a line item."""
    client = get_client()
    props: dict = {}
    if name:
        props["name"] = name
    if quantity is not None:
        props["quantity"] = str(quantity)
    if price is not None:
        props["price"] = str(price)
    if not props:
        _output(err("No properties provided to update."))
        raise typer.Exit(1)
    try:
        li = client.crm.line_items.basic_api.update(
            line_item_id=line_item_id,
            simple_public_object_input=SimplePublicObjectInput(properties=props),
        )
        _output(ok({"id": li.id, "properties": li.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def delete(line_item_id: str = typer.Argument(..., help="Line item ID.")) -> None:
    """Delete a line item."""
    client = get_client()
    try:
        client.crm.line_items.basic_api.archive(line_item_id=line_item_id)
        _output(ok({"id": line_item_id, "deleted": True}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def search(
    name: Optional[str] = typer.Option(None, help="Search by name (partial match)."),
    product_id: Optional[str] = typer.Option(None, "--product-id", help="Filter by HubSpot product ID."),
    min_price: Optional[float] = typer.Option(None, "--min-price", help="Minimum unit price."),
    max_price: Optional[float] = typer.Option(None, "--max-price", help="Maximum unit price."),
    sort_by: str = typer.Option("createdate", "--sort-by", help="Property to sort by."),
    sort_dir: str = typer.Option("DESCENDING", "--sort-dir", help="ASCENDING or DESCENDING."),
    limit: int = typer.Option(10, help="Max results."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
) -> None:
    """Search line items with filtering and sorting."""
    from hubspot.crm.line_items import PublicObjectSearchRequest, Filter, FilterGroup

    client = get_client()
    filters: list = []

    if name:
        filters.append(Filter(property_name="name", operator="CONTAINS_TOKEN", value=name))
    if product_id:
        filters.append(Filter(property_name="hs_product_id", operator="EQ", value=product_id))
    if min_price is not None:
        filters.append(Filter(property_name="price", operator="GTE", value=str(min_price)))
    if max_price is not None:
        filters.append(Filter(property_name="price", operator="LTE", value=str(max_price)))

    try:
        req = PublicObjectSearchRequest(
            filter_groups=[FilterGroup(filters=filters)] if filters else [],
            properties=["name", "quantity", "price", "hs_product_id", "createdate"],
            sorts=[{"propertyName": sort_by, "direction": sort_dir.upper()}],
            limit=limit,
        )
        if after:
            req.after = after
        results = client.crm.line_items.search_api.do_search(public_object_search_request=req)
        paging = None
        if results.paging and results.paging.next:
            paging = {"next": {"after": results.paging.next.after}}
        _output(ok({
            "results": [{"id": li.id, "properties": li.properties} for li in results.results],
            "total": results.total,
            "paging": paging,
        }))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def associate(
    line_item_id: str = typer.Argument(..., help="Line item ID."),
    deal_id: str = typer.Option(..., "--deal-id", help="Deal ID to associate with."),
) -> None:
    """Associate a line item with a deal."""
    client = get_client()
    try:
        client.crm.associations.v4.basic_api.create(
            object_type="line_items",
            object_id=line_item_id,
            to_object_type="deals",
            to_object_id=deal_id,
            association_spec=[
                AssociationSpec(
                    association_category="HUBSPOT_DEFINED",
                    association_type_id=LINE_ITEM_TO_DEAL_TYPE_ID,
                )
            ],
        )
        _output(ok({"line_item_id": line_item_id, "deal_id": deal_id}))
    except Exception as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)
