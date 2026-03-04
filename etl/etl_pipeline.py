"""
===============================================================================
This module implements the end-to-end ETL workflow for the Modern Data
Warehouse project. It extracts CRM sales data from CSV, performs data quality
checks and transformations, resolves duplicates, and batch loads the cleansed
data into the SQL Server Bronze layer using SQLAlchemy and pyodbc.
===============================================================================
"""
# etl_pipeline.py

import pandas as pd
import logging
from sqlalchemy import text
from database.db_connection import get_sql_engine

# -------------------------------
# Logging setup
# -------------------------------
logging.basicConfig(
    filename='logs/etl_process.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

BATCH_SIZE = 1000  # Controls bulk insert performance

# -------------------------------
# Extract
# -------------------------------
def extract_data(file_path: str) -> pd.DataFrame | None:
    """Extract sales data from CSV source."""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Data extracted from {file_path}")
        print("✅ Data extracted successfully.")
        return df
    except Exception as e:
        logging.error(f"Extraction error: {e}")
        print(f"❌ Data extraction failed: {e}")
        return None


# -------------------------------
# Inspect Columns
# -------------------------------
def inspect_columns(df: pd.DataFrame) -> None:
    """Quick inspection of key numeric columns."""
    print("\n===== Inspecting Columns =====")
    print(df[['sls_quantity', 'sls_price']].dtypes)
    print(df[['sls_quantity', 'sls_price']].head(5))
    print("==============================\n")


# -------------------------------
# Primary Key Check
# -------------------------------
def check_primary_key(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """Check nulls and duplicates in primary key."""
    null_count = df[key_column].isnull().sum()
    duplicate_count = df[key_column].duplicated().sum()

    print(f"Primary Key: {key_column}")
    print(f"Nulls: {null_count}")
    print(f"Duplicates: {duplicate_count}")

    logging.info(
        f"PK check — nulls: {null_count}, duplicates: {duplicate_count}"
    )
    return df


# -------------------------------
# Resolve Duplicates
# -------------------------------
def resolve_duplicates(df: pd.DataFrame, key_column: str, date_column: str) -> pd.DataFrame:
    """Keep the latest record per business key."""
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    before_count = len(df)

    df = (
        df.sort_values(by=date_column, ascending=False)
        .drop_duplicates(subset=[key_column], keep="first")
    )

    after_count = len(df)

    print(f"Rows before duplicate resolution: {before_count}")
    print(f"Rows after duplicate resolution: {after_count}")

    logging.info("Duplicates resolved using latest-date rule")
    return df


# -------------------------------
# Transform
# -------------------------------
def transform_data(df: pd.DataFrame) -> pd.DataFrame | None:
    """Clean and standardize data for warehouse loading."""
    try:
        # Convert dates
        df['sls_order_dt'] = pd.to_datetime(df['sls_order_dt'], errors='coerce')
        df['sls_ship_dt'] = pd.to_datetime(df['sls_ship_dt'], errors='coerce')
        df['sls_due_dt'] = pd.to_datetime(df['sls_due_dt'], errors='coerce')

        # Convert numerics
        df['sls_quantity'] = pd.to_numeric(df['sls_quantity'], errors='coerce')
        df['sls_price'] = pd.to_numeric(df['sls_price'], errors='coerce')

        # Business metric
        df['total_sales'] = df['sls_quantity'] * df['sls_price']

        # 🔥 Convert to Python-native types (important for pyodbc)
        df['sls_quantity'] = df['sls_quantity'].astype('Int64').astype(object)
        df['sls_price'] = df['sls_price'].astype(float)
        df['total_sales'] = df['total_sales'].astype(float)

        df['sls_order_dt'] = df['sls_order_dt'].dt.to_pydatetime()
        df['sls_ship_dt'] = df['sls_ship_dt'].dt.to_pydatetime()
        df['sls_due_dt'] = df['sls_due_dt'].dt.to_pydatetime()

        # Replace NaN/NaT with None for SQL Server
        df = df.where(pd.notnull(df), None)

        logging.info("Transformation successful")
        print("✅ Data transformation successful.")
        return df

    except Exception as e:
        logging.error(f"Transform error: {e}")
        print(f"❌ Transformation failed: {e}")
        return None


# -------------------------------
# Batch Load to SQL Server
# -------------------------------
def load_to_sql(df: pd.DataFrame) -> None:
    """Batch insert data into bronze.sales_details."""
    engine = get_sql_engine()
    if engine is None:
        print("❌ Engine not created.")
        return

    total_rows = len(df)
    print(f"Rows about to load: {total_rows}")

    insert_stmt = text("""
        INSERT INTO bronze.sales_details
        (sls_ord_num, sls_order_dt, sls_ship_dt, sls_due_dt,
         sls_quantity, sls_price, total_sales)
        VALUES
        (:sls_ord_num, :sls_order_dt, :sls_ship_dt, :sls_due_dt,
         :sls_quantity, :sls_price, :total_sales)
    """)

    data = df.to_dict(orient="records")

    with engine.begin() as conn:
        for i in range(0, total_rows, BATCH_SIZE):
            batch = data[i:i + BATCH_SIZE]
            conn.execute(insert_stmt, batch)
            print(f"✅ Loaded batch {i//BATCH_SIZE + 1}")

    logging.info("Batch load completed")
    print("🎉 All batches loaded into bronze.sales_details")


# -------------------------------
# Summary
# -------------------------------
def summary_report(df: pd.DataFrame) -> None:
    """Print ETL summary statistics."""
    print("\n===== ETL Summary =====")
    print(f"Total rows processed: {len(df)}")
    print("Nulls per column:")
    print(df.isnull().sum())
    print("=======================\n")


# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":

    file_path = r"datasets/source_crm/sales_details.csv"

    df = extract_data(file_path)

    if df is not None:
        inspect_columns(df)
        df = check_primary_key(df, "sls_ord_num")
        df = resolve_duplicates(df, "sls_ord_num", "sls_order_dt")
        df_transformed = transform_data(df)

        if df_transformed is not None:
            load_to_sql(df_transformed)
            summary_report(df_transformed)
            print("🚀 ETL process completed successfully.")
