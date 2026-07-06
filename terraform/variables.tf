variable "catalog_name" {
  description = "Unity Catalog catalog holding every schema (bronze/staging/marts) for this project."
  type        = string
  default     = "retail"
}

variable "managed_storage_root" {
  description = "Base URL of the workspace's Databricks-managed UC storage (get it with `databricks external-locations list`)."
  type        = string
}

variable "owner_email" {
  description = "Email of the sole workspace user granted privileges on project-managed Unity Catalog objects."
  type        = string
}
