#!/bin/bash
# setup_docker_dev.sh
# Bash script to set up and run Docker for local development

echo -e "\033[0;32mSetting up Docker environment for local development...\033[0m"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "\033[0;31mDocker is not running. Please start Docker and run this script again.\033[0m"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "\033[0;33mCreating .env file with default values...\033[0m"
    cat > .env << EOL
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
EOL
    echo -e "\033[0;32m.env file created successfully.\033[0m"
else
    # Check if DATABASE_URL exists in .env and add it if not
    if ! grep -q "DATABASE_URL=" .env; then
        echo -e "\033[0;33mAdding DATABASE_URL to .env file...\033[0m"
        echo "DATABASE_URL=postgres://marketplace:marketplace@db:5432/marketplace" >> .env
        echo -e "\033[0;32mDATABASE_URL added to .env file.\033[0m"
    fi
fi

# Start Docker containers
echo -e "\033[0;32mStarting Docker containers...\033[0m"
docker-compose up -d

# Wait for database to be ready
echo -e "\033[0;33mWaiting for database to be ready...\033[0m"
sleep 5

# Run migrations
echo -e "\033[0;32mRunning migrations...\033[0m"
docker-compose exec web python manage.py migrate

# Create test users
echo -e "\033[0;32mCreating test users...\033[0m"
docker-compose exec web python manage.py create_test_users

# Show running containers
echo -e "\033[0;32mDocker containers are now running:\033[0m"
docker-compose ps

echo -e "\n\033[0;32mSetup complete! Your application is running at http://localhost:8000\033[0m"
echo -e "\033[0;33mTo stop the containers, run: docker-compose down\033[0m"