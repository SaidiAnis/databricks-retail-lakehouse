# databricks-retail-lakehouse

A retail lakehouse on Databricks, built end-to-end from the UCI "Online Retail" dataset (UK online retailer transactions, Dec 2010–Dec 2011): bronze → staging → marts pipeline, plus a text-to-SQL chat app over the marts.

Everything — Unity Catalog governance, schema/job deployment, transformations — is defined as code and deployed via CLI. No manual configuration in the Databricks UI, aside from one Free Edition restriction noted below.

## Architecture

![Architecture diagram](docs/Diagram_retail.png)

| Layer | Built by | What it does |
|---|---|---|
| Volume | Databricks Asset Bundle | Landing zone for the raw file — no processing |
| Bronze | Notebook, PySpark | Raw ingestion, explicit schema, no business rules |
| Staging | dbt (view) | Rename, type, surrogate key |
| Marts | dbt (table) | Star schema — 3 dimensions + 1 fact table, tested |
| App | FastAPI + `ai_query` | Natural language queries over the marts, read-only |

**Orchestration:** one Databricks Job, `retail_pipeline`, with two chained tasks (bronze notebook, then `dbt run` + `dbt test`), deployed via a Databricks Asset Bundle and triggered with a single command.

**Governance:** Terraform owns the Unity Catalog catalog (`retail`) and its grants — the one Unity Catalog object the Bundle can't manage, since catalog creation is account-level, not workspace-level.

## Stack

| | |
|---|---|
| Platform | Databricks Free Edition — Unity Catalog, serverless compute, SQL Warehouse, Foundation Model APIs |
| Governance | Terraform |
| Deployment | Databricks Asset Bundles |
| Ingestion | PySpark |
| Transformation | dbt-databricks |
| AI feature | FastAPI, `ai_query()` (Llama 3.1, served by Databricks) |

## Repo structure

```
terraform/                              Unity Catalog catalog + grants
orchestration/databricks_bundle/        Bundle resources (schemas, volume, job)
notebooks/                              Bronze ingestion + dbt runner notebooks
dbt/                                    dbt project (staging/marts models, tests)
app/                                    Text-to-SQL chat app (FastAPI + static frontend)
data/raw/                               Source dataset
```

## Running it

### Pipeline

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

### Text-to-SQL chat app (local)

```powershell
pip install -r requirements.txt
$env:DATABRICKS_HOST = "<your workspace URL>"
$env:DATABRICKS_HTTP_PATH = "<your SQL Warehouse HTTP path>"
$env:DATABRICKS_TOKEN = "<your token>"
cd app
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

## How the text-to-SQL feature works

1. The question, together with a description of the `retail.marts` schema, is sent to a Databricks-hosted LLM via `ai_query()`.
2. The generated SQL is validated in Python before anything runs: single statement, `SELECT` only, no destructive keywords, restricted to the 4 marts tables.
3. Only a query that passes validation is executed on the SQL Warehouse — the LLM never gets direct database access.

## Notes

- Catalog creation is blocked via API/Terraform on Free Edition ("Please use the UI to create a catalog with Default Storage") — the catalog was created once via the UI, then `terraform import`ed, so every change since is code-managed.
- This workspace only supports serverless compute; the native Databricks `dbt_task` job type doesn't work here (fails on cluster launch), so the dbt step runs from a plain notebook task instead (`notebooks/02_dbt_transform.py`).

## Status

Bronze → staging → marts pipeline, orchestration, and the text-to-SQL app are all working end-to-end. Remaining: a recorded demo.
