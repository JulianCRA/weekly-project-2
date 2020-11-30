from bs4 import BeautifulSoup
import requests
import sqlite3
import re
import json
import time
import random

TIKI_URL = 'https://tiki.vn'
PATH_TO_DB = './'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

# def add_product(product):
#     query = """
#         INSERT INTO products (sku, name, url, price, discount, image, seller_id, tikinow, freeship, shocking, under_price, installments, gifts, reviews, rating, info)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
#     """
#     val = (product['sku'], product['name'], product['url'], product['price'], product['discount'], product['image'], product['seller_id'], product['tikinow'], product['freeship'], product['shocking'], product['under_price'], product['installments'], product['gifts'], product['reviews'], product['rating'], product['info'])
#     try:
#         cur.execute(query, val)
#         conn.commit()
#     except Exception as err:
#         print('ERROR BY INSERT:', err)

def add_product_page(list):
    query = '''
        INSERT INTO products(sku,
        name,
        url, 
        price,
        discount,
        image,
        seller_id,
        tikinow,
        freeship,
        shocking,
        under_price,
        installments,
        gifts,
        reviews,
        rating,
        info,
        subcategory)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''
    p = []
    for product in list:
        tuple = (
            product['sku'], 
            product['name'], 
            product['url'],
            product['price'],
            product['discount'],
            product['image'],
            product['seller_id'],
            product['tikinow'],
            product['freeship'],
            product['shocking'],
            product['under_price'],
            product['installments'],
            product['gifts'],
            product['reviews'],
            product['rating'],
            product['info'],
            product['subcategory']
        )
        p.append(tuple)
    
    try:
        cur.executemany(query,p)
        conn.commit()
        print(f'Added {len(list)} products')
    except Exception as err:
        print('ERROR MULTIPLE INSERTION:', err)


current_category = 0
current_page = 0

try:
    f = open('current.json',) 
    save_point = json.load(f) 
    current_category = save_point["category"]
    current_page = save_point["page"]
    f.close() 
except IOError:
    print("File not accessible")

conn = sqlite3.connect(PATH_TO_DB+'tiki.db')
cur = conn.cursor()

query = '''
            SELECT tiki_id FROM categories
            WHERE id NOT IN (SELECT parent_id FROM categories WHERE parent_id is not null)
                AND tiki_id > ?
            ORDER BY tiki_id asc
        '''
val = (current_category,)
categories = cur.execute(query, val).fetchall()

for category in categories:
    
    
    while True:
        print(category)
        product_page = []
        apilink = f'https://tiki.vn/api/v2/products?limit=300&category={category[0]}&page={current_page}'
        try:
            response = requests.get(apilink, headers=HEADERS)
        except:
            print('Connection Error')
            continue
        
        res = response.json()
        
        if len(res['data']) == 0: break
        for item in res['data']:
            product = {}
            product['sku'] = item['sku'] if 'sku' in item else 0
            product['name'] = item['name']
            product['url'] = 'https://tiki.vn/'+item['url_path']
            product['price'] = item['price']
            product['discount'] = item['discount_rate']
            product['image'] = item['thumbnail_url']
            product['seller_id'] = item['seller_product_id']

            has_badges = 'badges_new' in item

            flag = 0
            if has_badges:
                for badge in item['badges_new']:
                    if badge["code"] == 'tikinow':
                        flag = 1
                        break
            product['tikinow'] = flag

            flag = 0
            if has_badges:
                for badge in item['badges_new']:
                    if badge["code"] == 'freeship':
                        flag = 1
                        break
            product['freeship'] = flag

            product['shocking'] = 0

            flag = 0
            if has_badges:
                for badge in item['badges_new']:
                    if badge["code"] == 'is_best_price_guaranteed':
                        flag = 1
                        break
            product['under_price'] = flag

            flag = 0
            if has_badges:
                for badge in item['badges_new']:
                    if badge["code"] == 'installment':
                        flag = 1
                        break
            product['installments'] = flag

            product['gifts'] = 'freegift_items' in item

            product['reviews'] = item['review_count']
            product['rating'] = item['rating_average']

            flag = None
            if has_badges:
                for badge in item['badges_new']:
                    if badge["code"] == 'only_ship_to':
                        flag = badge['text']
                        break
            product['info'] = flag
            product['subcategory'] = category[0]
            
            product_page.append(product)

        add_product_page(product_page)

        paging = res['paging']
        if paging['current_page'] == paging['last_page']: break


        json_object = json.dumps({"category":category[0], "page":current_page}, indent = 4) 
  
        # Writing to sample.json 
        with open("current.json", "w") as outfile: 
            outfile.write(json_object) 

        current_page += 1

        wait_period = random.randint(20, 40)/10
        print(f'Waiting for {wait_period} seconds to fetch next page')
        time.sleep(wait_period)
        
    current_page = 1
    wait_period = random.randint(20, 40)/10
    print(f'Waiting for {wait_period} seconds to fetch next category')
    time.sleep(wait_period)

print('DONE')
   