from django.test import TestCase

from utils.enums import Colour

from ..enums import *
from ..forms import *


class CommunityTest(TestCase):
    def test_community_form(self):
        test = CommunityForm(
            data={
                "name": "CLIST-FOO",
                "members": ["1299:333", "1299:444", "1299:555"],
            }
        )
        self.assertTrue(test.is_valid(), test.errors)
        obj = test.save()
        self.assertEqual(obj.members, ["1299:333", "1299:444", "1299:555"])


class Relationshipest(TestCase):
    def test_relationship_form(self):
        test = RelationshipForm(
            data={"name": "test", "slug": "test", "color": Colour.BLUE}
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class PrefixListTest(TestCase):
    def test_prefix_list_form(self):
        test = PrefixListForm(
            data={
                "name": "PLIST-V4-TEST",
                "slug": "plist-v4-test",
                "family": PrefixListFamily.IPV4,
                "prefixes": [{"prefix": "192.0.2.0/24", "type": "orlonger"}],
            }
        )
        self.assertTrue(test.is_valid(), test.errors)
        obj = test.save()
        self.assertEqual(obj.prefixes[0]["prefix"], "192.0.2.0/24")


class ASPathTest(TestCase):
    def test_as_path_form(self):
        test = ASPathForm(
            data={
                "name": "ASPATH-CUST",
                "slug": "aspath-cust",
                "regexps": ["^1299 .*", ".* 174$"],
            }
        )
        self.assertTrue(test.is_valid(), test.errors)
        obj = test.save()
        self.assertEqual(len(obj.regexps), 2)
