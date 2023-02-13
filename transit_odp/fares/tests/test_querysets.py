from datetime import datetime, timedelta

import faker
import pytest
from django.test import override_settings

from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.fares_validator.factories import FaresValidationResultFactory
from transit_odp.organisation.constants import (
    FeedStatus,
)
from transit_odp.organisation.factories import (
    OrganisationFactory,
)
from transit_odp.fares.models import (
    FaresMetadata,
)

pytestmark = pytest.mark.django_db


class TestFaresQuerySet:
    # Annotations
    def test_add_published_date(self):
        """Tests the queryset is annotated with published date"""
        orgs = OrganisationFactory.create_batch(3)
        FaresMetadataFactory(
            revision__dataset__organisation=orgs[0], revision__is_published=False
        )
        FaresMetadataFactory(
            revision__dataset__organisation=orgs[1], revision__is_published=False
        )
        FaresMetadataFactory(
            revision__dataset__organisation=orgs[2], revision__is_published=True
        )
        qs = FaresMetadata.objects.add_published_date()

        assert len(qs) == 3
        for org in qs:
            if org.id == orgs[0].id:
                assert org.last_updated_date == None
            elif org.id == orgs[1].id:
                assert org.last_updated_date == None
            else:
                assert org.last_updated_date is not None

    def test_add_operator_id(self):
        """Tests the queryset is annotated with operator_id from the dataset table"""
        org1 = OrganisationFactory.create_batch(1, name="KPMG_TEST1")
        org2 = OrganisationFactory.create_batch(1, name="KPMG_TEST2")
        FaresMetadataFactory(
            revision__dataset__organisation=org1[0], revision__is_published=False
        )
        FaresMetadataFactory(
            revision__dataset__organisation=org2[0], revision__is_published=False
        )
        FaresMetadataFactory(
            revision__dataset__organisation=org2[0], revision__is_published=True
        )
        qs = FaresMetadata.objects.add_operator_id()
        assert len(qs) == 3
        for org in qs:
            if org.id == org1[0].id:
                assert org.operator_id == org1[0].id

    def test_add_organisation_name(self):
        """Tests the queryset is annotated with operator_id from the dataset table"""
        org1 = OrganisationFactory.create_batch(1, name="KPMG_TEST1")
        org2 = OrganisationFactory.create_batch(1, name="KPMG_TEST2")
        FaresMetadataFactory(
            revision__dataset__organisation=org1[0], revision__is_published=False
        )
        FaresMetadataFactory(
            revision__dataset__organisation=org2[0], revision__is_published=False
        )
        FaresMetadataFactory(
            revision__dataset__organisation=org2[0], revision__is_published=True
        )
        qs = FaresMetadata.objects.add_organisation_name()
        assert len(qs) == 3
        assert qs[0].organisation_name == "KPMG_TEST1"
        assert qs[1].organisation_name == "KPMG_TEST2"

    def test_add_compliance_status(self):
        """Tests the queryset is annoted with compliance status"""
        org1 = OrganisationFactory.create_batch(1, name="KPMG_TEST1")
        FaresValidationResultFactory()
        FaresMetadataFactory(
            revision__dataset__organisation=org1[0], revision__is_published=True
        )
        qs = FaresMetadata.objects.add_compliance_status()
        assert len(qs) == 1
        assert qs[0].is_fares_compliant == False
