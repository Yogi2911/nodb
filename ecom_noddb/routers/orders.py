from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from auth_utils import get_current_user, get_admin_user
import store

router = APIRouter()

class OrderIn(BaseModel):
    shipping_address: str

class StatusUpdate(BaseModel):
    status: str  # pending, confirmed, shipped, delivered, cancelled

VALID_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

@router.post("/checkout", status_code=201)
def checkout(payload: OrderIn, current_user: dict = Depends(get_current_user)):
    user_id    = current_user["id"]
    user_cart  = [item for item in store.cart_items.values() if item["user_id"] == user_id]

    if not user_cart:
        raise HTTPException(400, "Cart is empty")

    # Validate stock for all items first
    for item in user_cart:
        product = store.products.get(item["product_id"])
        if not product:
            raise HTTPException(404, f"Product {item['product_id']} not found")
        if product["stock"] < item["quantity"]:
            raise HTTPException(400, f"Insufficient stock for '{product['name']}'")

    # Calculate total
    total = sum(
        store.products[item["product_id"]]["price"] * item["quantity"]
        for item in user_cart
    )

    # Create order
    oid = store.next_id("orders")
    store.orders[oid] = {
        "id":               oid,
        "user_id":          user_id,
        "total_amount":     round(total, 2),
        "status":           "pending",
        "shipping_address": payload.shipping_address,
    }

    # Create order items + deduct stock
    for item in user_cart:
        product = store.products[item["product_id"]]
        iid = store.next_id("order_items")
        store.order_items[iid] = {
            "id":         iid,
            "order_id":   oid,
            "product_id": item["product_id"],
            "quantity":   item["quantity"],
            "unit_price": product["price"],
            "product":    product,
        }
        product["stock"] -= item["quantity"]

    # Clear cart
    to_delete = [k for k, v in store.cart_items.items() if v["user_id"] == user_id]
    for k in to_delete:
        del store.cart_items[k]

    order = store.orders[oid]
    order["order_items"] = [i for i in store.order_items.values() if i["order_id"] == oid]
    return order

@router.get("/")
def my_orders(current_user: dict = Depends(get_current_user)):
    user_orders = [o for o in store.orders.values() if o["user_id"] == current_user["id"]]
    for o in user_orders:
        o["order_items"] = [i for i in store.order_items.values() if i["order_id"] == o["id"]]
    return user_orders

@router.get("/{order_id}")
def get_order(order_id: int, current_user: dict = Depends(get_current_user)):
    order = store.orders.get(order_id)
    if not order or order["user_id"] != current_user["id"]:
        raise HTTPException(404, "Order not found")
    order["order_items"] = [i for i in store.order_items.values() if i["order_id"] == order_id]
    return order

# ── Admin ─────────────────────────────────────────────────

@router.get("/admin/all")
def all_orders(_=Depends(get_admin_user)):
    all_o = list(store.orders.values())
    for o in all_o:
        o["order_items"] = [i for i in store.order_items.values() if i["order_id"] == o["id"]]
    return all_o

@router.put("/admin/{order_id}/status")
def update_status(order_id: int, payload: StatusUpdate, _=Depends(get_admin_user)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(400, f"Status must be one of: {VALID_STATUSES}")
    order = store.orders.get(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    order["status"] = payload.status
    return order
