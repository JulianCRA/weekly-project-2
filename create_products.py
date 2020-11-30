import sqlite3
import re

PATH_TO_DB = './'

conn = sqlite3.connect(PATH_TO_DB+'tiki.db')
cur = conn.cursor()

query = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        sku VARCHAR(255),
        name VARCHAR(255),
        url TEXT, 
        price INTEGER,
        discount INTEGER,
        image TEXT,
        seller_id VARCHAR(255),
        tikinow INTEGER,
        freeship INTEGER,
        shocking INTEGER,
        under_price INTEGER,
        installments INTEGER,
        gifts INTEGER,
        reviews INTEGER,
        rating VARCHAR(10),
        info TEXT,
        subcategory INTEGER   
        
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
try:
    cur.execute('DROP TABLE products;')
    conn.commit()

    cur.execute(query)
    conn.commit()
    # print(cur.execute('select count(*) from products').fetchall())
except Exception as err:
    print('ERROR BY CREATE TABLE', err)

