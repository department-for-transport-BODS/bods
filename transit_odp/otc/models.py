from django.db import models

from transit_odp.otc.constants import (
    LicenceDescription,
    LicenceStatuses,
    SubsidiesDescription,
    TrafficAreas,
)
from transit_odp.otc.dataclasses import Licence as RegistryLicence
from transit_odp.otc.dataclasses import LocalAuthority as RegistryLocalAuthority
from transit_odp.otc.dataclasses import Operator as RegistryOperator
from transit_odp.otc.dataclasses import Service as RegistryService
from transit_odp.otc.managers import (
    LicenceManager,
    LocalAuthorityManager,
    OperatorManager,
    ServiceManager,
)


class Licence(models.Model):
    granted_date = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    number = models.CharField(max_length=9, blank=False, null=False, unique=True)
    status = models.CharField(
        choices=LicenceStatuses.choices, max_length=30, blank=True, null=False
    )

    objects = LicenceManager()

    @classmethod
    def from_registry_licence(cls, registry_licence: RegistryLicence):
        return cls(**registry_licence.dict())


class Operator(models.Model):
    discs_in_possession = models.IntegerField(blank=False, null=True)
    authdiscs = models.IntegerField(blank=False, null=True)
    operator_id = models.IntegerField(unique=True, blank=False, null=False)
    operator_name = models.CharField(max_length=100, blank=True, null=False)
    address = models.TextField(blank=True, null=False)

    objects = OperatorManager()

    @classmethod
    def from_registry_operator(cls, registry_operator: RegistryOperator):
        return cls(**registry_operator.dict())


class Service(models.Model):
    operator = models.ForeignKey(
        Operator, related_name="services", on_delete=models.CASCADE
    )
    licence = models.ForeignKey(
        Licence, related_name="services", on_delete=models.CASCADE
    )
    registration_number = models.CharField(max_length=20, blank=False, null=False)
    variation_number = models.IntegerField(blank=False, null=False)
    service_number = models.CharField(max_length=1000, blank=True, null=False)
    current_traffic_area = models.CharField(
        choices=TrafficAreas.choices, max_length=1, blank=True, null=False
    )
    start_point = models.TextField(blank=True, null=False)
    finish_point = models.TextField(blank=True, null=False)
    via = models.TextField(blank=True, null=False)
    effective_date = models.DateField(null=True)
    received_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    service_type_other_details = models.TextField(blank=True, null=False)
    registration_code = models.IntegerField(blank=False, null=True)
    description = models.CharField(
        choices=LicenceDescription.choices, max_length=25, blank=True, null=False
    )
    registration_status = models.CharField(max_length=20, blank=True, null=False)
    public_text = models.TextField(blank=True, null=False)
    service_type_description = models.CharField(max_length=1000, blank=True, null=False)
    short_notice = models.BooleanField(blank=False, null=True)
    subsidies_description = models.CharField(
        choices=SubsidiesDescription.choices, max_length=7, blank=True, null=False
    )
    subsidies_details = models.TextField(blank=True, null=False)
    last_modified = models.DateTimeField(null=True)

    objects = ServiceManager()

    @classmethod
    def from_registry_service(
        cls, registry_service: RegistryService, operator: Operator, licence: Licence
    ):
        kwargs = registry_service.dict()
        kwargs["operator"] = operator
        kwargs["licence"] = licence
        return cls(**kwargs)


class LocalAuthority(models.Model):
    name = models.TextField(blank=True, null=False)
    registration_numbers = models.ManyToManyField(Service, related_name="registration")

    @classmethod
    def from_registry_lta(cls, registry_lta: RegistryLocalAuthority):
        return cls(
            name=registry_lta.name,
            registration_numbers=[
                Service(**service) for service in registry_lta.registration_numbers
            ],
        )

    objects = LocalAuthorityManager()


class LocalAuthorityMappingAdmin(models.Model):
    otc_lta_name = models.CharField(max_length=255, unique=True)
    ui_lta_name = models.CharField(max_length=255)
    atco_code = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return self.otc_lta_name