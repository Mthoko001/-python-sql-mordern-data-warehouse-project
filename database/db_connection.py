"""
db_connection.py
---------------------------------
Centralized SQL Server connection manager for the Modern Data Warehouse.

Responsibilities:
- Create SQLAlchemy engine
- Manage ODBC connection string
- Provide reusable database connectivity
- Enable fast_executemany for bulk loads
-HERE I Have been using my local SSMS
"""

import os
import urllib.parse
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


# =========================
# Environment Configuration
# =========================
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_SERVER = os.getenv("DB_SERVER", r"NONHLEMIYA\SQLEXPRESS")
DB_DATABASE = os.getenv("DB_DATABASE", "ModernDWH")
DB_TRUSTED = os.getenv("DB_TRUSTED", "yes")  # yes/no


# =========================
# Engine Factory
# =========================
def get_sql_engine(echo: bool = False) -> Engine:
    """
    Create and return a SQLAlchemy engine for SQL Server.

    Features:
    - Windows Trusted Connection
    - fast_executemany enabled
    - Connection pooling
    - URL-safe ODBC string
    """

    try:
        odbc_str = (
            f"DRIVER={{{DB_DRIVER}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"Trusted_Connection={DB_TRUSTED};"
            "TrustServerCertificate=yes;"
        )

        connect_str = urllib.parse.quote_plus(odbc_str)

        engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={connect_str}",
            echo=echo,
            fast_executemany=True,  # 🚀 critical for bulk insert performance
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            future=True,
        )

        logger.info("✅ SQLAlchemy engine created successfully")
        return engine

    except Exception as e:
        logger.exception("❌ Failed to create SQL engine")
        raise


# =========================
# Connection Test Utility
# =========================
def test_connection() -> bool:
    """
    Test database connectivity.

    Returns:
        bool: True if connection succeeds
    """
    try:
        engine = get_sql_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection test successful")
        return True
    except Exception:
        logger.exception("❌ Database connection test failed")
        return False


# =========================
# Script Entry Point
# =========================
if __name__ == "__main__":
    success = test_connection()
    if success:
        print("🎉 Database connection OK")
    else:
        print("💥 Database connection FAILED")
