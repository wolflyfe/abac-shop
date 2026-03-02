"""Pydantic models for ABAC Shop API."""

from pydantic import BaseModel
from typing import Optional, List


class CategoryCreate(BaseModel):
    name: str
    description: str = ""
    icon: str = "🛍️"


class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    category_id: int
    image_url: str = ""
    back_image_url: str = ""
    sizes: List[str] = []
    colors: List[str] = []
    min_quantity: int = 1
    featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    back_image_url: Optional[str] = None
    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    min_quantity: Optional[int] = None
    featured: Optional[bool] = None
    active: Optional[bool] = None


class OrderItem(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    size: str = ""
    color: str = ""


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str = ""
    customer_address: str = ""
    items: List[OrderItem]
    notes: str = ""
    design_notes: str = ""


class OrderStatusUpdate(BaseModel):
    status: str
