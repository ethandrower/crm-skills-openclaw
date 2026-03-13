"""HubSpot Contacts commands."""

from __future__ import annotations

import json
from typing import Optional

import typer
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from hubspot.crm.contacts.exceptions import ApiException

from hubspot_crm.client import get_client, ok, err, handle_api_exception

app = typer.Typer(help="Manage HubSpot contacts.")


def _output(data: dict) -> None:
    print(json.dumps(data, indent=2))


@app.command()
def list(
    limit: int = typer.Option(20, help="Number of contacts to return."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
    properties: Optional[str] = typer.Option(
        None, help="Comma-separated property names to include."
    ),
) -> None:
    """List contacts."""
    client = get_client()
    props = properties.split(",") if properties else ["email", "firstname", "lastname", "phone", "company"]
    try:
        kwargs: dict = {"limit": limit, "properties": props}
        if after:
            kwargs["after"] = after
        page = client.crm.contacts.basic_api.get_page(**kwargs)
        results = [{"id": c.id, "properties": c.properties} for c in page.results]
        paging = None
        if page.paging and page.paging.next:
            paging = {"next": {"after": page.paging.next.after}}
        _output(ok({"results": results, "paging": paging}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def get(contact_id: str = typer.Argument(..., help="Contact ID.")) -> None:
    """Get a contact by ID."""
    client = get_client()
    try:
        contact = client.crm.contacts.basic_api.get_by_id(
            contact_id=contact_id,
            properties=["email", "firstname", "lastname", "phone", "company", "hs_lead_status"],
        )
        _output(ok({"id": contact.id, "properties": contact.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def create(
    email: str = typer.Option(..., help="Contact email address."),
    firstname: Optional[str] = typer.Option(None, help="First name."),
    lastname: Optional[str] = typer.Option(None, help="Last name."),
    phone: Optional[str] = typer.Option(None, help="Phone number."),
    company: Optional[str] = typer.Option(None, help="Company name."),
) -> None:
    """Create a new contact."""
    client = get_client()
    props: dict = {"email": email}
    if firstname:
        props["firstname"] = firstname
    if lastname:
        props["lastname"] = lastname
    if phone:
        props["phone"] = phone
    if company:
        props["company"] = company
    try:
        contact = client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=props
            )
        )
        _output(ok({"id": contact.id, "properties": contact.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def update(
    contact_id: str = typer.Argument(..., help="Contact ID."),
    email: Optional[str] = typer.Option(None, help="Email address."),
    firstname: Optional[str] = typer.Option(None, help="First name."),
    lastname: Optional[str] = typer.Option(None, help="Last name."),
    phone: Optional[str] = typer.Option(None, help="Phone number."),
    company: Optional[str] = typer.Option(None, help="Company name."),
) -> None:
    """Update a contact."""
    client = get_client()
    props: dict = {}
    if email:
        props["email"] = email
    if firstname:
        props["firstname"] = firstname
    if lastname:
        props["lastname"] = lastname
    if phone:
        props["phone"] = phone
    if company:
        props["company"] = company
    if not props:
        _output(err("No properties provided to update."))
        raise typer.Exit(1)
    try:
        contact = client.crm.contacts.basic_api.update(
            contact_id=contact_id,
            simple_public_object_input=SimplePublicObjectInput(properties=props),
        )
        _output(ok({"id": contact.id, "properties": contact.properties}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def delete(contact_id: str = typer.Argument(..., help="Contact ID.")) -> None:
    """Delete a contact."""
    client = get_client()
    try:
        client.crm.contacts.basic_api.archive(contact_id=contact_id)
        _output(ok({"id": contact_id, "deleted": True}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)


@app.command()
def search(
    email: Optional[str] = typer.Option(None, help="Filter by email (exact)."),
    name: Optional[str] = typer.Option(None, help="Search by first name (partial match)."),
    lifecycle_stage: Optional[str] = typer.Option(
        None, "--lifecycle-stage",
        help="Filter by lifecycle stage: lead, marketingqualifiedlead, opportunity, customer, evangelist."
    ),
    has_phone: bool = typer.Option(False, "--has-phone", help="Only contacts with a phone number."),
    created_after: Optional[str] = typer.Option(None, "--created-after", help="Created after date (YYYY-MM-DD)."),
    created_before: Optional[str] = typer.Option(None, "--created-before", help="Created before date (YYYY-MM-DD)."),
    sort_by: str = typer.Option("createdate", "--sort-by", help="Property to sort by."),
    sort_dir: str = typer.Option("DESCENDING", "--sort-dir", help="ASCENDING or DESCENDING."),
    limit: int = typer.Option(10, help="Max results."),
    after: Optional[str] = typer.Option(None, help="Pagination cursor."),
) -> None:
    """Search contacts with filtering and sorting."""
    from hubspot.crm.contacts import PublicObjectSearchRequest, Filter, FilterGroup

    client = get_client()
    filters: list = []

    if email:
        filters.append(Filter(property_name="email", operator="EQ", value=email))
    if name:
        filters.append(Filter(property_name="firstname", operator="CONTAINS_TOKEN", value=name))
    if lifecycle_stage:
        filters.append(Filter(property_name="lifecyclestage", operator="EQ", value=lifecycle_stage))
    if has_phone:
        filters.append(Filter(property_name="phone", operator="HAS_PROPERTY"))
    if created_after:
        filters.append(Filter(property_name="createdate", operator="GTE", value=_date_to_ms(created_after)))
    if created_before:
        filters.append(Filter(property_name="createdate", operator="LTE", value=_date_to_ms(created_before)))

    try:
        req = PublicObjectSearchRequest(
            filter_groups=[FilterGroup(filters=filters)] if filters else [],
            properties=["email", "firstname", "lastname", "phone", "company", "lifecyclestage", "createdate"],
            sorts=[{"propertyName": sort_by, "direction": sort_dir.upper()}],
            limit=limit,
        )
        if after:
            req.after = after
        results = client.crm.contacts.search_api.do_search(public_object_search_request=req)
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
    """Convert YYYY-MM-DD to millisecond timestamp string for HubSpot date filters."""
    from datetime import datetime, timezone
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return str(int(dt.timestamp() * 1000))
