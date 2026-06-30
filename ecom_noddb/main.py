from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, products, cart, orders

app = FastAPI(
    title="E-Commerce API (No Database)",
    description="FastAPI e-commerce using in-memory storage — no database needed!",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(cart.router,     prefix="/api/cart",     tags=["Cart"])
app.include_router(orders.router,   prefix="/api/orders",   tags=["Orders"])

@app.get("/")
def root():
    return {"message": "E-Commerce API running (no database mode)!", "docs": "/docs"}
