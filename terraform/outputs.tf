output "catalog_name" {
  description = "Name of the Unity Catalog catalog created for this project."
  value       = databricks_catalog.retail.name
}
