"""ABAC Shop — SQLite database setup and seeding."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "shop.db"

ROT = "https://img.rushordertees.com/modelImages"
UNS = "https://images.unsplash.com/photo"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT DEFAULT '🛍️',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category_id INTEGER REFERENCES categories(id),
        image_url TEXT DEFAULT '',
        back_image_url TEXT DEFAULT '',
        stock INTEGER DEFAULT 999,
        sizes TEXT DEFAULT '[]',
        colors TEXT DEFAULT '[]',
        min_quantity INTEGER DEFAULT 1,
        featured INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Upgrade existing DB that may be missing back_image_url
    try:
        c.execute("ALTER TABLE products ADD COLUMN back_image_url TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_phone TEXT DEFAULT '',
        customer_address TEXT DEFAULT '',
        items TEXT NOT NULL,
        subtotal REAL NOT NULL,
        shipping REAL DEFAULT 0,
        total REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        notes TEXT DEFAULT '',
        design_notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()

    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        _seed_data(conn, c)

    conn.close()


def _seed_data(conn, c):
    categories = [
        ("Apparel",         "Custom clothing and wearables",         "👕"),
        ("Accessories",     "Bags, cases, and more",                 "🎒"),
        ("Print & Signage", "Stickers, banners, business cards",     "🖨️"),
        ("Drinkware",       "Mugs, tumblers, water bottles",         "☕"),
        ("Sports & Teams",  "Jerseys, uniforms, team gear",          "🏆"),
    ]
    c.executemany(
        "INSERT INTO categories (name, description, icon) VALUES (?,?,?)", categories
    )
    conn.commit()

    c.execute("SELECT id, name FROM categories")
    cats = {name: cid for cid, name in c.fetchall()}

    products = [
        ("Custom Graphic T-Shirt","100% cotton premium tee with your custom design.",12.99,cats["Apparel"],f"{ROT}/rt2000_WHT_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/rt2000_WHT_bk.jpg?w=400&h=400&auto=format&q=75",'["XS","S","M","L","XL","2XL","3XL"]','["Black","White","Red","Navy","Gray","Royal Blue"]',1,1),
        ("Custom Hoodie","Heavyweight fleece hoodie with front pouch pocket.",29.99,cats["Apparel"],f"{ROT}/cp90_cc64_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/cp90_cc64_bk.jpg?w=400&h=400&auto=format&q=75",'["S","M","L","XL","2XL","3XL"]','["Black","White","Red","Navy","Gray"]',1,1),
        ("Custom Polo Shirt","Professional polo, great for business or team events.",18.99,cats["Apparel"],f"{ROT}/vl100p_c12c_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/vl100p_c12c_bk.jpg?w=400&h=400&auto=format&q=75",'["S","M","L","XL","2XL","3XL"]','["Black","White","Red","Navy","Gray"]',1,0),
        ("Custom Snapback Hat","Structured 6-panel cap with flat brim and snap closure.",15.99,cats["Apparel"],f"{ROT}/112_89_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/112_89_bk.jpg?w=400&h=400&auto=format&q=75",'["One Size"]','["Black","White","Red","Navy","Gray"]',1,1),
        ("Custom Joggers","Premium fleece joggers with drawstring waist and side pockets.",24.99,cats["Apparel"],f"{ROT}/q4500_56_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/q4500_56_bk.jpg?w=400&h=400&auto=format&q=75",'["S","M","L","XL","2XL"]','["Black","Red","Navy","Gray"]',1,0),
        ("Custom Tank Top","Lightweight breathable tank with moisture-wicking fabric.",10.99,cats["Apparel"],f"{ROT}/g640_80_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/g640_80_bk.jpg?w=400&h=400&auto=format&q=75",'["XS","S","M","L","XL","2XL"]','["Black","White","Red","Gray"]',1,0),
        ("Custom Jacket","Wind-resistant full-zip jacket with printed or embroidered design.",45.99,cats["Apparel"],f"{ROT}/f244_99d1_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/f244_99d1_bk.jpg?w=400&h=400&auto=format&q=75",'["S","M","L","XL","2XL","3XL"]','["Black","Red","Navy"]',1,0),
        ("Custom Tote Bag","Heavy-duty canvas tote bag with custom print. 15x16 inches.",14.99,cats["Accessories"],f"{ROT}/ba5100_06_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/ba5100_06_bk.jpg?w=400&h=400&auto=format&q=75",'["One Size"]','["Natural","Black","Red"]',1,1),
        ("Custom Phone Case","Slim hard-shell case with full-color custom print.",19.99,cats["Accessories"],f"{UNS}-1601784551446-20c9e07cdbdb?w=400",f"{UNS}-1612835903023-be7e1c0b7ca6?w=400",'["iPhone 14","iPhone 15","Samsung S23","Samsung S24","Pixel 8"]','[]',1,0),
        ("Custom Embroidered Patch","Iron-on or sew-on embroidered patch with your design.",7.99,cats["Accessories"],f"{UNS}-1620325867502-221cfb5faa5f?w=400",f"{UNS}-1569263879244-f5b6a6e32de9?w=400",'["2in","3in","4in"]','[]',5,0),
        ("Custom Vinyl Stickers","High-quality vinyl stickers. Waterproof and UV resistant. Sheet of 10.",8.99,cats["Print & Signage"],f"{UNS}-1612838320302-4b3b3996765e?w=400",f"{UNS}-1558618666-fcd25c85cd64?w=400",'["2in","3in","4in","5in"]','[]',10,1),
        ("Custom Banner","Heavy-duty 13oz vinyl banner with grommets. Full-color print.",49.99,cats["Print & Signage"],f"{UNS}-1504711434969-e33886168f5c?w=400",f"{UNS}-1497366216548-37526070297c?w=400",'["2x4ft","3x6ft","4x8ft","5x10ft"]','[]',1,0),
        ("Business Cards (100pk)","Premium matte or glossy business cards. 3.5x2 inches.",19.99,cats["Print & Signage"],f"{UNS}-1497366811353-6870744d04b2?w=400",f"{UNS}-1586281380117-5a60ae2050cc?w=400",'["100","250","500","1000"]','[]',1,0),
        ("Custom Coffee Mug","11oz ceramic mug with full-color custom wrap print. Dishwasher safe.",11.99,cats["Drinkware"],f"{ROT}/msc1_blk0_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/msc1_blk0_bk.jpg?w=400&h=400&auto=format&q=75",'["11oz","15oz"]','["White","Black"]',1,1),
        ("Custom Tumbler","20oz stainless steel tumbler with custom print. Double-wall insulated.",22.99,cats["Drinkware"],f"{ROT}/qtb_54_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/qtb_54_bk.jpg?w=400&h=400&auto=format&q=75",'["20oz","30oz"]','["Black","White","Red","Silver"]',1,0),
        ("Custom Sports Jersey","Moisture-wicking performance jersey with player name and number.",34.99,cats["Sports & Teams"],f"{ROT}/tt11l_QQ_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/tt11l_QQ_bk.jpg?w=400&h=400&auto=format&q=75",'["YXS","YS","YM","YL","S","M","L","XL","2XL"]','["Black","White","Red","Navy"]',6,1),
        ("Team Uniform Set","Complete uniform set: jersey + shorts. Min 6 pieces.",59.99,cats["Sports & Teams"],f"{ROT}/tt51_9k_fr.jpg?w=400&h=400&auto=format&q=75",f"{ROT}/tt51_9k_bk.jpg?w=400&h=400&auto=format&q=75",'["YXS","YS","YM","YL","S","M","L","XL","2XL"]','["Black","White","Red","Navy"]',6,0),
    ]

    for p in products:
        c.execute("""INSERT INTO products
            (name, description, price, category_id, image_url, back_image_url,
             sizes, colors, min_quantity, featured, active)
            VALUES (?,?,?,?,?,?,?,?,?,?,1)""", p)
    conn.commit()


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
