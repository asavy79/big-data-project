terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

locals {
  services = {
    job_discovery = "job-discovery-service"
    user          = "user-service"
    matching      = "matching-service"
  }

  cloud_sql_connection_name = "${var.project_id}:${var.region}:${google_sql_database_instance.main.name}"

  database_url = "postgresql+asyncpg://${google_sql_user.app.name}:${random_password.db_password.result}@/${google_sql_database.jobdb.name}?host=/cloudsql/${local.cloud_sql_connection_name}"

  common_env = {
    GCP_PROJECT_ID    = var.project_id
    VERTEX_AI_LOCATION = var.region
    EMBEDDING_MODEL   = var.embedding_model
  }
}
