# News Aggregator Backend API

Django REST API backend for the News Aggregator platform with admin dashboard support.

## Features

- ✅ User authentication and authorization (Reader, Journalist, Admin roles)
- ✅ Article management (CRUD operations)
- ✅ Article interactions (likes, comments, saves)
- ✅ Admin dashboard endpoints
- ✅ Cloudinary integration for media uploads
- ✅ CORS support for frontend integration
- ✅ Django Admin with Jazzmin theme

## Tech Stack

- **Framework:** Django 5.2.7
- **Database:** SQLite (development) / PostgreSQL (production)
- **Authentication:** Custom token-based authentication
- **Media Storage:** Cloudinary
- **Admin Theme:** Django Jazzmin

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)
- Cloudinary account (for media uploads)

## Local Development Setup

### 1. Clone and Navigate

```bash
cd n_backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Admin User

```bash
python create_admin_user.py
```

Or manually:
```bash
python manage.py shell
```

```python
from n_backend.app.users.models import Users
from n_backend.app.users.views import generate_simple_token

admin_user = Users.objects.create(
    username='admin',
    email='admin@example.com',
    password='admin123',
    role='admin'
)
token = generate_simple_token(admin_user)
print(f"Token: {token}")
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Docker Setup

### Quick Start with Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Docker Build and Run

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

### Docker Commands

```bash
# Create admin user in Docker
docker-compose exec web python create_admin_user.py

# Run migrations manually
docker-compose exec web python manage.py migrate

# Access Django shell
docker-compose exec web python manage.py shell

# View logs
docker-compose logs -f web

# Restart container
docker-compose restart web
```

For detailed Docker documentation, see [DOCKER_README.md](./DOCKER_README.md)

## API Endpoints

### Authentication Endpoints

- `POST /auth/register/` - Register new user
- `POST /auth/login/` - User login
- `GET /auth/profile/` - Get user profile (requires auth)
- `PUT /auth/profile/update/` - Update user profile (requires auth)
- `POST /auth/change-password/` - Change password (requires auth)
- `DELETE /auth/delete-account/` - Delete account (requires auth)

### Article Endpoints

- `GET /api/articles/get/` - Get all articles
- `GET /api/articles/get-by-id/?id={id}` - Get article by ID
- `GET /api/articles/get-by-category/?category={category}` - Get articles by category
- `GET /api/articles/get-by-author/?author={author_id}` - Get articles by author
- `POST /api/articles/create/` - Create article (requires auth)
- `PUT /api/articles/update/` - Update article (requires auth)
- `DELETE /api/articles/delete/?id={id}` - Delete article (requires auth)

### Article Interaction Endpoints

- `POST /api/articles/add-like/` - Like/unlike article
- `POST /api/articles/add-comment/` - Add comment
- `GET /api/articles/get-comments/?article_id={id}` - Get comments
- `POST /api/articles/toggle-save-article/` - Save/unsave article
- `GET /api/articles/user-interaction/?article_id={id}&user_id={id}` - Get user interaction

### Admin Endpoints (Admin Only)

- `GET /api/articles/admin/pending/` - Get pending articles
- `POST /api/articles/admin/approve/` - Approve article(s)
- `POST /api/articles/admin/reject/` - Reject article
- `DELETE /api/articles/admin/delete/?id={id}` - Delete article (admin)
- `GET /auth/admin/counts/` - Get user counts (readers/journalists)

## Admin Dashboard

The admin dashboard is accessible at `/admin/` with Django's admin interface (Jazzmin theme).

### Admin Features

- View and manage all users
- View and manage all articles
- Approve/reject pending articles via API
- Monitor user counts
- Manage article categories and content

## API Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <token>
```

Tokens are obtained from the login endpoint and should be stored client-side.

## Project Structure

```
n_backend/
├── manage.py
├── requirements.txt
├── DockerFile
├── docker-compose.yml
├── .dockerignore
├── n_backend/
│   ├── settings.py
│   ├── urls.py
│   └── app/
│       ├── articles/
│       │   ├── models.py
│       │   ├── views.py
│       │   └── urls.py
│       ├── users/
│       │   ├── models.py
│       │   ├── views.py
│       │   └── urls.py
│       ├── cloudinary.py
│       └── utils.py (admin decorators)
└── db.sqlite3
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | Yes |
| `CLOUDINARY_API_KEY` | Cloudinary API key | Yes |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | Yes |
| `DJANGO_SETTINGS_MODULE` | Django settings module | Auto-set |
| `DEBUG` | Debug mode (True/False) | Optional |

## Database

### Development (SQLite)

The project uses SQLite by default for development. The database file is `db.sqlite3`.

### Production (PostgreSQL)

For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

## Testing

Run the test script to verify admin endpoints:

```bash
# Install requests if not already installed
pip install requests

# Run test script
python test_admin_endpoints.py
```

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

To add more origins, update `CORS_ALLOWED_ORIGINS` in `settings.py`.

## Troubleshooting

### Migration Issues

```bash
# Reset migrations (careful - deletes data)
python manage.py migrate --run-syncdb
```

### Token Issues

- Tokens expire after 7 days
- Generate new token via login endpoint
- Check token is included in Authorization header

### Database Issues

```bash
# Create new database
python manage.py migrate

# Create superuser (for Django admin)
python manage.py createsuperuser
```

### Docker Issues

- Check logs: `docker-compose logs -f`
- Verify environment variables
- Check port 8000 is available
- Ensure database file has proper permissions

## Production Deployment

### Recommended Setup

1. **Use PostgreSQL** instead of SQLite
2. **Set DEBUG=False** in settings
3. **Use Gunicorn** instead of runserver:
   ```bash
   pip install gunicorn
   gunicorn --bind 0.0.0.0:8000 n_backend.wsgi:application
   ```
4. **Add Nginx** as reverse proxy
5. **Enable HTTPS** with SSL certificates
6. **Use environment variables** for secrets
7. **Set up proper logging**

### Security Checklist

- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use HTTPS
- [ ] Set up proper CORS origins
- [ ] Use environment variables for secrets
- [ ] Enable CSRF protection
- [ ] Use secure database credentials

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the repository.

## Author

Naman Jha

