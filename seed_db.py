# seed_db.py
import sqlite3
import os

DB_PATH = 'database.db'

# sample product data
products = [
    ("Wireless Mouse", 799.0, "Ergonomic wireless mouse"),
    ("Keyboard", 1299.0, "Mechanical keyboard with RGB"),
    ("Headphones", 1999.0, "Noise-cancelling headphones"),
    ("USB-C Charger", 499.0, "Fast 20W USB-C wall charger"),
    ("Laptop Stand", 899.0, "Adjustable aluminum laptop stand")
]

def init_and_seed():
    # create database file if it doesn't exist
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'w').close()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # check if products already exist
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]

    if count == 0:
        cur.executemany(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            products
        )
        conn.commit()
        print(f"Seeded {len(products)} products.")
    else:
        print("Products already exist—no seeding needed.")

    conn.close()

if __name__ == "__main__":
    init_and_seed()
