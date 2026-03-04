# test_insert.py

from db_connection import get_sql_engine
from datetime import datetime
from sqlalchemy import text  # <-- IMPORTANT

# Get SQLAlchemy engine
engine = get_sql_engine()

# Prepare one row as a dictionary
row = {
    "sls_ord_num": "TEST456",
    "sls_order_dt": datetime.now(),
    "sls_ship_dt": datetime.now(),
    "sls_due_dt": datetime.now(),
    "sls_quantity": 1,
    "sls_price": 100.0,
    "total_sales": 100.0
}

# Insert row using sqlalchemy.text()
with engine.begin() as conn:
    conn.execute(
        text("""
        INSERT INTO bronze.sales_details
        (sls_ord_num, sls_order_dt, sls_ship_dt, sls_due_dt, sls_quantity, sls_price, total_sales)
        VALUES (:sls_ord_num, :sls_order_dt, :sls_ship_dt, :sls_due_dt, :sls_quantity, :sls_price, :total_sales)
        """),
        [row]  # list of dictionaries
    )

print("✅ Test row inserted successfully.")