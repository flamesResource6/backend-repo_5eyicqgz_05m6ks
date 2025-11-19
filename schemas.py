"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# Example schemas (you can keep these around for reference)

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# --------------------------------------------------
# Bulghousing schemas

BULGARIAN_REGIONS = [
    "Blagoevgrad",
    "Burgas",
    "Dobrich",
    "Gabrovo",
    "Haskovo",
    "Kardzhali",
    "Kyustendil",
    "Lovech",
    "Montana",
    "Pazardzhik",
    "Pernik",
    "Pleven",
    "Plovdiv",
    "Razgrad",
    "Ruse",
    "Shumen",
    "Silistra",
    "Sliven",
    "Smolyan",
    "Sofia City",
    "Sofia Province",
    "Stara Zagora",
    "Targovishte",
    "Varna",
    "Veliko Tarnovo",
    "Vidin",
    "Vratsa",
    "Yambol",
]

class Property(BaseModel):
    """
    Real estate properties across Bulgarian regions
    Collection name: "property"
    """
    title: str = Field(..., description="Listing title")
    region: Literal[tuple(BULGARIAN_REGIONS)] = Field(..., description="Region in Bulgaria")
    address: Optional[str] = Field(None, description="Street address or area")
    description: Optional[str] = Field(None, description="Short description")
    size_sqm: float = Field(..., gt=0, description="Area in square meters")
    currency: Literal["EUR", "BGN"] = Field("EUR", description="Currency of the provided price")
    price_value: float = Field(..., gt=0, description="Price numeric value in the provided currency")
    images: Optional[List[str]] = Field(default=None, description="Optional image URLs")

class PropertyStored(Property):
    """Extended fields stored for efficient filtering"""
    price_eur: float = Field(..., gt=0)
    price_bgn: float = Field(..., gt=0)
