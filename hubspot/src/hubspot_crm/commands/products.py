"""HubSpot Products commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from hubspot.crm.products import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from hubspot.crm.products.exceptions import ApiException

from hubspot_crm.client import get_client, ok, err, handle_api_exception

app = typer.Typer(help="Manage HubSpot products.")


def _output(data: dict) -> None:
    print(json.dumps(data, indent=2))


@app.command()
def list(
    limit: int = typer.Option(20, help="Number of products to return."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
    properties: Optional[str] = typer.Option(None, help="Comma-separated properties."),
) -> None:
    """List products."""
    client = get_client()
    props = properties.split(",") if properties else ["name", "price", "description", "hs_sku"]
    try:
        kwargs: dict = {"limit": limit, "properties": props}
        if after:
            kwargs["after"] = after
        page = client.crm.products.basic_api.get_page(**kwargs)
        results = [{"id": p.id, "properties": p.properties} for p in page.results]
        paging = None
        if page.paging and page.paging.next:
            paging = {"next": {"after": page.paging.next.after}}
        _output(ok({"results": results, "paging": paging}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def get(product_id: str = typer.Argument(..., help="Product ID.")) -> None:
    """Get a product by ID."""
    client = get_client()
    try:
        product = client.crm.products.basic_api.get_by_id(
            product_id=product_id,
            properties=["name", "price", "description", "hs_sku", "recurringbillingfrequency"],
        )
        _output(ok({"id": product.id, "properties": product.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Product name."),
    price: Optional[float] = typer.Option(None, help="Unit price."),
    description: Optional[str] = typer.Option(None, help="Product description."),
    sku: Optional[str] = typer.Option(None, "--sku", help="Product SKU."),
) -> None:
    """Create a new product."""
    client = get_client()
    props: dict = {"name": name}
    if price is not None:
        props["price"] = str(price)
    if description:
        props["description"] = description
    if sku:
        props["hs_sku"] = sku
    try:
        product = client.crm.products.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            )
        )
        _output(ok({"id": product.id, "properties": product.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def update(
    product_id: str = typer.Argument(..., help="Product ID."),
    name: Optional[str] = typer.Option(None, "--name", help="Product name."),
    price: Optional[float] = typer.Option(None, help="Unit price."),
    description: Optional[str] = typer.Option(None, help="Product description."),
    sku: Optional[str] = typer.Option(None, "--sku", help="Product SKU."),
) -> None:
    """Update a product."""
    client = get_client()
    props: dict = {}
    if name:
        props["name"] = name
    if price is not None:
        props["price"] = str(price)
    if description:
        props["description"] = description
    if sku:
        props["hs_sku"] = sku
    if not props:
        _output(err("No properties provided to update."))
        raise typer.Exit(1)
    try:
        product = client.crm.products.basic_api.update(
            product_id=product_id,
            simple_public_object_input=SimplePublicObjectInput(properties=props),
        )
        _output(ok({"id": product.id, "properties": product.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def delete(product_id: str = typer.Argument(..., help="Product ID.")) -> None:
    """Delete a product."""
    client = get_client()
    try:
        client.crm.products.basic_api.archive(product_id=product_id)
        _output(ok({"id": product_id, "deleted": True}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)
