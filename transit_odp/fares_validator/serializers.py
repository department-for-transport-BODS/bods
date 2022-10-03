from rest_framework import serializers

from .models import FaresValidation


class FaresSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaresValidation
        fields = ["id", "dataset_id", "file_name", "error_line_no", "error"]
