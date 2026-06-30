# ─────────────────────────────────────────────────────────
#  In-Memory Store — replaces the database entirely
#  All data lives in Python dicts/lists in RAM.
#  Data resets when server restarts (no persistence).
# ─────────────────────────────────────────────────────────

from typing import Dict, List, Any

# ── Tables (plain Python dicts) ───────────────────────────

users:      Dict[int, dict] = {}   # id → user dict
products:   Dict[int, dict] = {}   # id → product dict
categories: Dict[int, dict] = {}   # id → category dict
cart_items: Dict[int, dict] = {}   # id → cart_item dict
orders:     Dict[int, dict] = {}   # id → order dict
order_items: Dict[int, dict] = {}  # id → order_item dict

# ── Auto-increment ID counters ────────────────────────────

counters = {
    "users":       0,
    "products":    0,
    "categories":  0,
    "cart_items":  0,
    "orders":      0,
    "order_items": 0,
}

def next_id(table: str) -> int:
    counters[table] += 1
    return counters[table]

# ── Seed some sample data on startup ─────────────────────

def seed():
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Admin user
    uid = next_id("users")
    users[uid] = {
        "id": uid, "name": "Admin", "email": "admin@example.com",
        "password": pwd.hash("admin123"), "is_admin": True
    }

    # Sample category
    cid = next_id("categories")
    categories[cid] = {"id": cid, "name": "Electronics"}

    # Sample products
    for name, price, stock in [
        ("Wireless Headphones", 1499.0, 50),
        ("Mechanical Keyboard", 2999.0, 30),
        ("USB-C Hub",            899.0, 100),
    ]:
        pid = next_id("products")
        products[pid] = {
            "id": pid, "name": name, "description": f"High quality {name}",
            "price": price, "stock": stock, "image_url": None,
            "is_active": True, "category_id": cid
        }

seed()
