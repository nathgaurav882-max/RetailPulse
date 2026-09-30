"""
RetailPulse - Real-Time Stream Simulator (psycopg2-only version)

Avoids SQLAlchemy entirely (works around Windows Application Control
policies that can block SQLAlchemy's compiled cyextension DLLs).

Usage:
    pip install pandas psycopg2-binary
    python stream_producer.py
"""

import time
import random
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# --- Edit these to match your local Postgres setup ---
DB_USER = "postgres"
DB_PASSWORD = "postgres"   # <-- change this to your real password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "retailpulse"
# -------------------------------------------------------

BATCH_SIZE = 5
INTERVAL_SECONDS = 3

COLUMNS = ["sale_key", "invoice_key", "date_key", "customer_key",
           "product_key", "geography_key", "quantity", "unit_price", "line_amount"]


def main():
    df = pd.read_csv("clean_csv/fact_sales.csv", low_memory=False)
    df.columns = [c.lower() for c in df.columns]
    df = df[COLUMNS]  # ensure correct order
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    total = len(df)

    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                             user=DB_USER, password=DB_PASSWORD)
    conn.autocommit = True
    cur = conn.cursor()

    print(f"Streaming {total:,} sales rows into fact_sales, {BATCH_SIZE} every {INTERVAL_SECONDS}s...")
    print("Leave this running. Press Ctrl+C to stop.\n")

    cur.execute("DELETE FROM fact_sales")
    print("fact_sales cleared -- starting from zero.\n")

    insert_sql = f"INSERT INTO fact_sales ({', '.join(COLUMNS)}) VALUES %s"

    pos = 0
    batch_num = 0
    try:
        while pos < total:
            batch = df.iloc[pos: pos + BATCH_SIZE]
            values = [tuple(row) for row in batch.itertuples(index=False, name=None)]
            execute_values(cur, insert_sql, values)
            batch_num += 1
            pos += BATCH_SIZE
            print(f"[Batch {batch_num}] inserted {len(batch)} orders "
                  f"({min(pos, total):,}/{total:,} total so far)")
            time.sleep(INTERVAL_SECONDS + random.uniform(-0.5, 0.5))
    except KeyboardInterrupt:
        print("\nStopped. Re-run to continue.")
    finally:
        cur.close()
        conn.close()

    print("\nAll rows streamed.")


if __name__ == "__main__":
    main()
