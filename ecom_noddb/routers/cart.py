from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth_utils import get_current_user
import store

router = APIRouter()

class CartAddIn(BaseModel):
    product_id: int
    quantity:   int = 1

class CartUpdateIn(BaseModel):
    quantity: int

@router.get("/")
def get_cart(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    items = [
        {**item, "product": store.products.get(item["product_id"])}
        for item in store.cart_items.values()
        if item["user_id"] == user_id
    ]
    total = sum(
        store.products[i["product_id"]]["price"] * i["quantity"]
        for i in store.cart_items.values()
        if i["user_id"] == user_id and store.products.get(i["product_id"])
    )
    return {"items": items, "total_price": round(total, 2)}

@router.post("/", status_code=201)
def add_to_cart(payload: CartAddIn, current_user: dict = Depends(get_current_user)):
    product = store.products.get(payload.product_id)
    if not product or not product["is_active"]:
        raise HTTPException(404, "Product not found")
    if product["stock"] < payload.quantity:
        raise HTTPException(400, f"Only {product['stock']} units in stock")

    user_id = current_user["id"]
    # Check if already in cart
    existing = next(
        (item for item in store.cart_items.values()
         if item["user_id"] == user_id and item["product_id"] == payload.product_id),
        None
    )
    if existing:
        existing["quantity"] += payload.quantity
    else:
        cid = store.next_id("cart_items")
        store.cart_items[cid] = {
            "id":         cid,
            "user_id":    user_id,
            "product_id": payload.product_id,
            "quantity":   payload.quantity,
        }
    return {"message": "Item added to cart"}

@router.put("/{item_id}")
def update_cart(item_id: int, payload: CartUpdateIn, current_user: dict = Depends(get_current_user)):
    item = store.cart_items.get(item_id)
    if not item or item["user_id"] != current_user["id"]:
        raise HTTPException(404, "Cart item not found")
    if payload.quantity <= 0:
        del store.cart_items[item_id]
    else:
        item["quantity"] = payload.quantity
    return {"message": "Cart updated"}

@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: int, current_user: dict = Depends(get_current_user)):
    item = store.cart_items.get(item_id)
    if not item or item["user_id"] != current_user["id"]:
        raise HTTPException(404, "Cart item not found")
    del store.cart_items[item_id]

@router.delete("/", status_code=204)
def clear_cart(current_user: dict = Depends(get_current_user)):
    to_delete = [k for k, v in store.cart_items.items() if v["user_id"] == current_user["id"]]
    for k in to_delete:
        del store.cart_items[k]
