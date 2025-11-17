import pandas as pd
import sqlite3
import os

# Path to local data folder
data_path = "data"

db = "ecommerce.db"
if os.path.exists(db):
    os.remove(db)

conn = sqlite3.connect(db)

def load(name):
    df = pd.read_csv(f"{data_path}/{name}")
    table_name = name.replace("olist_", "").replace("_dataset.csv", "").replace(".csv", "")
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    print(f"Loaded: {name} -> {table_name} table ({df.shape[0]} rows, {df.shape[1]} columns)")

# Load all datasets
load("olist_customers_dataset.csv")
load("olist_orders_dataset.csv")
load("olist_order_items_dataset.csv")
load("olist_order_payments_dataset.csv")
load("olist_order_reviews_dataset.csv")
load("olist_products_dataset.csv")
load("olist_sellers_dataset.csv")
load("olist_geolocation_dataset.csv")
load("product_category_name_translation.csv")

conn.close()
print(f"\nDatabase created: {db}")
print("Tables: customers, orders, order_items, order_payments, order_reviews, products, sellers, geolocation, product_category_name_translation")
