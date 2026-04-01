variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone (used by Cloud SQL)"
  type        = string
  default     = "us-central1-a"
}

variable "embedding_model" {
  description = "Vertex AI embedding model name"
  type        = string
  default     = "text-embedding-004"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "jobdb"
}

variable "db_user" {
  description = "PostgreSQL application user"
  type        = string
  default     = "jobmatch"
}

variable "internal_api_key" {
  description = "Shared secret for service-to-service auth"
  type        = string
  sensitive   = true
}

variable "rapidapi_key" {
  description = "RapidAPI key for JSearch"
  type        = string
  sensitive   = true
}

variable "frontend_bucket_name" {
  description = "GCS bucket name for frontend static assets (must be globally unique)"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag for Cloud Run services"
  type        = string
  default     = "latest"
}

variable "match_limit" {
  description = "Maximum number of job matches returned per user"
  type        = number
  default     = 10
}
