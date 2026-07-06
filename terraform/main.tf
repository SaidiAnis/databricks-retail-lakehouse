# Only the catalog lives here; schemas/volumes are Bundle resources (Bundles can't manage catalogs).
# Free Edition blocks catalog creation via API — created once via the UI, then `terraform import`ed here.
resource "databricks_catalog" "retail" {
  name         = var.catalog_name
  comment      = "Retail lakehouse (Online Retail dataset): bronze/staging/marts schemas."
  storage_root = var.managed_storage_root

  properties = {
    project = "databricks-retail-lakehouse"
  }
}

# Authoritative: replaces the "account users" ALL_PRIVILEGES grant made via the UI with a scoped one.
resource "databricks_grants" "retail" {
  catalog = databricks_catalog.retail.name

  grant {
    principal  = var.owner_email
    privileges = ["ALL_PRIVILEGES"]
  }
}
