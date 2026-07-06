# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze — Online Retail ingestion
# MAGIC
# MAGIC Reads `Online Retail.xlsx` from a Unity Catalog Volume and writes it to a
# MAGIC bronze Delta table, with an explicit schema faithful to the source plus
# MAGIC two technical ingestion columns. No business rules here — that stays the
# MAGIC responsibility of the dbt staging models.
# MAGIC
# MAGIC The source file is a one-off export (not a stream of files), so this
# MAGIC table is fully reloaded on every run (`overwrite`) rather than ingested
# MAGIC incrementally via Auto Loader.

# COMMAND ----------

# MAGIC %pip install openpyxl

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("raw_path", "/Volumes/retail/bronze/raw_landing/Online Retail.xlsx")
dbutils.widgets.text("catalog", "retail")
dbutils.widgets.text("bronze_schema", "bronze")
dbutils.widgets.text("table_name", "online_retail")

raw_path = dbutils.widgets.get("raw_path")
catalog = dbutils.widgets.get("catalog")
bronze_schema = dbutils.widgets.get("bronze_schema")
table_name = dbutils.widgets.get("table_name")

target_table = f"{catalog}.{bronze_schema}.{table_name}"

# COMMAND ----------

import os

import pandas as pd
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
    TimestampType,
    IntegerType,
    DoubleType,
)
from pyspark.sql import functions as F

# InvoiceNo/CustomerID as string: faithful representation (avoids the ".0"
# float artifact on CustomerID, and InvoiceNo carries a "C" prefix for
# cancellations) — not a business rule, just a typing choice.
BRONZE_SCHEMA = StructType(
    [
        StructField("InvoiceNo", StringType(), nullable=False),
        StructField("StockCode", StringType(), nullable=False),
        StructField("Description", StringType(), nullable=True),
        StructField("Quantity", IntegerType(), nullable=False),
        StructField("InvoiceDate", TimestampType(), nullable=False),
        StructField("UnitPrice", DoubleType(), nullable=False),
        StructField("CustomerID", StringType(), nullable=True),
        StructField("Country", StringType(), nullable=True),
    ]
)

# COMMAND ----------

if not os.path.exists(raw_path):
    raise FileNotFoundError(f"Source file not found: {raw_path}")

pdf = pd.read_excel(raw_path)

missing_columns = set(f.name for f in BRONZE_SCHEMA.fields) - set(pdf.columns)
if missing_columns:
    raise ValueError(
        f"Columns missing from {raw_path} vs. the expected bronze schema: {sorted(missing_columns)}"
    )

# COMMAND ----------

# Align pandas types with the target schema before the Spark conversion, so
# spark.createDataFrame doesn't have to infer anything (fragile on nulls/mixed types).
pdf["InvoiceNo"] = pdf["InvoiceNo"].astype(str)
pdf["StockCode"] = pdf["StockCode"].astype(str)
pdf["Description"] = pdf["Description"].apply(lambda v: None if pd.isna(v) else str(v))
pdf["CustomerID"] = pdf["CustomerID"].apply(lambda v: None if pd.isna(v) else str(int(v)))
pdf["Quantity"] = pdf["Quantity"].astype("int32")
pdf["UnitPrice"] = pdf["UnitPrice"].astype("float64")

df = spark.createDataFrame(pdf[[f.name for f in BRONZE_SCHEMA.fields]], schema=BRONZE_SCHEMA)

df = df.withColumn("_ingested_at", F.current_timestamp()).withColumn("_source_file", F.lit(raw_path))

# COMMAND ----------

row_count = df.count()
if row_count == 0:
    raise ValueError(f"{raw_path} produced no rows — ingestion aborted.")

(
    df.write.mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)

print(f"{row_count} rows written to {target_table}")

# COMMAND ----------

display(spark.table(target_table).limit(20))
