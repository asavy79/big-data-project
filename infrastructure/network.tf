# --------------------------------------------------------------------------
# VPC + Private Service Access (Cloud SQL) + Serverless VPC Connector
# --------------------------------------------------------------------------

resource "google_compute_network" "main" {
  name                    = "jobmatch-vpc"
  auto_create_subnetworks = false

  depends_on = [google_project_service.apis["compute.googleapis.com"]]
}

resource "google_compute_subnetwork" "main" {
  name          = "jobmatch-subnet"
  network       = google_compute_network.main.id
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
}

# Private IP range reserved for Cloud SQL via Private Service Access
resource "google_compute_global_address" "private_ip_range" {
  name          = "jobmatch-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id

  depends_on = [google_project_service.apis["servicenetworking.googleapis.com"]]
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# Serverless VPC Access connector — Cloud Run uses this to reach Cloud SQL
resource "google_vpc_access_connector" "main" {
  name          = "jobmatch-connector"
  region        = var.region
  network       = google_compute_network.main.name
  ip_cidr_range = "10.8.0.0/28"
  min_instances = 2
  max_instances = 3

  depends_on = [google_project_service.apis["vpcaccess.googleapis.com"]]
}
