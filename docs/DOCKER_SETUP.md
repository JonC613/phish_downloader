# 🐳 Docker Setup Guide

## Quick Start

### Windows (PowerShell)
```powershell
.\docker-start.ps1
```

### Linux/Mac
```bash
chmod +x docker-start.sh
./docker-start.sh
```

## Manual Setup

### 1. Start PostgreSQL
```bash
docker-compose up -d postgres
```

### 2. Load Database (after PostgreSQL is ready)
```bash
docker-compose up db_loader
```

### 3. Start Streamlit
```bash
docker-compose up -d streamlit
```

## Services

- **Streamlit UI**: http://localhost:8501
- **PostgreSQL**: localhost:5434
  - Database: `phish_shows`
  - User: `phish_user`
  - Password: `phish_password`

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f streamlit
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart streamlit
```

### Stop Services
```bash
# Stop without removing containers
docker-compose stop

# Stop and remove containers (data persists)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose build streamlit

# Rebuild and restart
docker-compose up -d --build streamlit
```

### Access Container Shell
```bash
docker exec -it phish_streamlit bash
```

### Check Service Status
```bash
docker-compose ps
```

## Troubleshooting

### Streamlit Not Starting
```bash
# Check logs
docker-compose logs streamlit

# Restart
docker-compose restart streamlit
```

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database is healthy
docker-compose ps postgres
```

### Port Already in Use
If port 8501 or 5434 is already in use, edit `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Change to different port
```

### Fresh Start
```bash
# Remove everything and start over
docker-compose down -v
docker-compose up --build
```

## Architecture

```
┌─────────────────┐
│   Streamlit     │ :8501
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │ :5434
│   (Database)    │
└─────────────────┘
```

## Data Volumes

- `postgres_data`: Persistent PostgreSQL data
- `./normalized_shows`: Mounted read-only from host
- `./enriched_shows`: Mounted read-only from host

## Environment Variables

You can customize the setup by editing environment variables in `docker-compose.yml`:

```yaml
environment:
  POSTGRES_DB: phish_shows
  POSTGRES_USER: phish_user
  POSTGRES_PASSWORD: phish_password
  DATABASE_URL: postgresql://...
```

## Production Deployment

For production, consider:
1. Using proper secrets management (not hardcoded passwords)
2. Adding SSL/TLS for database connections
3. Setting up proper backup strategies
4. Using a reverse proxy (nginx) for HTTPS
5. Resource limits and monitoring

## Development Workflow

### Code Changes
1. Edit files locally
2. Rebuild: `docker-compose up -d --build streamlit`
3. View logs: `docker-compose logs -f streamlit`

### Database Changes
1. Update `init_db.sql`
2. Recreate database: `docker-compose down -v && docker-compose up -d`
