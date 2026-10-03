# RetailPulse — Business Intelligence Project 
![Python](https://img.shields.io/badge/Python-3.14-blue) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791) ![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811) ![Status](https://img.shields.io/badge/Status-Complete-brightgreen) 

**Course:** 23UDSPEL4704A – Business Intelligence | B.Tech CSE (Data Science), GHRCEM Pune
**Team:** Gaurav, [Add Teammate Name]

A Business Intelligence framework for customer value, returns, and sales performance
analytics in online retail — built end-to-end from raw, uncleaned transaction data to
a live, real-time-refreshing Power BI dashboard.

## Project Overview

- **Domain:** Online retail / e-commerce
- **Raw dataset:** [Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) — UCI Machine Learning Repository (NOT Kaggle, not pre-cleaned)
- **Business problem:** Revenue reporting doesn't net returns, no customer segmentation exists,
  and product KPIs are contaminated by non-product rows (postage, discounts, manual charges).
- **KPIs:** Net Revenue, Return Rate %, Average Order Value, Customer Lifetime Value,
  Repeat Purchase Rate, Revenue by Country.

```mermaid
flowchart TD
    A[Raw Source<br/>UCI .xlsx] --> B[Staging / Cleaning Layer<br/>Python - pandas - clean.py]
    B --> C[Data Warehouse Layer<br/>PostgreSQL - Star Schema - schema.sql]
    C --> D[Real-Time Ingestion Layer<br/>stream_producer_psycopg2.py]
    D --> E[Semantic & Visualisation Layer<br/>Power BI - DirectQuery]

    style A fill:#1F3864,color:#fff
    style B fill:#2E75B6,color:#fff
    style C fill:#1F3864,color:#fff
    style D fill:#2E75B6,color:#fff
    style E fill:#F2C811,color:#000
```
## Live Dashboard Preview ![Dashboard](image.png)
