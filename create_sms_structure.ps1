# Create base folder
$base = "sms_local"
New-Item -ItemType Directory -Force -Path $base | Out-Null
Set-Location $base

# Root files
New-Item README.md -ItemType File
New-Item requirements.txt -ItemType File
New-Item .env.example -ItemType File
New-Item alembic.ini -ItemType File

# Main app structure
$folders = @(
  "app",
  "app/security",
  "app/models",
  "app/schemas",
  "app/services",
  "app/routers",
  "app/views",
  "app/templates",
  "app/templates/components",
  "app/templates/director",
  "app/templates/admin",
  "app/templates/print",
  "app/static/css",
  "app/static/js",
  "app/jobs",
  "alembic",
  "alembic/versions",
  "storage",
  "storage/challans",
  "storage/report_cards",
  "storage/payslips",
  "storage/exports",
  "storage/backups"
)

foreach ($f in $folders) {
  New-Item -ItemType Directory -Force -Path $f | Out-Null
}

# Starter files
New-Item app/main.py -ItemType File
New-Item app/settings.py -ItemType File
New-Item app/db.py -ItemType File
