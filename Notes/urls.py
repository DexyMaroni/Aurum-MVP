from django.urls import path
from .views import (
    NoteListAPIView, NoteDetailAPIView, NoteSearchAPIView,
    NoteVersionListAPIView, NoteVersionRestoreAPIView,
    NoteShareAPIView, NoteFileUploadAPIView,
    CategoryListAPIView, CategoryDetailAPIView,
    TemplateListAPIView, TemplateDetailAPIView
)

app_name = 'notes'

urlpatterns = [
    # Notes
    path('notes/', NoteListAPIView.as_view(), name='note-list'),
    path('notes/<uuid:pk>/', NoteDetailAPIView.as_view(), name='note-detail'),
    path('notes/search/', NoteSearchAPIView.as_view(), name='note-search'),
    
    # Note versions
    path('notes/<uuid:note_pk>/versions/', NoteVersionListAPIView.as_view(), name='note-version-list'),
    path('notes/<uuid:note_pk>/versions/<uuid:version_pk>/restore/', NoteVersionRestoreAPIView.as_view(), name='note-version-restore'),
    
    # Note sharing
    path('notes/<uuid:note_pk>/share/', NoteShareAPIView.as_view(), name='note-share'),
    
    # File uploads
    path('notes/<uuid:note_pk>/upload/', NoteFileUploadAPIView.as_view(), name='note-file-upload'),
    
    # Categories
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', CategoryDetailAPIView.as_view(), name='category-detail'),
    
    # Templates
    path('templates/', TemplateListAPIView.as_view(), name='template-list'),
    path('templates/<uuid:pk>/', TemplateDetailAPIView.as_view(), name='template-detail'),
]