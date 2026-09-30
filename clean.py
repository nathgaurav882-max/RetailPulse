"""
RetailPulse - Raw Data Cleaning Script
Reads the raw "Online Retail II.xlsx" file and produces clean CSVs
matching the star-schema tables (Fact_Sales, Fact_Returns, Dim_Customer,
Dim_Product, Dim_Date, Dim_Geography, Dim_Adjustment).

Usage:
    pip install pandas openpyxl
    python clean.py

Before running: place "online_retail_II.xlsx" (downloaded from
https://archive.ics.uci.edu/dataset/502/online+retail+ii) in the same
folder as this script.
"""

import pandas as pd

RAW_FILE = "online_retail_II.xlsx"
OUT_DIR = "clean_csv"

NON_PRODUCT_CODES = {"POST", "M", "D", "DOT", "BANK CHARGES", "C2", "PADS", "S"}


def load_raw():
    sheet_2009 = pd.read_excel(RAW_FILE, sheet_name="Year 2009-2010")
    sheet_2010 = pd.read_excel(RAW_FILE, sheet_name="Year 2010-2011")
    df = pd.concat([sheet_2009, sheet_2010], ignore_index=True)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    return df


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    df = load_raw()
    print(f"Loaded {len(df):,} raw rows")

    # 1. De-duplicate exact repeated lines
    df = df.drop_duplicates()
    print(f"After de-dup: {len(df):,} rows")

    # Normalise key columns
    df["Invoice"] = df["Invoice"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str).str.upper().str.strip()
    df["Country"] = df["Country"].replace(
        {"Unspecified": "Unknown", "European Community": "Other Europe", "EIRE": "Ireland"}
    )
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Date"] = df["InvoiceDate"].dt.date
    df["Time"] = df["InvoiceDate"].dt.time
    df["Line_Amount"] = df["Quantity"] * df["Price"]

    # 2. Split non-product adjustment rows (postage, manual, discount, etc.) out first
    is_adjustment = df["StockCode"].isin(NON_PRODUCT_CODES)
    adjustments_df = df[is_adjustment].copy()
    df = df[~is_adjustment].copy()
    print(f"Adjustment rows isolated: {len(adjustments_df):,}")

    # 3. Split sales vs returns (cancelled invoices start with 'C', or negative quantity)
    is_return = df["Invoice"].str.startswith("C") | (df["Quantity"] < 0)
    returns_df = df[is_return].copy()
    sales_df = df[~is_return].copy()
    print(f"Sales rows: {len(sales_df):,} | Return rows: {len(returns_df):,}")

    # Drop rows with non-positive price on the sales side (data-entry errors)
    sales_df = sales_df[sales_df["Price"] > 0]

    # 4. Handle missing Customer ID -> synthetic "Guest" key (-1)
    for d in (sales_df, returns_df):
        d["Customer_ID"] = d["Customer_ID"].fillna(-1).astype(int)

    # ---- Build dimension tables ----
    dim_customer = (
        pd.concat([sales_df[["Customer_ID"]], returns_df[["Customer_ID"]]])
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_customer["Segment"] = dim_customer["Customer_ID"].apply(lambda x: "Guest" if x == -1 else "Registered")
    dim_customer.insert(0, "Customer_Key", range(1, len(dim_customer) + 1))

    dim_product = (
        pd.concat([sales_df[["StockCode", "Description"]], returns_df[["StockCode", "Description"]]])
        .drop_duplicates(subset=["StockCode"])
        .reset_index(drop=True)
    )
    dim_product.insert(0, "Product_Key", range(1, len(dim_product) + 1))

    dim_geography = (
        pd.concat([sales_df[["Country"]], returns_df[["Country"]]])
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_geography.insert(0, "Geography_Key", range(1, len(dim_geography) + 1))

    all_dates = pd.concat([sales_df["Date"], returns_df["Date"]]).drop_duplicates().sort_values()
    dim_date = pd.DataFrame({"Full_Date": all_dates}).reset_index(drop=True)
    dim_date["Full_Date"] = pd.to_datetime(dim_date["Full_Date"])
    dim_date["Day"] = dim_date["Full_Date"].dt.day
    dim_date["Month"] = dim_date["Full_Date"].dt.month
    dim_date["Quarter"] = dim_date["Full_Date"].dt.quarter
    dim_date["Year"] = dim_date["Full_Date"].dt.year
    dim_date["Is_Weekend"] = dim_date["Full_Date"].dt.dayofweek >= 5
    dim_date.insert(0, "Date_Key", range(1, len(dim_date) + 1))

    dim_adjustment = pd.DataFrame({
        "Adjustment_Type": ["Postage", "Manual", "Discount", "Bank Charges", "Sample/Other"]
    })
    dim_adjustment.insert(0, "Adjustment_Key", range(1, len(dim_adjustment) + 1))

    # ---- Build fact tables (join dims to get surrogate keys) ----
    def attach_keys(d):
        d = d.merge(dim_customer[["Customer_Key", "Customer_ID"]], on="Customer_ID", how="left")
        d = d.merge(dim_product[["Product_Key", "StockCode"]], on="StockCode", how="left")
        d = d.merge(dim_geography[["Geography_Key", "Country"]], on="Country", how="left")
        d["Full_Date"] = pd.to_datetime(d["Date"])
        d = d.merge(dim_date[["Date_Key", "Full_Date"]], on="Full_Date", how="left")
        return d

    sales_df = attach_keys(sales_df)
    returns_df = attach_keys(returns_df)

    fact_sales = sales_df[[
        "Invoice", "Date_Key", "Customer_Key", "Product_Key", "Geography_Key",
        "Quantity", "Price", "Line_Amount"
    ]].rename(columns={"Invoice": "Invoice_Key", "Price": "Unit_Price"})
    fact_sales.insert(0, "Sale_Key", range(1, len(fact_sales) + 1))

    fact_returns = returns_df[[
        "Invoice", "Date_Key", "Customer_Key", "Product_Key", "Quantity", "Line_Amount"
    ]].rename(columns={"Invoice": "Invoice_Key", "Quantity": "Returned_Quantity", "Line_Amount": "Return_Amount"})
    fact_returns.insert(0, "Return_Key", range(1, len(fact_returns) + 1))
    fact_returns["Return_Amount"] = fact_returns["Return_Amount"].abs()
    fact_returns["Returned_Quantity"] = fact_returns["Returned_Quantity"].abs()

    # ---- Write everything out ----
    dim_customer.rename(columns={"Customer_ID": "Customer_ID_Natural"}).to_csv(f"{OUT_DIR}/dim_customer.csv", index=False)
    dim_product.to_csv(f"{OUT_DIR}/dim_product.csv", index=False)
    dim_geography.to_csv(f"{OUT_DIR}/dim_geography.csv", index=False)
    dim_date.to_csv(f"{OUT_DIR}/dim_date.csv", index=False)
    dim_adjustment.to_csv(f"{OUT_DIR}/dim_adjustment.csv", index=False)
    fact_sales.to_csv(f"{OUT_DIR}/fact_sales.csv", index=False)
    fact_returns.to_csv(f"{OUT_DIR}/fact_returns.csv", index=False)
    adjustments_df.to_csv(f"{OUT_DIR}/adjustments_raw.csv", index=False)

    print("\nDone. Clean CSVs written to ./clean_csv/")
    print(f"  Fact_Sales:   {len(fact_sales):,} rows")
    print(f"  Fact_Returns: {len(fact_returns):,} rows")
    print(f"  Dim_Customer: {len(dim_customer):,} rows")
    print(f"  Dim_Product:  {len(dim_product):,} rows")
    print(f"  Dim_Geography:{len(dim_geography):,} rows")
    print(f"  Dim_Date:     {len(dim_date):,} rows")


if __name__ == "__main__":
    main()
