#!/bin/bash
# Download CDN Assets Script
# This script downloads all required CDN assets locally

cd "$(dirname "$0")"

echo "Downloading CDN assets..."

# Bootstrap 5.3.2
echo "Downloading Bootstrap 5.3.2..."
curl -o static/css/vendor/bootstrap/bootstrap.min.css \
  https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css
curl -o static/css/vendor/bootstrap/bootstrap.min.css.map \
  https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css.map
curl -o static/js/vendor/bootstrap/bootstrap.bundle.min.js \
  https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js
curl -o static/js/vendor/bootstrap/bootstrap.bundle.min.js.map \
  https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js.map

# jQuery 3.7.1
echo "Downloading jQuery 3.7.1..."
curl -o static/js/vendor/jquery/jquery-3.7.1.min.js \
  https://code.jquery.com/jquery-3.7.1.min.js

# RemixIcon 3.5.0
echo "Downloading RemixIcon 3.5.0..."
curl -o static/fonts/remixicon/remixicon.css \
  https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css
curl -o static/fonts/remixicon/remixicon.woff2 \
  https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.woff2
curl -o static/fonts/remixicon/remixicon.woff \
  https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.woff

# Bootstrap Icons 1.11.2
echo "Downloading Bootstrap Icons 1.11.2..."
curl -o static/fonts/bootstrap-icons/bootstrap-icons.css \
  https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css
curl -o static/fonts/bootstrap-icons/bootstrap-icons.woff2 \
  https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/fonts/bootstrap-icons.woff2
curl -o static/fonts/bootstrap-icons/bootstrap-icons.woff \
  https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/fonts/bootstrap-icons.woff

# ApexCharts 3.45.0
echo "Downloading ApexCharts 3.45.0..."
curl -o static/js/vendor/apexcharts/apexcharts.min.js \
  https://cdn.jsdelivr.net/npm/apexcharts@3.45.0/dist/apexcharts.min.js
curl -o static/css/vendor/apexcharts/apexcharts.css \
  https://cdn.jsdelivr.net/npm/apexcharts@3.45.0/dist/apexcharts.css

# DataTables 1.13.7
echo "Downloading DataTables 1.13.7..."
curl -o static/css/vendor/datatables/dataTables.bootstrap5.min.css \
  https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css
curl -o static/js/vendor/datatables/jquery.dataTables.min.js \
  https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js
curl -o static/js/vendor/datatables/dataTables.bootstrap5.min.js \
  https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js
curl -o static/css/vendor/datatables/responsive.dataTables.min.css \
  https://cdn.datatables.net/responsive/2.5.0/css/responsive.dataTables.min.css
curl -o static/js/vendor/datatables/dataTables.responsive.min.js \
  https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js

echo "All CDN assets downloaded successfully!"
