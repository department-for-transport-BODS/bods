from pyexpat import model
from unicodedata import category
from django.db import models

class FaresValidation(models.Model):
    dataset_id = models.IntegerField()
    organisation = models.ForeignKey(
        "organisation.Organisation",
        on_delete=models.CASCADE,
        help_text="Bus portal organisation.",
    )
    file_name = models.CharField(max_length=200)
    error_line_no = models.IntegerField()
    type_of_observation = models.CharField(max_length=2000)
    category = models.CharField(max_length=2000)
    error = models.CharField(max_length=2000)
    reference = models.CharField(max_length=2000, default='Please see BODS Fares Validator Guidance v0.2')
    important_note = models.CharField(max_length=2000, default='Data containing this warning will be rejected by BODS after January 2023. Please contact your ticket machine supplier')

    def __str__(self):
        return "%s %s %s" % (self.file_name, self.dataset_id, self.organisation)