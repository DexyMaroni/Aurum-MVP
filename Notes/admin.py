from django.contrib import admin
from .models import Note, Template, Category, NoteVersion, NoteShare, NoteFile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'description']


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'user']
    search_fields = ['name', 'description']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'category', 'user']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NoteVersion)
class NoteVersionAdmin(admin.ModelAdmin):
    list_display = ['note', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(NoteShare)
class NoteShareAdmin(admin.ModelAdmin):
    list_display = ['note', 'shared_with', 'permission', 'created_at']
    list_filter = ['permission', 'created_at']
    readonly_fields = ['created_at']


@admin.register(NoteFile)
class NoteFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'note', 'uploaded_at']
    list_filter = ['uploaded_at']
    readonly_fields = ['uploaded_at']
