"""Core text-to-SQL logic: prompt the LLM, validate the generated SQL, run it.

Runs locally (Streamlit UI) but generation and execution both happen on
Databricks: `ai_query` calls a Foundation Model API endpoint, and the
generated SQL runs on the SQL Warehouse — this module is just a client.
"""

import os
import re

from databricks import sql

SCHEMA_CONTEXT = """
retail.marts.dim_products (product_code STRING, product_description STRING)
retail.marts.dim_customers (customer_id STRING, country STRING, first_order_at TIMESTAMP, last_order_at TIMESTAMP)
retail.marts.dim_dates (date_day DATE, year INT, month INT, month_name STRING, quarter INT, day_of_week INT, day_name STRING, is_weekend BOOLEAN)
retail.marts.fct_sales (invoice_line_id STRING, invoice_id STRING, invoice_at TIMESTAMP, date_day DATE, customer_id STRING, product_code STRING, quantity INT, unit_price DOUBLE, line_amount DOUBLE, is_cancellation BOOLEAN)
"""

PROMPT_TEMPLATE = """You are a SQL assistant for a Databricks lakehouse. Given the schema below, \
write a single Databricks SQL SELECT query that answers the question. Only use the tables and \
columns listed. Reply with the SQL query only, no explanation, no markdown formatting.

Schema:
{schema}

Question: {question}

SQL:"""

DEFAULT_MODEL_ENDPOINT = "databricks-meta-llama-3-1-8b-instruct"

ALLOWED_TABLES = {
    "retail.marts.dim_products",
    "retail.marts.dim_customers",
    "retail.marts.dim_dates",
    "retail.marts.fct_sales",
}
_UNQUALIFIED_TABLE_NAMES = {t.rsplit(".", 1)[-1] for t in ALLOWED_TABLES}
BLOCKED_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter",
    "truncate", "create", "grant", "revoke", "merge",
)


def _connection():
    return sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )


def generate_sql(question: str, model_endpoint: str = DEFAULT_MODEL_ENDPOINT) -> str:
    prompt = PROMPT_TEMPLATE.format(schema=SCHEMA_CONTEXT, question=question)
    with _connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT ai_query(%(model)s, %(prompt)s) AS sql_text",
            {"model": model_endpoint, "prompt": prompt},
        )
        raw = cursor.fetchone()[0]

    cleaned = raw.strip().strip("`")
    if cleaned.lower().startswith("sql\n"):
        cleaned = cleaned[4:]
    return cleaned.strip()


def validate_sql(generated_sql: str) -> str:
    normalized = generated_sql.strip().rstrip(";")

    if ";" in normalized:
        raise ValueError("Generated SQL must be a single statement.")

    if not normalized.lower().lstrip().startswith("select"):
        raise ValueError(f"Generated SQL is not a SELECT statement: {generated_sql}")

    lowered = normalized.lower()
    if any(re.search(rf"\b{kw}\b", lowered) for kw in BLOCKED_KEYWORDS):
        raise ValueError(f"Generated SQL contains a blocked keyword: {generated_sql}")

    referenced_tables = set(re.findall(r"(?:from|join)\s+([a-zA-Z0-9_.]+)", lowered))
    if not referenced_tables <= (ALLOWED_TABLES | _UNQUALIFIED_TABLE_NAMES):
        raise ValueError(f"Generated SQL references tables outside retail.marts: {referenced_tables}")

    return normalized


def run_query(sql_text: str):
    with _connection() as conn, conn.cursor() as cursor:
        cursor.execute(sql_text)
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
    return columns, rows


def ask(question: str, model_endpoint: str = DEFAULT_MODEL_ENDPOINT):
    """Full flow: generate SQL, validate it, run it. Raises ValueError if unsafe."""
    generated = generate_sql(question, model_endpoint)
    validated = validate_sql(generated)
    columns, rows = run_query(validated)
    return validated, columns, rows
