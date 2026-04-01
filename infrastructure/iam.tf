# --------------------------------------------------------------------------
# Service accounts — one per Cloud Run service (least-privilege)
# --------------------------------------------------------------------------

resource "google_service_account" "job_discovery" {
  account_id   = "job-discovery-sa"
  display_name = "Job Discovery Service"
}

resource "google_service_account" "user_service" {
  account_id   = "user-service-sa"
  display_name = "User Service"
}

resource "google_service_account" "matching" {
  account_id   = "matching-service-sa"
  display_name = "Matching Service"
}

# --------------------------------------------------------------------------
# IAM bindings — project-level roles
# --------------------------------------------------------------------------

# Cloud SQL client (user + job-discovery need DB access)
resource "google_project_iam_member" "job_discovery_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.job_discovery.email}"
}

resource "google_project_iam_member" "user_service_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.user_service.email}"
}

# Vertex AI (embedding generation)
resource "google_project_iam_member" "job_discovery_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.job_discovery.email}"
}

resource "google_project_iam_member" "user_service_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.user_service.email}"
}

# Pub/Sub publisher
resource "google_project_iam_member" "job_discovery_pubsub_publish" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.job_discovery.email}"
}

resource "google_project_iam_member" "user_service_pubsub_publish" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.user_service.email}"
}

resource "google_project_iam_member" "matching_pubsub_publish" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.matching.email}"
}

# Pub/Sub subscriber
resource "google_project_iam_member" "user_service_pubsub_subscribe" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.user_service.email}"
}

resource "google_project_iam_member" "matching_pubsub_subscribe" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.matching.email}"
}

# Secret Manager access
resource "google_project_iam_member" "job_discovery_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.job_discovery.email}"
}

resource "google_project_iam_member" "user_service_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.user_service.email}"
}

resource "google_project_iam_member" "matching_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.matching.email}"
}
