from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Note, Template, Category, NoteVersion, NoteShare, NoteFile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (for sharing)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'email']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model"""
    class Meta:
        model = Template
        fields = ['id', 'name', 'description', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NoteFileSerializer(serializers.ModelSerializer):
    """Serializer for NoteFile model"""
    class Meta:
        model = NoteFile
        fields = ['id', 'file', 'filename', 'uploaded_at']
        read_only_fields = ['id', 'filename', 'uploaded_at']


class NoteVersionSerializer(serializers.ModelSerializer):
    """Serializer for NoteVersion model"""
    class Meta:
        model = NoteVersion
        fields = ['id', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class NoteShareSerializer(serializers.ModelSerializer):
    """Serializer for NoteShare model"""
    shared_with = UserSerializer(read_only=True)
    shared_with_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = NoteShare
        fields = ['id', 'shared_with', 'shared_with_id', 'permission', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_shared_with_id(self, value):
        try:
            user = User.objects.get(id=value)
            # Ensure user is not sharing with themselves
            if user == self.context['request'].user:
                raise serializers.ValidationError("Cannot share note with yourself")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

    def create(self, validated_data):
        shared_with_id = validated_data.pop('shared_with_id')
        shared_with = User.objects.get(id=shared_with_id)
        validated_data['shared_with'] = shared_with
        return super().create(validated_data)


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for Note model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    files = NoteFileSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    shares = NoteShareSerializer(many=True, read_only=True)
    version_count = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'user', 'category', 'category_name',
            'created_at', 'updated_at', 'files', 'shares', 'version_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_version_count(self, obj):
        return obj.versions.count()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_category(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("You can only assign your own categories to notes")
        return value


class NoteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for Note lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    user = UserSerializer(read_only=True)
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'user', 'category', 'category_name',
            'created_at', 'updated_at', 'file_count'
        ]

    def get_file_count(self, obj):
        return obj.files.count()


class NoteSearchSerializer(serializers.Serializer):
    """Serializer for note search parameters"""
    q = serializers.CharField(required=False, help_text="Search query for title and content")
    category = serializers.UUIDField(required=False, help_text="Filter by category ID")
    user = serializers.IntegerField(required=False, help_text="Filter by user ID (for shared notes)")