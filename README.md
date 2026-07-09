# databricks-retail-lakehouse

Retail lakehouse on Databricks Free Edition, built from the UCI "Online Retail" dataset (UK online retailer transactions, Dec 2010–Dec 2011). Bronze → staging → marts pipeline, fully deployed and orchestrated as code — no manual clicks in the Databricks UI.

## Architecture

```
Online Retail.xlsx (Volume)
        |
        v
  bronze.online_retail        (notebook, PySpark, full overwrite)
        |
        v
  staging.stg_online_retail   (dbt, view - rename/type/surrogate key)
        |
        v
  marts.dim_products / dim_customers / dim_dates / fct_sales   (dbt, table)
```

Orchestrated as a single Databricks Job (`retail_pipeline`, two chained tasks), deployed via a Databricks Asset Bundle. Unity Catalog governance (catalog + grants) is managed via Terraform.

## Stack

- **Databricks Free Edition** - Unity Catalog, serverless compute, SQL Warehouse
- **Terraform** - Unity Catalog catalog + grants
- **Databricks Asset Bundles** - schemas, volume, job/task orchestration
- **PySpark** - bronze ingestion notebook
- **dbt-databricks** - staging + marts transformations, with tests

## Repo structure

```
terraform/                              Unity Catalog catalog + grants
orchestration/databricks_bundle/        Bundle resources (schemas, volume, job)
notebooks/                              Bronze ingestion + dbt runner notebooks
dbt/                                    dbt project (staging/marts models, tests)
data/raw/                               Source dataset
```

## Running it

Requires a Databricks workspace, the [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) configured (`databricks configure --token`), and [Terraform](https://developer.hashicorp.com/terraform/install).

```powershell
# 1. Unity Catalog governance
cd terraform
terraform init
terraform apply

# 2. Deploy schemas, volume, job
cd ..
databricks bundle deploy

# 3. Upload the dataset to the volume (one-off)
databricks fs cp "data/raw/Online Retail.xlsx" "dbfs:/Volumes/retail/bronze/raw_landing/Online Retail.xlsx"

# 4. Run the pipeline (bronze -> dbt staging -> dbt marts)
databricks bundle run bronze_ingestion
```

## Status

Bronze -> staging -> marts pipeline is fully working end-to-end. In progress: a text-to-SQL feature over the marts using Databricks AI (`ai_query()`), and a recorded demo.
