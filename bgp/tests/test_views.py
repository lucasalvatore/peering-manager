import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from utils.enums import Colour
from utils.testing import ViewTestCases

from ..enums import CommunityType
from ..models import *


class CommunityTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Community

    @classmethod
    def setUpTestData(cls):
        Community.objects.bulk_create(
            [
                Community(name="Community 1", slug="community-1", value="64500:1"),
                Community(name="Community 2", slug="community-2", value="64500:2"),
                Community(name="Community 3", slug="community-3", value="64500:3"),
            ]
        )

        # slug is auto-derived from name and no longer a form field
        cls.form_data = {
            "name": "Community 4",
            "value": "64500:4",
            "type": CommunityType.INGRESS,
            "comments": "",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "New description"}


class RelationshipTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Relationship

    @classmethod
    def setUpTestData(cls):
        Relationship.objects.bulk_create(
            [
                Relationship(name="Test1", slug="test1", color=Colour.YELLOW),
                Relationship(name="Test2", slug="test2", color=Colour.WHITE),
                Relationship(name="Test3", slug="test3", color=Colour.BLACK),
            ]
        )

        cls.form_data = {"name": "Test4", "slug": "test4", "color": Colour.RED}
        cls.bulk_edit_data = {"description": "Foo"}


class PrefixListEditorViewTestCase(TestCase):
    """The structured prefix editor posts members as JSON via a hidden field."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="pl-editor", password="x", is_superuser=True, is_staff=True
        )

    def test_add_view_persists_structured_prefixes(self):
        client = Client()
        client.force_login(self.user)
        resp = client.post(
            reverse("bgp:prefixlist_add"),
            data={
                "name": "PLIST-V4-TESTVIEW",
                "slug": "plist-v4-testview",
                "family": 4,
                "prefixes": json.dumps(
                    [
                        {"prefix": "203.0.113.0/24", "type": "orlonger"},
                        {
                            "prefix": "198.51.100.0/24",
                            "type": "prefix-length-range",
                            "params": {"start-length": "25", "end-length": "27"},
                        },
                    ]
                ),
            },
        )
        self.assertEqual(resp.status_code, 302)
        obj = PrefixList.objects.get(name="PLIST-V4-TESTVIEW")
        self.assertEqual(len(obj.prefixes), 2)
        self.assertEqual(obj.prefixes[1]["params"]["start-length"], "25")

    def test_editor_page_renders_row_editor(self):
        client = Client()
        client.force_login(self.user)
        resp = client.get(reverse("bgp:prefixlist_add"))
        self.assertContains(resp, 'id="prefix-rows"')
        self.assertContains(resp, 'id="editor-config"')


class ASPathEditorViewTestCase(TestCase):
    """The AS-path editor posts regexps as a JSON list via a hidden field."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="asp-editor", password="x", is_superuser=True, is_staff=True
        )

    def test_add_view_persists_regexps(self):
        client = Client()
        client.force_login(self.user)
        resp = client.post(
            reverse("bgp:aspath_add"),
            data={
                "name": "ASPATH-TESTVIEW",
                "slug": "aspath-testview",
                "regexps": json.dumps(["^1299 .*", ".* 174$"]),
            },
        )
        self.assertEqual(resp.status_code, 302)
        obj = ASPath.objects.get(name="ASPATH-TESTVIEW")
        self.assertEqual(obj.regexps, ["^1299 .*", ".* 174$"])

    def test_editor_page_renders_row_editor(self):
        client = Client()
        client.force_login(self.user)
        resp = client.get(reverse("bgp:aspath_add"))
        self.assertContains(resp, 'id="regexp-rows"')
