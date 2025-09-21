# Aurum-MVP
A student's all-in-one platform, seamlessly blending AI-powered notes, tasks, communication, and academic support

## Aurum Notes Backend

This repository includes a complete Django REST Framework backend for the Aurum Notes application.

### Quick Start

1. **Install dependencies:**
```bash
pip install django djangorestframework bleach pillow
```

2. **Run migrations:**
```bash
python manage.py migrate
```

3. **Create a superuser:**
```bash
python manage.py createsuperuser
```

4. **Start the server:**
```bash
python manage.py runserver
```

5. **Test the API:**
```bash
# List notes (requires authentication)
curl -u username:password http://localhost:8000/api/notes/

# Create a note
curl -u username:password -X POST http://localhost:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{"title": "My Note", "content": "<p>Hello World!</p>"}'
```

### Features

- ✅ Complete CRUD operations for notes, categories, and templates
- ✅ User authentication and authorization
- ✅ File uploads with validation (5MB max, specific file types)
- ✅ HTML sanitization to prevent XSS attacks
- ✅ Automatic version history tracking
- ✅ Note sharing with READ/EDIT permissions
- ✅ Search and filtering capabilities
- ✅ Pagination for all list endpoints
- ✅ Django admin integration

### API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

### Key Endpoints

- `/api/notes/` - Notes CRUD
- `/api/categories/` - Categories CRUD  
- `/api/templates/` - Templates CRUD
- `/api/notes/search/` - Search notes
- `/api/notes/{id}/versions/` - Version management
- `/api/notes/{id}/share/` - Sharing management
- `/api/notes/{id}/upload/` - File uploads