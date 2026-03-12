"""Shared Pydantic base models for CRM objects across skills (HubSpot, Salesforce, etc.)."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class Contact(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class Deal(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    stage: Optional[str] = None
    amount: Optional[float] = None
    closedate: Optional[str] = None
    pipeline: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class Company(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    phone: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class Product(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class LineItem(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    hs_product_id: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class Subscription(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    mrr: Optional[float] = None
    properties: dict[str, Any] = Field(default_factory=dict)
