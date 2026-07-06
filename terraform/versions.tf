terraform {
  required_version = ">= 1.13.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.50.0, < 2.0.0"
    }
  }
}

# Auth via ~/.databrickscfg or DATABRICKS_HOST/DATABRICKS_TOKEN — no secrets in repo.
provider "databricks" {}
