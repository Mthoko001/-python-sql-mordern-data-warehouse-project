/*
===============================================================================
 File: create_dwh.sql
 Project: Modern SQL Data Warehouse
 Author: Mthokozisi Seja

 Description:
     This script initializes the Data Warehouse by:

     1. Dropping the existing database (if it exists)
     2. Creating a new database (MthoDWH)
     3. Creating Medallion schemas (bronze, silver, gold)
     4. Creating the Silver layer Sales fact table

 WARNING:
     - This script will permanently delete the existing database.
     - All existing data will be lost.
     - Do NOT run in production unless intentional.
===============================================================================
*/

USE master;
GO

/* ===============================================================
   DROP DATABASE IF EXISTS
=============================================================== */

IF EXISTS (SELECT name FROM sys.databases WHERE name = 'MthoDWH')
BEGIN
    ALTER DATABASE MthoDWH SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE MthoDWH;
END
GO

/* ===============================================================
   CREATE DATABASE
=============================================================== */

CREATE DATABASE MthoDWH;
GO

USE MthoDWH;
GO

/* ===============================================================
   CREATE SCHEMAS (Medallion Architecture)
=============================================================== */

CREATE SCHEMA bronze;
GO

CREATE SCHEMA silver;
GO

CREATE SCHEMA gold;
GO

/* ===============================================================
   CREATE SALES FACT TABLE (Silver Layer)
=============================================================== */

CREATE TABLE bronze.fact_sales (
    order_number NVARCHAR(50) NOT NULL,
    product_key NVARCHAR(50) NOT NULL,
    customer_id INT NOT NULL,
    order_date DATE,
    ship_date DATE,
    due_date DATE,
    quantity INT,
    price DECIMAL(18,2),
    total_sales DECIMAL(18,2)
);

PRINT '========================================';
PRINT ' Database, Schemas, and Sales Table Created Successfully';
PRINT '========================================';
GO
