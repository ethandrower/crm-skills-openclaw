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
    email: Optional[str] = typer.Option(None, help="Search by email."),
    name: Optional[str] = typer.Option(None, help="Search by first or last name."),
    limit: int = typer.Option(10, help="Max results."),
) -> None:
    """Search contacts by email or name."""
    from hubspot.crm.contacts import PublicObjectSearchRequest, Filter, FilterGroup

    client = get_client()
    filters: list = []
    if email:
        filters.append(Filter(property_name="email", operator="EQ", value=email))
    if name:
        filters.append(Filter(property_name="firstname", operator="CONTAINS_TOKEN", value=name))
    if not filters:
        _output(err("Provide at least --email or --name."))
        raise typer.Exit(1)
    try:
        results = client.crm.contacts.search_api.do_search(
            public_object_search_request=PublicObjectSearchRequest(
                filter_groups=[FilterGroup(filters=filters)],
                properties=["email", "firstname", "lastname", "phone", "company"],
                limit=limit,
            )
        )
        _output(ok({"results": [{"id": c.id, "properties": c.properties} for c in results.results]}))
    except ApiException as e:
        _output(handle_api_exception(e))
        raise typer.Exit(1)
