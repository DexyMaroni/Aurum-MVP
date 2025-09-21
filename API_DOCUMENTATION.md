# Aurum Notes API Documentation

## Overview
Complete Django REST Framework backend for the Aurum Notes application with user authentication, note management, file uploads, sharing, and version control.

## Features Implemented

### 🔐 Authentication
- Django's built-in session and basic authentication
- All endpoints require authentication
- User-specific data isolation

### 📝 Core Models
- **Note**: Main note with title, HTML content, user, category, timestamps
- **Category**: User-specific note categories
- **Template**: Reusable note templates with HTML content
- **NoteVersion**: Automatic version history on content changes
- **NoteShare**: Share notes with READ/EDIT permissions
- **NoteFile**: File attachments with validation

### 🛡️ Security Features
- HTML sanitization using bleach to prevent XSS
- File upload validation (5MB max, jpg/png/gif/svg/pdf only)
- Permission-based access control for notes
- User isolation for all resources

### 📁 File Management
- Upload files to notes with size and type validation
- Files stored in user-specific directories
- Supported formats: JPG, PNG, GIF, SVG, PDF
- Maximum file size: 5MB

### 🔄 Version Control
- Automatic version creation when note content changes
- List all versions of a note
- Restore note to any previous version
- Version history preserved indefinitely

### 👥 Sharing System
- Share notes with other users
- READ or EDIT permissions
- Only note owners can manage sharing
- Shared notes appear in recipient's note list

### 🔍 Search & Filtering
- Search notes by title and content
- Filter by category
- Filter by user (for shared notes)
- Full-text search capabilities

### 📄 Pagination
- 20 items per page by default
- Configurable page size (max 100)
- Standard Django REST pagination

## API Endpoints

### Notes
```
GET /api/notes/                     # List user's notes (owned + shared)
POST /api/notes/                    # Create new note
GET /api/notes/{id}/                # Get note details
PUT /api/notes/{id}/                # Update note (creates version)
DELETE /api/notes/{id}/             # Delete note (owner only)
```

### Search
```
GET /api/notes/search/?q={query}&category={uuid}&user={id}
```

### Versions
```
GET /api/notes/{id}/versions/                      # List note versions
POST /api/notes/{id}/versions/{version_id}/restore/ # Restore version
```

### Sharing
```
GET /api/notes/{id}/share/     # List shares (owner only)
POST /api/notes/{id}/share/    # Share note (owner only)
DELETE /api/notes/{id}/share/  # Unshare note (owner only)
```

### File Uploads
```
POST /api/notes/{id}/upload/   # Upload file to note
```

### Categories
```
GET /api/categories/           # List user's categories
POST /api/categories/          # Create category
GET /api/categories/{id}/      # Get category
PUT /api/categories/{id}/      # Update category
DELETE /api/categories/{id}/   # Delete category
```

### Templates
```
GET /api/templates/            # List user's templates
POST /api/templates/           # Create template
GET /api/templates/{id}/       # Get template
PUT /api/templates/{id}/       # Update template
DELETE /api/templates/{id}/    # Delete template
```

## Example Usage

### Create a Category
```bash
curl -u admin:admin123 -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Work", "description": "Work-related notes"}'
```

### Create a Note
```bash
curl -u admin:admin123 -X POST http://localhost:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting Notes",
    "content": "<h2>Team Meeting</h2><p>Discussed project timeline.</p>",
    "category": "category-uuid-here"
  }'
```

### Search Notes
```bash
curl -u admin:admin123 "http://localhost:8000/api/notes/search/?q=meeting"
```

### Share a Note
```bash
curl -u admin:admin123 -X POST http://localhost:8000/api/notes/{note-id}/share/ \
  -H "Content-Type: application/json" \
  -d '{"shared_with_id": 2, "permission": "READ"}'
```

### Upload File
```bash
curl -u admin:admin123 -X POST http://localhost:8000/api/notes/{note-id}/upload/ \
  -F "file=@document.pdf"
```

## Database Schema

All models use UUID primary keys for security and scalability.

### Key Relationships
- Notes → User (ForeignKey, CASCADE)
- Notes → Category (ForeignKey, SET_NULL, optional)
- Categories → User (ForeignKey, CASCADE)
- Templates → User (ForeignKey, CASCADE)
- NoteVersions → Note (ForeignKey, CASCADE)
- NoteShares → Note, User (ForeignKey, CASCADE)
- NoteFiles → Note (ForeignKey, CASCADE)

### Constraints
- Category names must be unique per user
- Template names must be unique per user
- One share record per note-user pair
- File size limited to 5MB
- File types restricted to: jpg, jpeg, png, gif, svg, pdf

## Testing Results

✅ **Authentication**: All endpoints properly protected
✅ **CRUD Operations**: Working for all models
✅ **File Uploads**: Size and type validation working
✅ **HTML Sanitization**: XSS prevention confirmed
✅ **Version History**: Auto-creation and restore working
✅ **Sharing**: READ/EDIT permissions enforced
✅ **Search**: Text and filter search working
✅ **Pagination**: Proper pagination implemented
✅ **Admin Interface**: Full Django admin integration

## Installation & Setup

1. Install dependencies:
```bash
pip install django djangorestframework bleach pillow
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Create superuser:
```bash
python manage.py createsuperuser
```

4. Start development server:
```bash
python manage.py runserver
```

## Security Considerations

- All HTML content is sanitized to prevent XSS attacks
- File uploads are validated for size and type
- User isolation ensures data privacy
- Permission system prevents unauthorized access
- UUID primary keys prevent enumeration attacks

## Future Enhancements

- JWT authentication for mobile/SPA clients
- Real-time collaboration features
- Advanced search with indexing
- Export/import functionality
- Backup and restore capabilities
- API rate limiting
- Email notifications for sharing