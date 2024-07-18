from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import MultiTableMixin, SingleTableView
from django_hosts import reverse
import config.hosts

from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable
from transit_odp.organisation.models import Dataset
