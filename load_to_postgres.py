"""
RetailPulse - Load clean CSVs into PostgreSQL
"""

import pandas as pd
from sqlalchemy import create_engine

# --- Edit these to match your local Postgres setup ---
DB_USER = "postgres"
DB_PASSWORD = "postgres"   # <-- change this to your real password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "retailpulse"
# -------------------------------------------------------

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

FILES_TO_TABLES = [
    ("clean_csv/dim_customer.csv", "dim_customer"),
    ("clean_csv/dim_product.csv", "dim_product"),
    ("clean_csv/dim_geography.csv", "dim_geography"),
    ("clean_csv/dim_date.csv", "dim_date"),
    ("clean_csv/dim_adjustment.csv", "dim_adjustment"),
    ("clean_csv/fact_returns.csv", "fact_returns"),
]

for csv_path, table_name in FILES_TO_TABLES:
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]   # match Postgres's lowercase column names
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"Loaded {len(df):,} rows into {table_name}")

print("\nAll dimension tables loaded. fact_sales will be filled by stream_producer.py.")