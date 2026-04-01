# --------------------------------------------------------------------------
# Pub/Sub topics and pull subscriptions
# --------------------------------------------------------------------------

resource "google_pubsub_topic" "user_refresh_requested" {
  name = "user-refresh-requested"

  depends_on = [google_project_service.apis["pubsub.googleapis.com"]]
}

resource "google_pubsub_topic" "matches_calculated" {
  name = "matches-calculated"

  depends_on = [google_project_service.apis["pubsub.googleapis.com"]]
}

resource "google_pubsub_topic" "jobs_ingested" {
  name = "jobs-ingested"

  depends_on = [google_project_service.apis["pubsub.googleapis.com"]]
}

# Pull subscriptions ---------------------------------------------------------

resource "google_pubsub_subscription" "user_refresh_requested" {
  name  = "user-refresh-requested-sub"
  topic = google_pubsub_topic.user_refresh_requested.id

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s" # 7 days
  retain_acked_messages      = false

  expiration_policy {
    ttl = "" # never expires
  }
}

resource "google_pubsub_subscription" "matches_calculated" {
  name  = "matches-calculated-sub"
  topic = google_pubsub_topic.matches_calculated.id

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
  retain_acked_messages      = false

  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "jobs_ingested" {
  name  = "jobs-ingested-sub"
  topic = google_pubsub_topic.jobs_ingested.id

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
  retain_acked_messages      = false

  expiration_policy {
    ttl = ""
  }
}
