# Docker Setup for News Aggregator Backend

## Quick Start

### Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Build and Run with Docker

```bash
# Build the image
docker build -t news-backend -f DockerFile .

# Run the container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/db.sqlite3:/app/db.sqlite3 \
  -e CLOUDINARY_CLOUD_NAME=your_cloud_name \
  -e CLOUDINARY_API_KEY=your_api_key \
  -e CLOUDINARY_API_SECRET=your_api_secret \
  --name news-backend \
  news-backend
```

## Environment Variables

Create a `.env` file in the project root with:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Or set them in `docker-compose.yml` directly.

## Features

### Updated Dockerfile Includes:
- ✅ Python 3.11 slim base image
- ✅ System dependencies (PostgreSQL client, build tools, curl, git)
- ✅ Automatic pip upgrade
- ✅ Proper directory structure
- ✅ Health check endpoint
- ✅ Automatic migrations on startup
- ✅ Static files collection

### Docker Compose Features:
- ✅ Database persistence (SQLite mounted as volume)
- ✅ Environment variable support
- ✅ Health checks
- ✅ Auto-restart on failure
- ✅ Cloudinary configuration support

## Database Migrations

Migrations run automatically on container startup. To run manually:

```bash
# With docker-compose
docker-compose exec web python manage.py migrate

# With docker
docker exec -it news-backend python manage.py migrate
```

## Creating Admin User in Docker

```bash
# With docker-compose
docker-compose exec web python create_admin_user.py

# With docker
docker exec -it news-backend python create_admin_user.py
```

## Accessing Django Shell

```bash
# With docker-compose
docker-compose exec web python manage.py shell

# With docker
docker exec -it news-backend python manage.py shell
```

## Viewing Logs

```bash
# With docker-compose
docker-compose logs -f web

# With docker
docker logs -f news-backend
```

## Troubleshooting

### Container won't start
- Check logs: `docker-compose logs web`
- Verify environment variables are set
- Check if port 8000 is already in use

### Database issues
- Ensure `db.sqlite3` file exists or create it
- Check file permissions on mounted volume
- Run migrations manually if needed

### Static files not loading
- Run `python manage.py collectstatic` inside container
- Check static files directory permissions

### Health check failing
- Wait for migrations to complete (can take 30-40 seconds)
- Check if Django admin is accessible
- Verify container is running: `docker ps`

## Development Mode

For development with live code reloading, uncomment the volumes section in `docker-compose.yml`:

```yaml
volumes:
  - ./db.sqlite3:/app/db.sqlite3
  - .:/app  # Uncomment this for live reload
```

**Note:** Live reload may cause issues with static files. For production, keep volumes minimal.

## Production Considerations

1. **Use PostgreSQL instead of SQLite** for production
2. **Set DEBUG=False** in settings
3. **Use Gunicorn** instead of runserver:
   ```dockerfile
   CMD ["gunicorn", "--bind", "0.0.0.0:8000", "n_backend.wsgi:application"]
   ```
4. **Add reverse proxy** (nginx) for static files
5. **Use secrets management** for sensitive env vars
6. **Enable HTTPS** with proper SSL certificates

## Build Optimization

The Dockerfile uses multi-stage caching:
- Requirements are copied first (better cache utilization)
- Project files are copied last (faster rebuilds when code changes)

## Health Check

The container includes a health check that verifies the Django admin is accessible. Check status:

```bash
docker ps  # Shows health status
```

