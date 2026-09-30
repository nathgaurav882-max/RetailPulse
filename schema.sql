-- RetailPulse star schema (run against the "retailpulse" database)

DROP TABLE IF EXISTS fact_sales, fact_returns, dim_customer, dim_product, dim_geography, dim_date, dim_adjustment CASCADE;

CREATE TABLE dim_customer (
    customer_key        INTEGER PRIMARY KEY,
    customer_id_natural  INTEGER,
    segment              VARCHAR(20)
);

CREATE TABLE dim_product (
    product_key   INTEGER PRIMARY KEY,
    stockcode     VARCHAR(20),
    description   VARCHAR(255)
);

CREATE TABLE dim_geography (
    geography_key INTEGER PRIMARY KEY,
    country       VARCHAR(100)
);

CREATE TABLE dim_date (
    date_key    INTEGER PRIMARY KEY,
    full_date   DATE,
    day         INTEGER,
    month       INTEGER,
    quarter     INTEGER,
    year        INTEGER,
    is_weekend  BOOLEAN
);

CREATE TABLE dim_adjustment (
    adjustment_key   INTEGER PRIMARY KEY,
    adjustment_type  VARCHAR(50)
);

CREATE TABLE fact_sales (
    sale_key       INTEGER PRIMARY KEY,
    invoice_key    VARCHAR(20),
    date_key       INTEGER REFERENCES dim_date(date_key),
    customer_key   INTEGER REFERENCES dim_customer(customer_key),
    product_key    INTEGER REFERENCES dim_product(product_key),
    geography_key  INTEGER REFERENCES dim_geography(geography_key),
    quantity       INTEGER,
    unit_price     NUMERIC(10,2),
    line_amount    NUMERIC(12,2)
);

CREATE TABLE fact_returns (
    return_key         INTEGER PRIMARY KEY,
    invoice_key        VARCHAR(20),
    date_key           INTEGER REFERENCES dim_date(date_key),
    customer_key       INTEGER REFERENCES dim_customer(customer_key),
    product_key        INTEGER REFERENCES dim_product(product_key),
    returned_quantity  INTEGER,
    return_amount      NUMERIC(12,2)
);
