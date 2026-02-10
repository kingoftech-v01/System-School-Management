"""
Accounts App Serializers - DRF serializers for user and profile models.

Provides API serialization for:
- User accounts
- Student profiles
- Lecturer/Staff profiles
- Parent profiles
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'is_student', 'is_lecturer', 'is_parent', 'is_dep_head',
            'role', 'role_display', 'phone', 'address', 'picture',
            'date_joined', 'last_login', 'is_active', 'is_staff'
        ]
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'address',
            'is_student', 'is_lecturer', 'is_parent', 'role'
        ]

    def validate(self, data):
        """Validate password match."""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student profile."""
    user_details = UserSerializer(source='student', read_only=True)
    program_name = serializers.CharField(source='program.title', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = User._meta.get_field('student').related_model  # Get Student model
        fields = [
            'id', 'student', 'user_details', 'level', 'level_display',
            'program', 'program_name'
        ]


class LecturerSerializer(serializers.ModelSerializer):
    """Serializer for Lecturer profile."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'address', 'picture', 'is_lecturer', 'date_joined'
        ]


class ParentSerializer(serializers.ModelSerializer):
    """Serializer for Parent profile."""
    user_details = UserSerializer(source='user', read_only=True)
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    relation_display = serializers.CharField(source='get_relation_display', read_only=True)

    class Meta:
        model = User._meta.get_field('parent_profiles').related_model
        fields = [
            'id', 'user', 'user_details', 'student', 'student_name',
            'first_name', 'last_name', 'phone', 'email',
            'relation', 'relation_display'
        ]


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'address', 'picture'
        ]

    def validate_email(self, value):
        """Ensure email is unique."""
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate(self, data):
        """Validate passwords."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return data

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
