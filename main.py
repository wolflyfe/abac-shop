"""ABAC One Stop Custom Shop — FastAPI Backend"""

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
import json
from pathlib import Path

from models import (
    CategoryCreate, ProductCreate, ProductUpdate,
    OrderCreate, OrderStatusUpdate
)
from database import init_db, get_db
from mockup_processor import process_product

ADMIN_KEY = "BerNard33"   # Change this to a strong secret
STATIC_DIR = Path(__file__).parent / "static"
FREE_SHIPPING_THRESHOLD = 75.0
SHIPPING_RATE = 9.99


def require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized — invalid admin key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    STATIC_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="ABAC Shop API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Categories ───────────────────────────────────────────────────────────────

@app.get("/api/categories")
async def get_categories(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/categories")
async def create_category(cat: CategoryCreate, db=Depends(get_db), _=Depends(require_admin)):
    cur = db.execute(
        "INSERT INTO categories (name, description, icon) VALUES (?,?,?)",
        (cat.name, cat.description, cat.icon)
    )
    db.commit()
    return {"id": cur.lastrowid, **cat.model_dump()}


@app.delete("/api/categories/{cat_id}")
async def delete_category(cat_id: int, db=Depends(get_db), _=Depends(require_admin)):
    db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    db.commit()
    return {"message": "Category deleted"}


# ── Products ─────────────────────────────────────────────────────────────────

@app.get("/api/products")
async def get_products(
    category_id: int = None,
    featured: bool = None,
    search: str = None,
    db=Depends(get_db)
):
    query = """
        SELECT p.*, c.name as category_name, c.icon as category_icon
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.active = 1
    """
    params = []
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if featured is not None:
        query += " AND p.featured = ?"
        params.append(1 if featured else 0)
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY p.featured DESC, p.created_at DESC"

    rows = db.execute(query, params).fetchall()
    products = []
    for r in rows:
        p = dict(r)
        p["sizes"] = json.loads(p.get("sizes") or "[]")
        p["colors"] = json.loads(p.get("colors") or "[]")
        products.append(p)
    return products


@app.get("/api/products/all")
async def get_all_products(db=Depends(get_db), _=Depends(require_admin)):
    """Admin: returns all products including inactive."""
    rows = db.execute("""
        SELECT p.*, c.name as category_name
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
    """).fetchall()
    products = []
    for r in rows:
        p = dict(r)
        p["sizes"] = json.loads(p.get("sizes") or "[]")
        p["colors"] = json.loads(p.get("colors") or "[]")
        products.append(p)
    return products


@app.get("/api/products/{product_id}")
async def get_product(product_id: int, db=Depends(get_db)):
    row = db.execute("""
        SELECT p.*, c.name as category_name, c.icon as category_icon
        FROM products p LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    p = dict(row)
    p["sizes"] = json.loads(p.get("sizes") or "[]")
    p["colors"] = json.loads(p.get("colors") or "[]")
    return p


@app.post("/api/products")
async def create_product(product: ProductCreate, bg: BackgroundTasks, db=Depends(get_db), _=Depends(require_admin)):
    cur = db.execute("""
        INSERT INTO products
            (name, description, price, category_id, image_url, back_image_url, sizes, colors, min_quantity, featured, active)
        VALUES (?,?,?,?,?,?,?,?,?,?,1)
    """, (
        product.name, product.description, product.price,
        product.category_id, product.image_url, product.back_image_url,
        json.dumps(product.sizes), json.dumps(product.colors),
        product.min_quantity, 1 if product.featured else 0
    ))
    db.commit()
    new_id = cur.lastrowid
    bg.add_task(process_product, new_id)
    return {"id": new_id, "message": "Product created — mockup processing started"}


@app.put("/api/products/{product_id}")
async def update_product(product_id: int, product: ProductUpdate, bg: BackgroundTasks, db=Depends(get_db), _=Depends(require_admin)):
    updates = {}
    if product.name is not None:           updates["name"] = product.name
    if product.description is not None:    updates["description"] = product.description
    if product.price is not None:          updates["price"] = product.price
    if product.category_id is not None:    updates["category_id"] = product.category_id
    if product.image_url is not None:      updates["image_url"] = product.image_url
    if product.back_image_url is not None: updates["back_image_url"] = product.back_image_url
    if product.sizes is not None:          updates["sizes"] = json.dumps(product.sizes)
    if product.colors is not None:         updates["colors"] = json.dumps(product.colors)
    if product.min_quantity is not None:   updates["min_quantity"] = product.min_quantity
    if product.featured is not None:       updates["featured"] = 1 if product.featured else 0
    if product.active is not None:         updates["active"] = 1 if product.active else 0

    if not updates:
        return {"message": "Nothing to update"}

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    db.execute(f"UPDATE products SET {set_clause} WHERE id = ?", [*updates.values(), product_id])
    db.commit()
    # Re-process mockups if image URLs changed
    if "image_url" in updates or "back_image_url" in updates:
        bg.add_task(process_product, product_id)
        return {"message": "Product updated — mockup processing started"}
    return {"message": "Product updated"}


@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int, db=Depends(get_db), _=Depends(require_admin)):
    db.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
    db.commit()
    return {"message": "Product deactivated"}


# ── Orders ────────────────────────────────────────────────────────────────────

@app.post("/api/orders")
async def create_order(order: OrderCreate, db=Depends(get_db)):
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    subtotal = sum(item.price * item.quantity for item in order.items)
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_RATE
    total = subtotal + shipping

    cur = db.execute("""
        INSERT INTO orders
            (customer_name, customer_email, customer_phone, customer_address,
             items, subtotal, shipping, total, notes, design_notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        order.customer_name, order.customer_email,
        order.customer_phone, order.customer_address,
        json.dumps([i.model_dump() for i in order.items]),
        subtotal, shipping, total,
        order.notes, order.design_notes
    ))
    db.commit()

    return {
        "order_id": cur.lastrowid,
        "subtotal": round(subtotal, 2),
        "shipping": round(shipping, 2),
        "total": round(total, 2),
        "message": "Order placed! We'll contact you within 24 hours to finalize your design."
    }


@app.get("/api/orders")
async def get_orders(status: str = None, db=Depends(get_db), _=Depends(require_admin)):
    query = "SELECT * FROM orders"
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"

    rows = db.execute(query, params).fetchall()
    orders = []
    for r in rows:
        o = dict(r)
        o["items"] = json.loads(o["items"])
        orders.append(o)
    return orders


@app.get("/api/orders/{order_id}")
async def get_order(order_id: int, db=Depends(get_db), _=Depends(require_admin)):
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    o = dict(row)
    o["items"] = json.loads(o["items"])
    return o


@app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, body: OrderStatusUpdate, db=Depends(get_db), _=Depends(require_admin)):
    valid = {"pending", "confirmed", "in_production", "shipped", "delivered", "cancelled"}
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid}")
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (body.status, order_id))
    db.commit()
    return {"message": f"Order {order_id} → {body.status}"}


@app.get("/api/stats")
async def get_stats(db=Depends(get_db), _=Depends(require_admin)):
    total_orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue = db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status != 'cancelled'").fetchone()[0]
    total_products = db.execute("SELECT COUNT(*) FROM products WHERE active = 1").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0]
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_products": total_products,
        "pending_orders": pending
    }


# ── Serve frontend ─────────────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7800, reload=False)
