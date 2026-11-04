#Carrega os CSVs uma vez no startup e disponibiliza como DataFrames.


import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_all():
    data = {
        "categories": pd.read_csv(os.path.join(DATA_DIR, "desafio_tecnico_ai_eng - categories.csv")),
        "customers": pd.read_csv(os.path.join(DATA_DIR, "desafio_tecnico_ai_eng - customers.csv")),
        "products": pd.read_csv(os.path.join(DATA_DIR, "desafio_tecnico_ai_eng - products.csv")),
        "orders": pd.read_csv(os.path.join(DATA_DIR, "desafio_tecnico_ai_eng - orders.csv")),
        "order_items": pd.read_csv(os.path.join(DATA_DIR, "desafio_tecnico_ai_eng - order_items.csv")),
        "promotions": pd.read_csv(os.path.join(DATA_DIR, "desafio_tecnico_ai_eng - promotions.csv")),
    }
    return data

# Singleton: carrega uma vez
DB = load_all()
