# --------------------------------------------------------------------------
# GCS bucket for frontend static assets (React SPA)
# --------------------------------------------------------------------------

resource "google_storage_bucket" "frontend" {
  name     = var.frontend_bucket_name
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket_iam_member" "frontend_public" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
