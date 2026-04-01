# --------------------------------------------------------------------------
# Secret Manager — sensitive values referenced by Cloud Run as env secrets
# --------------------------------------------------------------------------

resource "google_secret_manager_secret" "db_password" {
  secret_id = "jobmatch-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "internal_api_key" {
  secret_id = "jobmatch-internal-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

resource "google_secret_manager_secret_version" "internal_api_key" {
  secret      = google_secret_manager_secret.internal_api_key.id
  secret_data = var.internal_api_key
}

resource "google_secret_manager_secret" "rapidapi_key" {
  secret_id = "jobmatch-rapidapi-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

resource "google_secret_manager_secret_version" "rapidapi_key" {
  secret      = google_secret_manager_secret.rapidapi_key.id
  secret_data = var.rapidapi_key
}
