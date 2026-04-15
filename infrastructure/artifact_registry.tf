resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "service-repo"
  format        = "DOCKER"
  description   = "Docker images for JobMatch Cloud Run services"

  depends_on = [google_project_service.apis["artifactregistry.googleapis.com"]]
}
