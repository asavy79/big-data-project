# --------------------------------------------------------------------------
# External HTTP Load Balancer + Cloud CDN
#
# Routes:
#   /*            → GCS bucket (frontend, CDN-cached)
#   /api/user/*   → Cloud Run user-service
#   /api/jobs/*   → Cloud Run job-discovery-service
#
# To upgrade to HTTPS later, add:
#   google_compute_managed_ssl_certificate + google_compute_target_https_proxy
# --------------------------------------------------------------------------

resource "google_compute_global_address" "lb" {
  name = "jobmatch-lb-ip"

  depends_on = [google_project_service.apis["compute.googleapis.com"]]
}

# ----- Backend: GCS bucket (frontend) with CDN ----------------------------

resource "google_compute_backend_bucket" "frontend" {
  name        = "jobmatch-frontend-backend"
  bucket_name = google_storage_bucket.frontend.name
  enable_cdn  = true

  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 3600
    max_ttl                      = 86400
    negative_caching             = true
    serve_while_stale            = 86400
    signed_url_cache_max_age_sec = 0
  }
}

# ----- Backend: Cloud Run serverless NEGs ---------------------------------

resource "google_compute_region_network_endpoint_group" "user_service" {
  name                  = "user-service-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.user.name
  }
}

resource "google_compute_region_network_endpoint_group" "job_discovery" {
  name                  = "job-discovery-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.job_discovery.name
  }
}

resource "google_compute_backend_service" "user_service" {
  name                  = "user-service-backend"
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 300
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.user_service.id
  }
}

resource "google_compute_backend_service" "job_discovery" {
  name                  = "job-discovery-backend"
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 30
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.job_discovery.id
  }
}

# ----- URL Map ------------------------------------------------------------

resource "google_compute_url_map" "main" {
  name            = "jobmatch-url-map"
  default_service = google_compute_backend_bucket.frontend.id

  host_rule {
    hosts        = ["*"]
    path_matcher = "api"
  }

  path_matcher {
    name            = "api"
    default_service = google_compute_backend_bucket.frontend.id

    path_rule {
      paths   = ["/api/user/*", "/api/user/ws"]
      service = google_compute_backend_service.user_service.id
    }

    path_rule {
      paths   = ["/api/jobs/*"]
      service = google_compute_backend_service.job_discovery.id
    }
  }
}

# ----- HTTP Proxy + Forwarding Rule ---------------------------------------

resource "google_compute_target_http_proxy" "main" {
  name    = "jobmatch-http-proxy"
  url_map = google_compute_url_map.main.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "jobmatch-http-rule"
  target                = google_compute_target_http_proxy.main.id
  port_range            = "80"
  ip_address            = google_compute_global_address.lb.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}
