from bs4 import BeautifulSoup
import re
import time
import requests
import time
import random
import json

FREESHIP_IMG = "https://salt.tikicdn.com/ts/upload/f3/74/46/f4c52053d220e94a047410420eaf9faf.png"
TIKINOW_IMG = "https://salt.tikicdn.com/ts/upload/9f/32/dd/8a8d39d4453399569dfb3e80fe01de75.png"
SHOCKING_IMG = "https://salt.tikicdn.com/ts/upload/75/34/d2/4a9a0958a782da8930cdad8f08afff37.png"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0'
}
CATEGORY_LINK = "https://tiki.vn/o-to-xe-may-xe-dap/c8594?src=c.8594.hamburger_menu_fly_out_banner"
MAX_TRIES = 10

page = 1
fails = 0
products = []

while True:
    wait_period = random.randint(10, 30)/10
    print(f'Waiting to fetch page {page} - {wait_period} seconds...')
    time.sleep( wait_period )
    link = f"{CATEGORY_LINK}&page={page}"

    try:
        response = requests.get(link, headers=HEADERS)
    except:
        print('Connection failure. Retrying')
        continue

    html = response.text
    soup = BeautifulSoup(html, features="html.parser")

    products_json = []
    for item in soup.findAll('script', attrs={'type': "application/ld+json"}):
        item_dict = json.loads(item.text)
        if(item_dict["@type"] == "Product"):
            products_json.append(item_dict)

    if soup.find('div', class_='alert alert-warning'): #<div class="alert alert-warning" role="alert">Sản phẩm bạn đang tìm không có.</div>
        fails += 1
        print(f'Request Denied or end of the list - Retry:({fails}/{MAX_TRIES})')
        
        if fails >= MAX_TRIES: break
        continue
    fails = 0
    
    product_list = soup.find_all('div', {"class":"product-item"})
    is_div = True
    if len(product_list) == 0:
        product_list = soup.find_all('a', {"class":"product-item"})
        is_div = False

    for index, product in enumerate(product_list):
        print(" "*50)
        print("="*50)
        print(f"Page {page} - Product {index}")
        print("="*50)

        article = {}
        
        #Seller ID
        article["seller"] = product["data-id"] if is_div else "N/A"
        print("Seller ID:", article["seller"])
        
        #Product ID
        article["id"] = products_json[index]["sku"]
        print("Product ID:", article["id"])

        #Product price
        article["price"] = products_json[index]["offers"]["price"]
        print("Product price:", article["price"] )

        #Product title
        article["name"] = products_json[index]["name"]
        print("Product title:", article["name"] )

        #Product image
        article["image"] = products_json[index]["image"]
        print("Product image:", article["image"])

        #Product link
        article["link"] = "https://tiki.vn"+re.findall(r'^.*\.html', products_json[index]["url"])[0]
        print("Product link:", article["link"])

        #Tikinow available
        service_badge = product.find('div', {'class': 'badge-service'})
        img = False
        if service_badge:
            img = service_badge.find('img')
        article["tiki_now"] = img["src"]==TIKINOW_IMG if img else False
        print("TikiNow:", article["tiki_now"])
        
        #Freeship available
        badge_top = product.find('div', {'class': 'badge-top'})
        img = False
        if badge_top:
            img = badge_top.find('img')
        article["freeship"] = img["src"]==FREESHIP_IMG if img else False
        print("Freeship available:", article["freeship"])

        #Shocking price
        badge_top = product.find('div', {'class': 'badge-top'})
        img = False
        if badge_top:
            img = badge_top.find('img')
        article["shocking_price"] = img["src"]==SHOCKING_IMG if img else False
        print("Shocking price:", article["shocking_price"])

        #Reviews
        article["reviews"] = products_json[index]["aggregateRating"]["reviewCount"] if "aggregateRating" in products_json[index] else 0
        print("# of reviews:", article["reviews"])

        #Rating average
        article["score"] = products_json[index]["aggregateRating"]["ratingValue"] if "aggregateRating" in products_json[index] else 0
        print("Average score:", article["score"])

        #Underpricing
        article["is_under_price"] = bool(product.find('div', {'class': 'badge-under_price'}))
        print("Under price:", article["is_under_price"])

        #Discount
        discount = "0%"
        if is_div:
            discount = product.find('span', {'class': 'sale-tag'})
        else:
            discount = product.find('div', {'class': 'price-discount__discount'})
        article["discount"] = discount.text if discount else "0%"
        print("Discount:", article["discount"])

        #Paid by installments
        is_paid_by_installments = False
        if is_div:
            is_paid_by_installments = bool( product.find('div', {'class': 'installment-wrapper'}) )
        else:
            is_paid_by_installments = bool( product.find('div', {'class': 'badge-benefits'}) )
        article["installments"] = is_paid_by_installments
        print("Paid by installments:", article["installments"])

        #Freegifts
        article["free_gift"] = bool(product.find('div',{'class':'freegift-list'}))
        print("Freegift:",article["free_gift"])
        
        #Additional info
        info = ""
        if is_div:
            info = product.find('div', {'class': 'ship-label-wrapper'}).text.strip()
        else:
            info = product.find('div', {'class': 'badge-additional-info'}).text.strip()
        article["extra_info"] = info
        print('Additional info:', article["extra_info"])

        products.append(article)

    page += 1

print("Pages:", page)
print("Products:", len(products))

import pandas as pd
articles = pd.DataFrame(products)
print(articles)
articles.to_csv("./result.csv", index=False, sep =';')
