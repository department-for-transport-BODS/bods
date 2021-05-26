from django.db import models


class Organisation(models.Model):
    name = models.CharField(max_length=255)


class NOC(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    noc = models.CharField(max_length=10, unique=True)
