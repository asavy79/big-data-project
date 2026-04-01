# --------------------------------------------------------------------------
# Cloud SQL PostgreSQL 16 (pgvector supported natively)
# --------------------------------------------------------------------------

resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "google_sql_database_instance" "main" {
  name             = "jobmatch-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.main.id
      enable_private_path_for_google_cloud_services = true
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
    }
  }

  deletion_protection = true

  depends_on = [
    google_service_networking_connection.private_vpc,
    google_project_service.apis["sqladmin.googleapis.com"],
  ]
}

resource "google_sql_database" "jobdb" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}
