# Multi-Vendor Marketplace

A full-stack multi-vendor marketplace application built with Django and React.

## Features

- User authentication with UUID support
- Vendor and customer profiles
- Product management
- Order processing
- Real-time notifications using Django Channels
- Background task processing with Celery

## Prerequisites

- Docker and Docker Compose
- Git

## Local Development Setup

### Using Docker (Recommended)

The easiest way to set up the project is using Docker, which provides a consistent development environment with PostgreSQL and Redis.

#### Windows

1. Clone the repository
2. Run the setup script:

```powershell
.\setup_docker_dev.ps1
```

#### macOS/Linux

1. Clone the repository
2. Make the setup script executable and run it:

```bash
chmod +x setup_docker_dev.sh
./setup_docker_dev.sh
```

The script will:
- Create a `.env` file with default values if it doesn't exist
- Start the Docker containers
- Run database migrations
- Create test users (vendor and customer)

After running the script, the application will be available at http://localhost:8000.

### Test Users

The setup script creates two test users:

1. Vendor:
   - Username: testvendor
   - Password: password123
   - First Name: John
   - Last Name: Seller

2. Customer:
   - Username: testcustomer
   - Password: password123
   - First Name: Jane
   - Last Name: Buyer

## Project Structure

- `backend/` - Django backend with REST API
  - `accounts/` - User authentication and management
  - `profiles/` - Vendor and customer profiles
  - `marketplace/` - Project settings and configuration

- `frontend/` - React frontend (to be implemented)

## Development Workflow

1. Start the Docker containers: `docker-compose up -d`
2. Make changes to the code
3. Access the API at http://localhost:8000/api/
4. Stop the containers when done: `docker-compose down`

## License

MIT