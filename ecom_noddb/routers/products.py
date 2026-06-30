from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from auth_utils import get_current_user, get_admin_user
import store

router = APIRouter()

class CategoryIn(BaseModel):
    name: str

class ProductIn(BaseModel):
    name:        str
    description: Optional[str] = None
    price:       float
    stock:       int
    image_url:   Optional[str] = None
    category_id: Optional[int] = None

class ProductUpdate(BaseModel):
    name:        Optional[str]   = None
    description: Optional[str]   = None
    price:       Optional[float] = None
    stock:       Optional[int]   = None
    image_url:   Optional[str]   = None
    is_active:   Optional[bool]  = None
    category_id: Optional[int]   = None

# ── Categories ────────────────────────────────────────────

@router.get("/categories")
def list_categories():
    return list(store.categories.values())

@router.post("/categories", status_code=201)
def create_category(payload: CategoryIn, _=Depends(get_admin_user)):
    for c in store.categories.values():
        if c["name"].lower() == payload.name.lower():
            raise HTTPException(400, "Category already exists")
    cid = store.next_id("categories")
    store.categories[cid] = {"id": cid, "name": payload.name}
    return store.categories[cid]

# ── Products ──────────────────────────────────────────────

@router.get("/")
def list_products(
    search:      Optional[str]   = Query(None),
    category_id: Optional[int]   = Query(None),
    min_price:   Optional[float] = Query(None),
    max_price:   Optional[float] = Query(None),
    in_stock:    bool             = Query(False),
    skip:        int              = Query(0, ge=0),
    limit:       int              = Query(20, le=100),
):
    items = [p for p in store.products.values() if p["is_active"]]
    if search:
        items = [p for p in items if search.lower() in p["name"].lower()]
    if category_id:
        items = [p for p in items if p["category_id"] == category_id]
    if min_price is not None:
        items = [p for p in items if p["price"] >= min_price]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]
    if in_stock:
        items = [p for p in items if p["stock"] > 0]
    return items[skip: skip + limit]

@router.get("/{product_id}")
def get_product(product_id: int):
    p = store.products.get(product_id)
    if not p or not p["is_active"]:
        raise HTTPException(404, "Product not found")
    return p

@router.post("/", status_code=201)
def create_product(payload: ProductIn, _=Depends(get_admin_user)):
    pid = store.next_id("products")
    store.products[pid] = {
        "id":          pid,
        "name":        payload.name,
        "description": payload.description,
        "price":       payload.price,
        "stock":       payload.stock,
        "image_url":   payload.image_url,
        "is_active":   True,
        "category_id": payload.category_id,
    }
    return store.products[pid]

@router.put("/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, _=Depends(get_admin_user)):
    p = store.products.get(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        p[field] = value
    return p

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, _=Depends(get_admin_user)):
    p = store.products.get(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    p["is_active"] = False  # soft delete
