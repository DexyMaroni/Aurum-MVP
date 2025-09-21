from django.db.models import Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Note, Template, Category, NoteVersion, NoteShare, NoteFile
from .serializers import (
    NoteSerializer, NoteListSerializer, TemplateSerializer, 
    CategorySerializer, NoteVersionSerializer, NoteShareSerializer,
    NoteFileSerializer, NoteSearchSerializer
)


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseNotePermissionMixin:
    """Mixin to check note access permissions"""
    
    def get_note_with_permission(self, note_id, required_permission='READ'):
        """Get note if user has required permission"""
        try:
            note = Note.objects.select_related('user', 'category').get(id=note_id)
        except Note.DoesNotExist:
            return None, False
            
        user = self.request.user
        
        # Owner has all permissions
        if note.user == user:
            return note, True
            
        # Check shared permissions
        try:
            share = NoteShare.objects.get(note=note, shared_with=user)
            if required_permission == 'READ':
                return note, True
            elif required_permission == 'EDIT' and share.permission == 'EDIT':
                return note, True
            else:
                return note, False
        except NoteShare.DoesNotExist:
            return note, False


class NoteListAPIView(APIView, BaseNotePermissionMixin):
    """List and create notes"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get(self, request):
        # Get notes owned by user and notes shared with user using separate queries
        owned_notes = Note.objects.filter(user=request.user).select_related('user', 'category').prefetch_related('files')
        shared_note_ids = NoteShare.objects.filter(shared_with=request.user).values_list('note_id', flat=True)
        shared_notes = Note.objects.filter(id__in=shared_note_ids).select_related('user', 'category').prefetch_related('files')
        
        # Combine querysets into a list and sort
        all_notes = list(owned_notes) + list(shared_notes)
        # Remove duplicates (in case user owns and is shared the same note)
        seen_ids = set()
        unique_notes = []
        for note in all_notes:
            if note.id not in seen_ids:
                unique_notes.append(note)
                seen_ids.add(note.id)
        
        # Sort by updated_at descending
        unique_notes.sort(key=lambda x: x.updated_at, reverse=True)
        
        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(unique_notes, request)
        
        serializer = NoteListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = NoteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NoteDetailAPIView(APIView, BaseNotePermissionMixin):
    """Retrieve, update and delete notes"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        note, has_permission = self.get_note_with_permission(pk, 'READ')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        if not has_permission:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = NoteSerializer(note)
        return Response(serializer.data)

    def put(self, request, pk):
        note, has_permission = self.get_note_with_permission(pk, 'EDIT')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        if not has_permission:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = NoteSerializer(note, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        note, has_permission = self.get_note_with_permission(pk, 'EDIT')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        # Only owner can delete
        if note.user != request.user:
            return Response({'error': 'Only note owner can delete'}, status=status.HTTP_403_FORBIDDEN)

        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteSearchAPIView(APIView):
    """Search notes by title, content, and category"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get(self, request):
        search_serializer = NoteSearchSerializer(data=request.query_params)
        if not search_serializer.is_valid():
            return Response(search_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Start with notes user can access
        owned_notes = Note.objects.filter(user=request.user)
        shared_note_ids = NoteShare.objects.filter(shared_with=request.user).values_list('note_id', flat=True)
        shared_notes = Note.objects.filter(id__in=shared_note_ids)
        
        # Combine into list
        all_notes = list(owned_notes.select_related('user', 'category').prefetch_related('files')) + \
                   list(shared_notes.select_related('user', 'category').prefetch_related('files'))
        
        # Remove duplicates
        seen_ids = set()
        unique_notes = []
        for note in all_notes:
            if note.id not in seen_ids:
                unique_notes.append(note)
                seen_ids.add(note.id)

        # Apply filters
        query_params = search_serializer.validated_data
        
        if 'q' in query_params and query_params['q']:
            q = query_params['q']
            unique_notes = [n for n in unique_notes if q.lower() in n.title.lower() or q.lower() in n.content.lower()]
        
        if 'category' in query_params and query_params['category']:
            category_id = query_params['category']
            unique_notes = [n for n in unique_notes if n.category_id == category_id]
        
        if 'user' in query_params and query_params['user']:
            user_id = query_params['user']
            unique_notes = [n for n in unique_notes if n.user_id == user_id]

        # Sort by updated_at descending
        unique_notes.sort(key=lambda x: x.updated_at, reverse=True)

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(unique_notes, request)
        
        serializer = NoteListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class NoteVersionListAPIView(APIView, BaseNotePermissionMixin):
    """List note versions"""
    permission_classes = [IsAuthenticated]

    def get(self, request, note_pk):
        note, has_permission = self.get_note_with_permission(note_pk, 'READ')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        if not has_permission:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        versions = note.versions.all()
        serializer = NoteVersionSerializer(versions, many=True)
        return Response(serializer.data)


class NoteVersionRestoreAPIView(APIView, BaseNotePermissionMixin):
    """Restore a note to a previous version"""
    permission_classes = [IsAuthenticated]

    def post(self, request, note_pk, version_pk):
        note, has_permission = self.get_note_with_permission(note_pk, 'EDIT')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        if not has_permission:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            version = note.versions.get(id=version_pk)
        except NoteVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)

        # Save current content as new version before restoring
        NoteVersion.objects.create(note=note, content=note.content)
        
        # Restore content
        note.content = version.content
        note.save()

        serializer = NoteSerializer(note)
        return Response(serializer.data)


class NoteShareAPIView(APIView, BaseNotePermissionMixin):
    """Share/unshare notes with users"""
    permission_classes = [IsAuthenticated]

    def get(self, request, note_pk):
        """List users note is shared with"""
        note, has_permission = self.get_note_with_permission(note_pk, 'READ')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        # Only owner can see shares
        if note.user != request.user:
            return Response({'error': 'Only note owner can view shares'}, status=status.HTTP_403_FORBIDDEN)

        shares = note.shares.all().select_related('shared_with')
        serializer = NoteShareSerializer(shares, many=True)
        return Response(serializer.data)

    def post(self, request, note_pk):
        """Share note with a user"""
        note, has_permission = self.get_note_with_permission(note_pk, 'EDIT')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        # Only owner can share
        if note.user != request.user:
            return Response({'error': 'Only note owner can share'}, status=status.HTTP_403_FORBIDDEN)

        serializer = NoteShareSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(note=note)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, note_pk):
        """Unshare note (remove sharing)"""
        note, has_permission = self.get_note_with_permission(note_pk, 'EDIT')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        # Only owner can unshare
        if note.user != request.user:
            return Response({'error': 'Only note owner can unshare'}, status=status.HTTP_403_FORBIDDEN)

        shared_with_id = request.data.get('shared_with_id')
        if not shared_with_id:
            return Response({'error': 'shared_with_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            share = note.shares.get(shared_with_id=shared_with_id)
            share.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NoteShare.DoesNotExist:
            return Response({'error': 'Share not found'}, status=status.HTTP_404_NOT_FOUND)


class NoteFileUploadAPIView(APIView, BaseNotePermissionMixin):
    """Upload files to notes"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, note_pk):
        note, has_permission = self.get_note_with_permission(note_pk, 'EDIT')
        if not note:
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        if not has_permission:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = NoteFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(note=note)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryListAPIView(APIView):
    """List and create categories"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(user=request.user).order_by('name')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailAPIView(APIView):
    """Retrieve, update and delete categories"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Category.objects.get(pk=pk, user=user)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(category, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TemplateListAPIView(APIView):
    """List and create templates"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = Template.objects.filter(user=request.user).order_by('name')
        serializer = TemplateSerializer(templates, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TemplateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TemplateDetailAPIView(APIView):
    """Retrieve, update and delete templates"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Template.objects.get(pk=pk, user=user)
        except Template.DoesNotExist:
            return None

    def get(self, request, pk):
        template = self.get_object(pk, request.user)
        if not template:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TemplateSerializer(template)
        return Response(serializer.data)

    def put(self, request, pk):
        template = self.get_object(pk, request.user)
        if not template:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TemplateSerializer(template, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        template = self.get_object(pk, request.user)
        if not template:
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)

        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)