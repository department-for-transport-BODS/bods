from django.http import JsonResponse


from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_gis import filters as gis_filters
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes


# views.py
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Level
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status as ResponseStatus


class SuppressObservationView(viewsets.ViewSet):

    queryset = ObservationResults.objects.all()

    pass
