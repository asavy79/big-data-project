terraform {
  backend "gcs" {
    bucket = "jobmatch-tfstate"
    prefix = "terraform/state"
  }
}
