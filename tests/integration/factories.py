import factory
from django.contrib.auth import get_user_model

from transit_odp.naptan.models import AdminArea, Locality
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.users.constants import AccountType


class OrganisationFactory(factory.django.DjangoModelFactory):
    short_name = factory.Faker("company")
    name = factory.Sequence(lambda n: factory.Faker("company").generate() + f" {n}")
    is_active = True

    class Meta:
        model = Organisation


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker("user_name")
    password = factory.Faker("password")
    email = factory.Faker("email")
    name = factory.Faker("name")
    account_type = AccountType.developer.value

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]

    @factory.post_generation
    def organisations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for organisation in extracted:
                self.organisations.add(organisation)
        else:
            self.organisations.add(OrganisationFactory())


class DeveloperFactory(UserFactory):
    account_type = AccountType.developer.value

    @factory.post_generation
    def organisations(self, create, extracted, **kwargs):
        if not create:
            return


class PublisherUserFactory(UserFactory):
    account_type = AccountType.org_admin.value


class SiteAdminFactory(UserFactory):
    account_type = AccountType.site_admin.value

    @factory.post_generation
    def organisations(self, create, extracted, **kwargs):
        if not create:
            return


class AdminAreaFactory(factory.DjangoModelFactory):
    class Meta:
        model = AdminArea

    atco_code = factory.Sequence(lambda n: n)  # unique atco code
    name = factory.Faker("street_name")
    traveline_region_id = factory.Faker("pystr", min_chars=12, max_chars=12)


class LocalityFactory(factory.DjangoModelFactory):
    class Meta:
        model = Locality

    gazetteer_id = factory.Sequence(lambda n: n)  # unique id
    name = factory.Faker("street_name")
    easting = 0
    northing = 0


class PublicationFactory(factory.django.DjangoModelFactory):
    organisation = factory.SubFactory(OrganisationFactory)
    contact = factory.SelfAttribute("organisation.key_contact")

    class Meta:
        model = Dataset


class RevisionFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: factory.Faker("sentence").generate() + f" {n}")
    description = factory.Faker("paragraph")
    short_description = factory.Faker("pystr", min_chars=1, max_chars=30)
    comment = factory.Faker("paragraph")
    published_at = None
    published_by = None

    class Meta:
        model = DatasetRevision


class TimetablePublicationFactory(PublicationFactory):
    dataset_type = DatasetType.TIMETABLE.value


class TimetableDatasetFactory(RevisionFactory):
    dataset = factory.SubFactory(
        TimetablePublicationFactory,
        live_revision=None,
    )
    url_link = factory.Faker("uri")

    """
        Create a fake upload_file. Override with 'upload_file__from_file' or
        'upload_file__from_path', see
        https://factoryboy.readthedocs.io/en/latest/orms.html#factory.django.FileField

        with open('filepath', 'r') as fin:
            feed = FeedFactory.create(upload_file__from_file=fin)

        or

        feed = FeedFactory.create(upload_file__from_path='filepath')
        """
    upload_file = factory.django.FileField(filename="transXchange.xml")


class AVLPublicationFactory(PublicationFactory):
    dataset_type = DatasetType.AVL.value


class AVLDatasetFactory(RevisionFactory):
    dataset = factory.SubFactory(
        AVLPublicationFactory,
        live_revision=None,
    )
    url_link = factory.Faker("uri")
    username = factory.Faker("user_name")
    password = factory.Faker("password")
    requestor_ref = ""


class FaresPublicationFactory(PublicationFactory):
    dataset_type = DatasetType.FARES.value


class FaresDatasetFactory(RevisionFactory):
    dataset = factory.SubFactory(
        FaresPublicationFactory,
        live_revision=None,
    )
    url_link = factory.Faker("uri")
    upload_file = factory.django.FileField(filename="netex.xml")
