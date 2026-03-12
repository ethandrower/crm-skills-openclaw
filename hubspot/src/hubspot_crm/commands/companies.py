"""HubSpot Companies commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from hubspot.crm.companies import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from hubspot.crm.companies.exceptions import ApiException

from hubspot_crm.client import get_client, ok, err, handle_api_exception

app = typer.Typer(help="Manage HubSpot companies.")


def _output(data: dict) -> None:
    print(json.dumps(data, indent=2))


@app.command()
def list(
    limit: int = typer.Option(20, help="Number of companies to return."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
    properties: Optional[str] = typer.Option(None, help="Comma-separated properties."),
) -> None:
    """List companies."""
    client = get_client()
    props = properties.split(",") if properties else ["name", "domain", "industry", "phone", "city"]
    try:
        kwargs: dict = {"limit": limit, "properties": props}
        if after:
            kwargs["after"] = after
        page = client.crm.companies.basic_api.get_page(**kwargs)
        results = [{"id": c.id, "properties": c.properties} for c in page.results]
        paging = None
        if page.paging and page.paging.next:
            paging = {"next": {"after": page.paging.next.after}}
        _output(ok({"results": results, "paging": paging}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def get(company_id: str = typer.Argument(..., help="Company ID.")) -> None:
    """Get a company by ID."""
    client = get_client()
    try:
        company = client.crm.companies.basic_api.get_by_id(
            company_id=company_id,
            properties=["name", "domain", "industry", "phone", "city", "country", "numberofemployees"],
        )
        _output(ok({"id": company.id, "properties": company.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Option(..., "--name", help="Company name."),
    domain: Optional[str] = typer.Option(None, help="Company domain."),
    industry: Optional[str] = typer.Option(None, help="Industry."),
    phone: Optional[str] = typer.Option(None, help="Phone number."),
) -> None:
    """Create a new company."""
    client = get_client()
    props: dict = {"name": name}
    if domain:
        props["domain"] = domain
    if industry:
        props["industry"] = industry
    if phone:
        props["phone"] = phone
    try:
        company = client.crm.companies.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            )
        )
        _output(ok({"id": company.id, "properties": company.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def update(
    company_id: str = typer.Argument(..., help="Company ID."),
    name: Optional[str] = typer.Option(None, "--name", help="Company name."),
    domain: Optional[str] = typer.Option(None, help="Domain."),
    industry: Optional[str] = typer.Option(None, help="Industry."),
    phone: Optional[str] = typer.Option(None, help="Phone number."),
) -> None:
    """Update a company."""
    client = get_client()
    props: dict = {}
    if name:
        props["name"] = name
    if domain:
        props["domain"] = domain
    if industry:
        props["industry"] = industry
    if phone:
        props["phone"] = phone
    if not props:
        _output(err("No properties provided to update."))
        raise typer.Exit(1)
    try:
        company = client.crm.companies.basic_api.update(
            company_id=company_id,
            simple_public_object_input=SimplePublicObjectInput(properties=props),
        )
        _output(ok({"id": company.id, "properties": company.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def delete(company_id: str = typer.Argument(..., help="Company ID.")) -> None:
    """Delete a company."""
    client = get_client()
    try:
        client.crm.companies.basic_api.archive(company_id=company_id)
        _output(ok({"id": company_id, "deleted": True}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def search(
    domain: Optional[str] = typer.Option(None, help="Search by domain."),
    name: Optional[str] = typer.Option(None, help="Search by name."),
    limit: int = typer.Option(10, help="Max results."),
) -> None:
    """Search companies by domain or name."""
    from hubspot.crm.companies import PublicObjectSearchRequest, Filter, FilterGroup

    client = get_client()
    filters: list = []
    if domain:
        filters.append(Filter(property_name="domain", operator="EQ", value=domain))
    if name:
        filters.append(Filter(property_name="name", operator="CONTAINS_TOKEN", value=name))
    if not filters:
        _output(err("Provide at least --domain or --name."))
        raise typer.Exit(1)
    try:
        results = client.crm.companies.search_api.do_search(
            public_object_search_request=PublicObjectSearchRequest(
                filter_groups=[FilterGroup(filters=filters)],
                properties=["name", "domain", "industry", "phone"],
                limit=limit,
            )
        )
        _output(ok({"results": [{"id": c.id, "properties": c.properties} for c in results.results]}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)
