# Databricks notebook source
# MAGIC %md
# MAGIC # dbt transform — staging + marts
# MAGIC
# MAGIC Runs `dbt run` and `dbt test` against the dbt project synced by the
# MAGIC Databricks Asset Bundle. Uses the current job run's own identity/token
# MAGIC (via the notebook context) to authenticate, so no stored credential is
# MAGIC needed — same reasoning as the native `dbt_task`, which is unavailable
# MAGIC on this workspace (fails with an unrelated cluster-launch error).

# COMMAND ----------

# MAGIC %pip install dbt-databricks==1.8.3

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("dbt_project_dir", "")
dbutils.widgets.text("warehouse_http_path", "")
dbutils.widgets.text("catalog", "retail")

dbt_project_dir = dbutils.widgets.get("dbt_project_dir")
warehouse_http_path = dbutils.widgets.get("warehouse_http_path")
catalog = dbutils.widgets.get("catalog")

# COMMAND ----------

import os
import subprocess

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
host = ctx.apiUrl().get()
token = ctx.apiToken().get()

profiles_dir = "/tmp/dbt_profiles"
os.makedirs(profiles_dir, exist_ok=True)

with open(f"{profiles_dir}/profiles.yml", "w") as f:
    f.write(f"""\
retail_lakehouse:
  target: job
  outputs:
    job:
      type: databricks
      catalog: {catalog}
      schema: default
      host: {host}
      http_path: {warehouse_http_path}
      token: {token}
      threads: 4
""")

# COMMAND ----------

env = os.environ.copy()
env["DBT_PROFILES_DIR"] = profiles_dir

for command in ["dbt run", "dbt test"]:
    result = subprocess.run(
        command.split(),
        cwd=dbt_project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"'{command}' failed with exit code {result.returncode}")
