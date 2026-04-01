output "load_balancer_ip" {
  description = "External IP of the HTTP load balancer"
  value       = google_compute_global_address.lb.address
}

output "frontend_bucket" {
  description = "GCS bucket name for frontend assets"
  value       = google_storage_bucket.frontend.name
}

output "cloud_run_urls" {
  description = "Cloud Run service URLs"
  value = {
    job_discovery = google_cloud_run_v2_service.job_discovery.uri
    user          = google_cloud_run_v2_service.user.uri
    matching      = google_cloud_run_v2_service.matching.uri
  }
}

output "artifact_registry" {
  description = "Artifact Registry repository path for docker push"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name (for Cloud SQL Auth Proxy)"
  value       = local.cloud_sql_connection_name
}

output "cloud_sql_instance_ip" {
  description = "Cloud SQL private IP"
  value       = google_sql_database_instance.main.private_ip_address
}
