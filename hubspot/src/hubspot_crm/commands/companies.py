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
    domain: Optional[str] = typer.Option(None, help="Filter by domain (exact)."),
    name: Optional[str] = typer.Option(None, help="Search by name (partial match)."),
    industry: Optional[str] = typer.Option(None, help="Filter by industry (e.g. TECHNOLOGY, PHARMACEUTICALS)."),
    created_after: Optional[str] = typer.Option(None, "--created-after", help="Created after (YYYY-MM-DD)."),
    created_before: Optional[str] = typer.Option(None, "--created-before", help="Created before (YYYY-MM-DD)."),
    sort_by: str = typer.Option("createdate", "--sort-by", help="Property to sort by."),
    sort_dir: str = typer.Option("DESCENDING", "--sort-dir", help="ASCENDING or DESCENDING."),
    limit: int = typer.Option(10, help="Max results."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
) -> None:
    """Search companies with filtering and sorting."""
    from hubspot.crm.companies import PublicObjectSearchRequest, Filter, FilterGroup

    client = get_client()
    filters: list = []

    if domain:
        filters.append(Filter(property_name="domain", operator="EQ", value=domain))
    if name:
        filters.append(Filter(property_name="name", operator="CONTAINS_TOKEN", value=name))
    if industry:
        filters.append(Filter(property_name="industry", operator="EQ", value=industry))
    if created_after:
        filters.append(Filter(property_name="createdate", operator="GTE", value=_date_to_ms(created_after)))
    if created_before:
        filters.append(Filter(property_name="createdate", operator="LTE", value=_date_to_ms(created_before)))

    try:
        req = PublicObjectSearchRequest(
            filter_groups=[FilterGroup(filters=filters)] if filters else [],
            properties=["name", "domain", "industry", "phone", "city", "createdate"],
            sorts=[{"propertyName": sort_by, "direction": sort_dir.upper()}],
            limit=limit,
        )
        if after:
            req.after = after
        results = client.crm.companies.search_api.do_search(public_object_search_request=req)
        paging = None
        if results.paging and results.paging.next:
            paging = {"next": {"after": results.paging.next.after}}
        _output(ok({
            "results": [{"id": c.id, "properties": c.properties} for c in results.results],
            "total": results.total,
            "paging": paging,
        }))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


def _date_to_ms(date_str: str) -> str:
    from datetime import datetime, timezone
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return str(int(dt.timestamp() * 1000))
