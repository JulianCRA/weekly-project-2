from bs4 import BeautifulSoup
import requests
import sqlite3
import re

TIKI_URL = 'https://tiki.vn'
PATH_TO_DB = './'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}


conn = sqlite3.connect(PATH_TO_DB+'tiki.db')
cur = conn.cursor()

def get_url(url):
    try:
        response = requests.get(url,headers = HEADERS).text
        soup = BeautifulSoup(response, 'html.parser')
        return soup
    except Exception as err:
        print('ERROR BY REQUEST:', err)

class Category:
    def __init__(self, name, url, parent_id=None, cat_id=None):
        self.cat_id = cat_id
        self.name = name
        self.url = url
        self.parent_id = parent_id
        self.tiki_id = re.findall('c(\d+)', self.url)
        self.tiki_id = int(self.tiki_id[0]) if self.tiki_id else 0

    def __repr__(self):
        return f"ID: {self.cat_id}, Name: {self.name}, URL: {self.url}, Parent: {self.parent_id}, Tiki_ID: {self.tiki_id}"

    def save_into_db(self):
        query = """
            INSERT INTO categories (name, url, parent_id, has_children, tiki_id)
            VALUES (?, ?, ?, ?, ?);
        """
        val = (self.name, self.url, self.parent_id, 1, self.tiki_id)
        try:
            cur.execute(query, val)
            self.cat_id = cur.lastrowid
            conn.commit()
        except Exception as err:
            print('ERROR BY INSERT:', err)

    def set_as_leaf(self):

        query = """
            UPDATE categories
            SET has_children = 0
            WHERE tiki_id = ?
        """

        try:
            val = (self.tiki_id,)
            cur.execute(query, val)
            conn.commit()
        except Exception as err:
            print('CAN\'T UPDATE:', err)
    

def create_categories_table():
    query = """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            url TEXT, 
            parent_id INTEGER, 
            has_children INTEGER,
            tiki_id INTEGER,
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    try:
        cur.execute(query)
        conn.commit()
    except Exception as err:
        print('ERROR BY CREATE TABLE', err)

CATEGORY_SET = set()
def can_add_to_cat_set(cat_name,save=False):
  if cat_name not in CATEGORY_SET:
    if save:
      CATEGORY_SET.add(cat_name)
      print(f'Added "{cat_name}" to CATEGORY_SET')
    return True
  return False

def get_main_categories(save_db=False):
    soup = get_url(TIKI_URL)

    result = []
    for a in soup.find_all('a', {'class': 'menu-link'}):
        name = a.find('span', {'class': 'text'}).text.strip()
        
        _=can_add_to_cat_set(name,save_db)

        url = a['href']
        main_cat = Category(name, url) # object from class Category

        if save_db:
            main_cat.save_into_db()
        result.append(main_cat)
    return result

# cur.execute('DROP TABLE categories;')
# conn.commit()
create_categories_table()
main_categories = get_main_categories(save_db=True)

def get_sub_categories(parent_category, save_db=False):
    parent_url = parent_category.url
    result = []

    try:
        soup = get_url(parent_url)
        for a in soup.find_all('a', {'class':'item--category'}):
            name = a.text.strip()
            if can_add_to_cat_set(name,save_db): 
              sub_url = a['href']
              cat = Category(name, sub_url, parent_category.cat_id)
              if save_db:
                  cat.save_into_db()
              result.append(cat)
    except Exception as err:
        print('ERROR IN GETTING SUB CATEGORIES:', err)
    if len(result) == 0:
        parent_category.set_as_leaf()
    return result

def get_all_categories(categories,save_db):
    # if I reach the last possible category, I need to stop
    if len(categories) == 0:
        return      
    for cat in categories:
        print(f'Getting {cat} sub-categories...')
        sub_categories = get_sub_categories(cat, save_db=save_db)
        print(f'Finished! {cat.name} has {len(sub_categories)} sub-categories')
        get_all_categories(sub_categories,save_db=save_db)

get_all_categories(main_categories,save_db=True)