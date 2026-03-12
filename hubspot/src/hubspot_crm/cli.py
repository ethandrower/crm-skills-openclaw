"""HubSpot CRM CLI — OpenClaw skill entry point."""

from __future__ import annotations

import typer

from hubspot_crm.commands import contacts, deals, companies, products, line_items, subscriptions

app = typer.Typer(
    name="hubspot-crm",
    help=(
        "Manage HubSpot CRM objects (contacts, deals, companies, products, "
        "line items, subscriptions). All output is JSON for agent compatibility."
    ),
    no_args_is_help=True,
)

app.add_typer(contacts.app, name="contacts")
app.add_typer(deals.app, name="deals")
app.add_typer(companies.app, name="companies")
app.add_typer(products.app, name="products")
app.add_typer(line_items.app, name="line-items")
app.add_typer(subscriptions.app, name="subscriptions")


if __name__ == "__main__":
    app()
