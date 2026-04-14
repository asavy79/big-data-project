#!/bin/sh
set -e
# Cloud Run sets PORT to the configured container port; default matches Dockerfile.
PORT="${PORT:-8080}"
sed -i "s/listen 8080;/listen ${PORT};/" /etc/nginx/conf.d/default.conf
