from pyexpat import model
from unicodedata import category
from django.db import models

class FaresValidation(models.Model):
    file_name = models.CharField(max_length=200)
    error = models.CharField(max_length=2000)

    def __str__(self):
        return self.file_name