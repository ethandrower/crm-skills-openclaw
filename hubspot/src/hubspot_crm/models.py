"""Pydantic models for HubSpot CRM objects."""

from __future__ import annotations

import sys
import os

# Allow importing shared types when running from monorepo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../"))

from shared.types.crm import (  # noqa: F401
    Contact,
    Deal,
    Company,
    Product,
    LineItem,
    Subscription,
)
