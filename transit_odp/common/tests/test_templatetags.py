from django.conf import settings
from django.http import QueryDict
from django.template import Context, Template
from django.test import TestCase

from config.settings.base import APP_VERSION_NUMBER


class TemplateTagsTestCase(TestCase):
    def test_version(self):
        out = Template("{% load  version %}" "{% version %}").render(Context())

        self.assertEqual(out, APP_VERSION_NUMBER)

    def test_active_url_pattern_match(self):
        context = Context(dict_={"request": self.client})
        context["request"].build_absolute_uri = lambda: "/"
        out = Template(
            "{% load active_url %}"
            '{% active_url "/" host="www" css_class="govuk-link--active" %}'
        ).render(context=context)
        self.assertEqual(out, "govuk-link--active")

    def test_active_url_empty(self):
        context = Context(dict_={"request": self.client})
        context["request"].build_absolute_uri = lambda: "/browse/"
        out = Template(
            "{% load active_url %}"
            '{% active_url "/guidance/" css_class="govuk-link--active" %}'
        ).render(context=context)
        self.assertEqual(out, "")


class TestQueryTransform(TestCase):
    def test_query_transform_add(self):
        self.request = self.client_class
        self.request.GET = QueryDict(query_string="foo=one&bar=two")
        context = Context(dict_={"request": self.request})
        out = Template(
            "{% load query_transform %}" "{% query_transform baz=9 %}"
        ).render(context=context)
        self.assertEqual(
            out, "?foo=one&amp;bar=two&amp;baz=9"
        )  # baz=9 added to the existing query arguments

    def test_query_transform_update(self):
        self.request = self.client_class
        self.request.GET = QueryDict(query_string="foo=one&bar=two")
        context = Context(dict_={"request": self.request})
        out = Template(
            "{% load query_transform %}" "{% query_transform bar='three' %}"
        ).render(context=context)
        self.assertEqual(out, "?foo=one&amp;bar=three")  # bar's value replaced


class TestQueryChop(TestCase):
    def test_query_chop_remove_present(self):
        self.request = self.client_class
        self.request.GET = QueryDict(query_string="foo=one&bar=two")
        context = Context(dict_={"request": self.request})
        out = Template("{% load query_transform %}" "{% query_chop 'bar' %}").render(
            context=context
        )
        self.assertEqual(out, "?foo=one")

    def test_query_chop_remove_non_existent(self):
        self.request = self.client_class
        self.request.GET = QueryDict(query_string="foo=one&bar=two")
        context = Context(dict_={"request": self.request})
        out = Template("{% load query_transform %}" "{% query_chop 'baz' %}").render(
            context=context
        )
        self.assertEqual(out, "?foo=one&amp;bar=two")

    def test_query_chop_remove_from_empty(self):
        self.request = self.client_class
        self.request.GET = QueryDict()
        context = Context(dict_={"request": self.request})
        out = Template("{% load query_transform %}" "{% query_chop 'baz' %}").render(
            context=context
        )
        self.assertEqual(out, "?")


class TestFeatureFlagEnabled(TestCase):
    def test_feature_flag_enabled_true(self):
        settings.IS_AVL_FEATURE_FLAG_ENABLED = True
        context = Context(dict_={"request": self.client})
        context["request"].path = "/"
        out = Template(
            "{% load feature_flag_enabled %}" "{% is_avl_feature_flag_enabled %}"
        ).render(context=context)
        self.assertEqual(out, "True")

    def test_feature_flag_enabled_false(self):
        settings.IS_AVL_FEATURE_FLAG_ENABLED = False
        context = Context(dict_={"request": self.client})
        context["request"].path = "/"
        out = Template(
            "{% load feature_flag_enabled %}" "{% is_avl_feature_flag_enabled %}"
        ).render(context=context)
        self.assertEqual(out, "False")
