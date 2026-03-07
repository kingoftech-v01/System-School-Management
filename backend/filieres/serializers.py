"""
Filieres Serializers - DRF serializers for academic programs API.

This module provides serializers for:
- Filiere model (academic programs)
- FiliereSubject model (subjects in a program)
- FiliereRequirement model (admission requirements)
"""

from rest_framework import serializers
from .models import Filiere, FiliereSubject, FiliereRequirement


# ============================================================================
# FILIERE SERIALIZERS
# ============================================================================

class FiliereSerializer(serializers.ModelSerializer):
    """
    Full serializer for filieres (academic programs).
    """
    coordinator_name = serializers.CharField(
        source='coordinator.get_full_name',
        read_only=True,
        allow_null=True
    )
    subject_count = serializers.IntegerField(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = Filiere
        fields = [
            'id', 'tenant', 'name', 'code', 'description', 'level', 'level_display',
            'duration_years', 'capacity', 'is_active', 'coordinator',
            'coordinator_name', 'subject_count', 'enrolled_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tenant', 'created_at', 'updated_at']


class FiliereListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing filieres.
    """
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    subject_count = serializers.IntegerField(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Filiere
        fields = [
            'id', 'name', 'code', 'level', 'level_display', 'is_active',
            'subject_count', 'enrolled_count'
        ]


class FiliereCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating filieres.
    """
    class Meta:
        model = Filiere
        fields = [
            'name', 'code', 'description', 'level', 'duration_years',
            'capacity', 'is_active', 'coordinator'
        ]

    def validate_code(self, value):
        """Ensure code is uppercase and unique per tenant."""
        return value.upper()

    def validate_duration_years(self, value):
        """Ensure duration is between 1 and 10 years."""
        if value < 1 or value > 10:
            raise serializers.ValidationError('Duration must be between 1 and 10 years.')
        return value


# ============================================================================
# FILIERE SUBJECT SERIALIZERS
# ============================================================================

class FiliereSubjectSerializer(serializers.ModelSerializer):
    """
    Full serializer for filiere subjects.
    """
    filiere_name = serializers.CharField(source='filiere.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = FiliereSubject
        fields = [
            'id', 'filiere', 'filiere_name', 'subject', 'subject_name',
            'year', 'semester', 'coefficient', 'is_mandatory', 'order'
        ]
        read_only_fields = ['filiere']


class FiliereSubjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for adding subjects to a filiere.
    """
    class Meta:
        model = FiliereSubject
        fields = ['subject', 'year', 'semester', 'coefficient', 'is_mandatory', 'order']

    def validate_coefficient(self, value):
        """Ensure coefficient is positive."""
        if value <= 0:
            raise serializers.ValidationError('Coefficient must be greater than 0.')
        return value


# ============================================================================
# FILIERE REQUIREMENT SERIALIZERS
# ============================================================================

class FiliereRequirementSerializer(serializers.ModelSerializer):
    """
    Serializer for filiere admission requirements.
    """
    filiere_name = serializers.CharField(source='filiere.name', read_only=True)
    type_display = serializers.CharField(source='get_requirement_type_display', read_only=True)

    class Meta:
        model = FiliereRequirement
        fields = [
            'id', 'filiere', 'filiere_name', 'requirement_type', 'type_display',
            'description', 'is_mandatory', 'created_at'
        ]
        read_only_fields = ['filiere', 'created_at']


class FiliereRequirementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating filiere requirements.
    """
    class Meta:
        model = FiliereRequirement
        fields = ['requirement_type', 'description', 'is_mandatory']
