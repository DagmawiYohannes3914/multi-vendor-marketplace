# setup_docker_dev.ps1
# PowerShell script to set up and run Docker for local development

Write-Host "Setting up Docker environment for local development..." -ForegroundColor Green

# Check if Docker is running
if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop and run this script again." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file with default values..." -ForegroundColor Yellow
    @"
# Postgres
POSTGRES_DB=marketplace
POSTGRES_USER=marketplace
POSTGRES_PASSWORD=marketplace

# Django
DJANGO_SECRET_KEY=change-me-to-a-secure-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# services
DATABASE_URL=postgres://marketplace:marketplace@db:5432/marketplace
DATABASE_HOST=db
DATABASE_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host ".env file created successfully." -ForegroundColor Green
}
else {
    # Check if DATABASE_URL exists in .env and add it if not
    $envContent = Get-Content ".env" -Raw
    if (-not ($envContent -match "DATABASE_URL=")) {
        Write-Host "Adding DATABASE_URL to .env file..." -ForegroundColor Yellow
        "DATABASE_URL=postgres://marketplace:marketplace@db:5432/marketplace" | Out-File -FilePath ".env" -Append -Encoding utf8
        Write-Host "DATABASE_URL added to .env file." -ForegroundColor Green
    }
}

# Start Docker containers
Write-Host "Starting Docker containers..." -ForegroundColor Green
docker-compose up -d

# Wait for database to be ready
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run migrations
Write-Host "Running migrations..." -ForegroundColor Green
docker-compose exec web python manage.py migrate

# Create test users
Write-Host "Creating test users..." -ForegroundColor Green
docker-compose exec web python manage.py create_test_users

# Show running containers
Write-Host "Docker containers are now running:" -ForegroundColor Green
docker-compose ps

Write-Host "\nSetup complete! Your application is running at http://localhost:8000" -ForegroundColor Green
Write-Host "To stop the containers, run: docker-compose down" -ForegroundColor Yellow