# --------------------------------------------------------------------------
# Cloud Run v2 services
# --------------------------------------------------------------------------

locals {
  ar_prefix = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

# ===================== Job Discovery Service ==============================

resource "google_cloud_run_v2_service" "job_discovery" {
  name     = "job-discovery-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.job_discovery.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [local.cloud_sql_connection_name]
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${local.ar_prefix}/job_discovery_service:${var.image_tag}"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name  = "DATABASE_URL"
        value = local.database_url
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "VERTEX_AI_LOCATION"
        value = var.region
      }
      env {
        name  = "EMBEDDING_MODEL"
        value = var.embedding_model
      }
      env {
        name  = "PUBSUB_TOPIC_INGESTED"
        value = google_pubsub_topic.jobs_ingested.name
      }
      env {
        name = "INTERNAL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.internal_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "RAPIDAPI_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.rapidapi_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.apis["run.googleapis.com"],
    google_secret_manager_secret_version.internal_api_key,
    google_secret_manager_secret_version.rapidapi_key,
  ]
}

# Allow unauthenticated access (LB handles external traffic)
resource "google_cloud_run_v2_service_iam_member" "job_discovery_public" {
  name     = google_cloud_run_v2_service.job_discovery.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}


# ===================== User Service =======================================

resource "google_cloud_run_v2_service" "user" {
  name     = "user-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.user_service.email

    # Always-on: pull subscriber for matches-calculated
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [local.cloud_sql_connection_name]
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${local.ar_prefix}/user_service:${var.image_tag}"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = false
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name  = "DATABASE_URL"
        value = local.database_url
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "VERTEX_AI_LOCATION"
        value = var.region
      }
      env {
        name  = "EMBEDDING_MODEL"
        value = var.embedding_model
      }
      env {
        name  = "PUBSUB_TOPIC_REFRESH"
        value = google_pubsub_topic.user_refresh_requested.name
      }
      env {
        name  = "PUBSUB_SUBSCRIPTION_MATCHES"
        value = google_pubsub_subscription.matches_calculated.name
      }
      env {
        name = "INTERNAL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.internal_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.apis["run.googleapis.com"],
    google_secret_manager_secret_version.internal_api_key,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "user_public" {
  name     = google_cloud_run_v2_service.user.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}


# ===================== Matching Service ===================================

resource "google_cloud_run_v2_service" "matching" {
  name     = "matching-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.matching.email

    # Always-on: pull subscribers for user-refresh-requested + jobs-ingested
    scaling {
      min_instance_count = 1
      max_instance_count = 3
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = "${local.ar_prefix}/matching_service:${var.image_tag}"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = false
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "JOB_SERVICE_URL"
        value = google_cloud_run_v2_service.job_discovery.uri
      }
      env {
        name  = "USER_SERVICE_URL"
        value = google_cloud_run_v2_service.user.uri
      }
      env {
        name  = "PUBSUB_SUB_REFRESH"
        value = google_pubsub_subscription.user_refresh_requested.name
      }
      env {
        name  = "PUBSUB_SUB_INGESTED"
        value = google_pubsub_subscription.jobs_ingested.name
      }
      env {
        name  = "PUBSUB_TOPIC_MATCHES"
        value = google_pubsub_topic.matches_calculated.name
      }
      env {
        name  = "MATCH_LIMIT"
        value = tostring(var.match_limit)
      }
      env {
        name = "INTERNAL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.internal_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.apis["run.googleapis.com"],
    google_secret_manager_secret_version.internal_api_key,
  ]
}
