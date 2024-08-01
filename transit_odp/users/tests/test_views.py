import pytest
from django.conf import settings
from django.test import RequestFactory
from django_hosts.resolvers import get_host, reverse

import config.hosts
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.forms.account import PublishAdminNotifications
from transit_odp.users.views.account import (
    DatasetManageView,
    PasswordChangeView,
    UserRedirectView,
)

pytestmark = pytest.mark.django_db


# class TestUserUpdateView:
#     """
#     TODO:
#         extracting view initialization code as class-scoped fixture
#         would be great if only pytest-django supported non-function-scoped
#         fixture db access -- this is a work-in-progress for now:
#         https://github.com/pytest-dev/pytest-django/pull/258
#     """
#
#     def test_get_success_url(
#         self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
#     ):
#         view = UserUpdateView()
#         request = request_factory.get("/fake-url/")
#         request.user = user
#
#         view.request = request
#
#         assert view.get_success_url() == f"/users/{user.username}/"
#
#     def test_get_object(
#         self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
#     ):
#         view = UserUpdateView()
#         request = request_factory.get("/fake-url/")
#         request.user = user
#
#         view.request = request
#
#         assert view.get_object() == user


class TestUserRedirectView:
    @pytest.mark.parametrize(
        "host",
        [
            config.hosts.ROOT_HOST,
            config.hosts.DATA_HOST,
            config.hosts.PUBLISH_HOST,
            config.hosts.ADMIN_HOST,
        ],
    )
    def test_get_redirect_url_for_host(
        self, host: str, request_factory: RequestFactory
    ):
        # Setup
        request = request_factory.get("/fake-url")
        request.host = get_host(host)

        view = UserRedirectView()
        view.request = request

        # Test/Assert
        assert view.get_redirect_url() == reverse("home", host=host)


class TestMyAccountView:
    host = config.hosts.DATA_HOST
    url = reverse("users:home", host=config.hosts.DATA_HOST)

    def test_template(self, user: settings.AUTH_USER_MODEL, client_factory):
        """Test the correct template is used"""
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 200
        assert "users/user_account.html" in [t.name for t in response.templates]

    def test_gatekeeper(self, client_factory):
        """Test the gatekeeper template is rendered when the user is unauthenticated"""
        # Test
        client = client_factory(host=self.host)
        response = client.get(self.url)

        # Assert
        assert response.status_code == 200
        assert "account/gatekeeper.html" in [t.name for t in response.templates]

    def test_context(self, user: settings.AUTH_USER_MODEL, client_factory):
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.context.get("user", None) == user


class TestSettingsView:
    host = config.hosts.DATA_HOST
    url = reverse("users:settings", host=config.hosts.DATA_HOST)

    def test_template(self, user: settings.AUTH_USER_MODEL, client_factory):
        """Test the correct template is used"""
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 200
        assert "users/users_settings.html" in [t.name for t in response.templates]

    def test_login_required(self, client_factory):
        """Test the unauthenticated user is redirected"""
        # Setup
        client = client_factory(host=self.host)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 302

    def test_context(self, user: settings.AUTH_USER_MODEL, client_factory):
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.context.get("api_key", None) == user.auth_token

    def test_developer_has_no_form(self, client_factory):
        # Set up
        user = UserFactory.create(account_type=AccountType.developer.value)
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert "form" not in response.context_data

    def test_admin_gets_admin_form(self, client_factory):
        # Set up
        user = UserFactory.create(account_type=AccountType.org_admin.value)
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        form = response.context_data["form"]
        assert isinstance(form, PublishAdminNotifications)


class TestPasswordChangeView:
    host = config.hosts.DATA_HOST
    url = reverse("account_change_password", host=config.hosts.DATA_HOST)

    def test_template(self, user: settings.AUTH_USER_MODEL, client_factory):
        """Test the correct template is used"""
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 200
        assert "account/password_change.html" in [t.name for t in response.templates]

    def test_login_required(self, client_factory):
        """Test the unauthenticated user is redirected"""
        # Setup
        client = client_factory(host=self.host)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 302

    def test_get_success_url(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        view = PasswordChangeView()
        request = request_factory.get(self.url)
        request.host = get_host(self.host)
        request.user = user

        view.request = request

        assert view.get_success_url() == reverse(
            "account_change_password_done", host=config.hosts.DATA_HOST
        )

    def test_change_of_password_triggers_email(self, user, client_factory, mailoutbox):
        client = client_factory(host=self.host)
        user.set_password("oldpassword")
        user.save()

        client.force_login(user=user)

        response = client.post(
            self.url,
            data={
                "oldpassword": "oldpassword",
                "password1": "newPassword_34324()()",
                "password2": "newPassword_34324()()",
                "submit": "submit",
            },
        )

        assert response.status_code == 302
        assert mailoutbox[0].to[0] == user.email
        assert (
            mailoutbox[0].subject
            == "You have changed your password on the Bus Open Data Service"
        )


class TestPasswordChangeDoneView:
    host = config.hosts.DATA_HOST
    url = reverse("account_change_password_done", host=config.hosts.DATA_HOST)

    def test_template(self, user: settings.AUTH_USER_MODEL, client_factory):
        """Test the correct template is used"""
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 200
        assert "account/password_change_done.html" in [
            t.name for t in response.templates
        ]

    def test_login_required(self, client_factory):
        """Test the unauthenticated user is redirected"""
        # Setup
        client = client_factory(host=self.host)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 302


class TestEmailView:
    host = config.hosts.DATA_HOST
    url = reverse("account_email", host=config.hosts.DATA_HOST)

    def test_login_required(self, client_factory):
        """Test the unauthenticated user is redirected"""
        # Setup
        client = client_factory(host=self.host)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 302

    def test_redirect(self, user: settings.AUTH_USER_MODEL, client_factory):
        """Test the view redirects all requests away (changing email is currently
        not supported)"""
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 302
        assert reverse("users:settings", host=config.hosts.DATA_HOST) in response.url


class TestFeedsManageView:
    host = config.hosts.DATA_HOST
    url = reverse("users:feeds-manage", host=config.hosts.DATA_HOST)

    def test_template(self, user: settings.AUTH_USER_MODEL, client_factory):
        """Test the correct template is used"""
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 200
        assert "users/feeds_manage.html" in [t.name for t in response.templates]

    def test_login_required(self, client_factory):
        """Test the unauthenticated user is redirected"""
        # Setup
        client = client_factory(host=self.host)

        # Test
        response = client.get(self.url)

        # Assert
        assert response.status_code == 302

    def test_paginated_by(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        # Setup
        request = request_factory.get(self.url)
        request.user = user
        request.host = get_host(self.host)

        # Test
        view = DatasetManageView()
        view.request = request

        # Assert
        assert view.paginate_by == 10

    def test_context(self, user: settings.AUTH_USER_MODEL, client_factory):
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)
        for revision in DatasetRevisionFactory.create_batch(15):
            revision.dataset.subscribers.add(user)

        # Test
        response = client.get(self.url)

        # Assert
        page = response.context_data.get("page_obj", None)
        assert page is not None
        assert page.number == 1

        assert response.context_data["object_list"].count() == 10

    @pytest.mark.parametrize("page,expected", [(1, 1), (2, 2)])
    def test_page_query_params(
        self, page, expected, user: settings.AUTH_USER_MODEL, client_factory
    ):
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)
        for revision in DatasetRevisionFactory.create_batch(15):
            revision.dataset.subscribers.add(user)

        # Test
        response = client.get(self.url, data={"page": page})

        # Assert
        page = response.context_data.get("page_obj", None)
        assert page is not None
        assert page.number == expected

    def test_mute_notifications(self, user: settings.AUTH_USER_MODEL, client_factory):
        # Set up
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Test
        response = client.post(self.url, data={"mute_notifications": True})

        user.refresh_from_db()

        # Assert
        assert response.status_code == 302
        assert user.settings.mute_all_dataset_notifications is True

    def test_can_filter_out_multiple_subscribers(
        self, user: settings.AUTH_USER_MODEL, client_factory
    ):
        bob, john = [UserFactory.create(username=name) for name in ("bob", "john")]
        client = client_factory(host=self.host)
        client.force_login(user=user)

        # Set up, three with logged in user, two with user plus two others
        # and one with just the others
        for revision in DatasetRevisionFactory.create_batch(3):
            revision.dataset.subscribers.add(user)

        for revision in DatasetRevisionFactory.create_batch(2):
            for sub in (user, bob, john):
                revision.dataset.subscribers.add(sub)

        revision = DatasetRevisionFactory.create()
        for sub in (bob, john):
            revision.dataset.subscribers.add(sub)

        # Test
        response = client.get(self.url)
        # Assert
        assert response.context_data["object_list"].count() == 5

    @pytest.mark.parametrize(
        "dataset_factory_type, rows, pages",
        [
            (DatasetRevisionFactory, 11, 2),
            (DatasetRevisionFactory, 21, 3),
            (DatasetRevisionFactory, 51, 6),
            (AVLDatasetRevisionFactory, 61, 7),
            (AVLDatasetRevisionFactory, 71, 8),
            (AVLDatasetRevisionFactory, 101, 11),
            (FaresDatasetRevisionFactory, 111, 12),
            (FaresDatasetRevisionFactory, 121, 13),
            (FaresDatasetRevisionFactory, 151, 16),
        ],
    )
    def test_unsubscribe_dataset(
        self,
        user: settings.AUTH_USER_MODEL,
        client_factory,
        dataset_factory_type,
        rows,
        pages,
    ):
        """
        GIVEN : different type of dataset: Timetable, AVL, Fares
               number of rows per table, number of pages in the table
        WHEN  : the table is created, the link for the last page of the table,
              the last element is deleted from the Dataset
        THEN  : the link in the last page should be updated according
              with the rows in the database.
        """
        client = client_factory(host=self.host)
        client.force_login(user=user)

        for revision in dataset_factory_type.create_batch(rows):
            revision.dataset.subscribers.add(user)

        response = client.get(self.url)
        page = response.context_data.get("page_obj", None)
        assert page is not None

        while page.has_next():
            url_next = f"{self.url}?page={page.next_page_number()}&"
            response = client.get(url_next)
            page = response.context_data.get("page_obj", None)
            assert page is not None

        assert page.number == pages

        revision.dataset.subscribers.remove(user)

        name_router_subscription = "feed-subscription"
        name_router_success = "feed-subscription-success"
        if dataset_factory_type().dataset.dataset_type == DatasetType.AVL.value:
            name_router_subscription = f"avl-{name_router_subscription}"
            name_router_success = f"avl-{name_router_success}"
        elif dataset_factory_type().dataset.dataset_type == DatasetType.FARES.value:
            name_router_subscription = f"fares-{name_router_subscription}"
            name_router_success = f"fares-{name_router_success}"

        # The right 'back_url' link in the "success" page has been
        # generated in the "subscription" page.  The steps here are:
        # 1. "subscription" page -> 'back_url' link with the correct
        #    number of the page according with the table in the
        #    queryparams.
        #
        # 2. The call of "success" page and test if in the
        #    context_data there is the correct 'back_url'
        client.get(
            reverse(
                name_router_subscription,
                args=[revision.dataset_id],
                host=config.hosts.DATA_HOST,
            ),
            follow=True,
            HTTP_REFERER=self.url + f"?page={pages}&",
        )
        response = client.get(
            reverse(
                name_router_success,
                args=[revision.dataset_id],
                host=config.hosts.DATA_HOST,
            ),
            follow=True,
        )

        assert response.context_data["back_url"] == self.url + f"?page={pages - 1}&"
