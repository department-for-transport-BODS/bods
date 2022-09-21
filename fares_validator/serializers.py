from rest_framework import serializers
from .models import FaresValidation

class FaresSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaresValidation
        fields = ['id', 'file_name', 'error']