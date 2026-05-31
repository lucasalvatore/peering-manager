import json
from types import SimpleNamespace as NS

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from bgp.models import ASPath, Community, PrefixList

from ..enums import PolicyTermAction, RoutingPolicyType
from ..forms import PolicyTermForm
from ..models import (
    PolicyTerm,
    RoutingPolicy,
    RoutingPolicyVersion,
    TermAction,
    TermMatch,
)
from ..policy_history import record, restore, snapshot_policy
from ..policy_render import (
    render_policy_statement,
    render_preview,
    render_prefix_list,
)


class RendererPureTestCase(SimpleTestCase):
    """The core rendering helpers are duck-typed and need no database."""

    def test_render_policy_statement(self):
        term = NS(
            name="ACCEPT-AGGREGATES",
            action="accept",
            matches=[
                NS(match_type="prefix-list", values=["PLIST-V4", "PLIST-V6"]),
                NS(match_type="protocol", values=["bgp"]),
            ],
            actions=[
                NS(action_type="local-preference", value="200"),
                NS(action_type="as-path-prepend", value="3"),
                NS(action_type="community-add", value="CLIST-DAL-TRANSIT"),
            ],
        )
        policy = NS(name="RMAP-AS1299-EXPORT", default_action="reject", terms=[term])
        out = render_policy_statement(policy)

        self.assertIn('policy-statement "RMAP-AS1299-EXPORT" {', out)
        self.assertIn('named-entry "ACCEPT-AGGREGATES" {', out)
        self.assertIn('prefix-list ["PLIST-V4" "PLIST-V6"]', out)
        # protocol renders as a nested block with unquoted names
        self.assertIn("protocol {", out)
        self.assertIn("name [bgp]", out)
        # community-add aggregates into a community { add [...] } block
        self.assertIn("community {", out)
        self.assertIn('add ["CLIST-DAL-TRANSIT"]', out)
        self.assertIn("local-preference 200", out)
        self.assertIn("action-type reject", out)

    def test_render_prefix_list_member_params(self):
        obj = NS(
            name="PLIST-V4-CUSTOMER",
            prefixes=[
                {"prefix": "192.0.2.0/24", "type": "orlonger"},
                {
                    "prefix": "198.51.100.0/24",
                    "type": "prefix-length-range",
                    "params": {"start-length": "25", "end-length": "27"},
                },
            ],
        )
        out = render_prefix_list(obj)
        self.assertIn('prefix-list "PLIST-V4-CUSTOMER" {', out)
        self.assertIn("prefix 192.0.2.0/24 type orlonger { }", out)
        self.assertIn("prefix 198.51.100.0/24 type prefix-length-range {", out)
        self.assertIn("start-length 25", out)


class PolicyTermModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutingPolicy.objects.create(
            name="RMAP-AS1299-EXPORT",
            slug="rmap-as1299-export",
            type=RoutingPolicyType.EXPORT,
            default_action=PolicyTermAction.REJECT,
        )
        PrefixList.objects.create(
            name="PLIST-V4-PUBLIC",
            slug="plist-v4-public",
            prefixes=[{"prefix": "192.0.2.0/24", "type": "exact"}],
        )
        cls.term = PolicyTerm.objects.create(
            routing_policy=cls.policy,
            name="ACCEPT-PUBLIC",
            sequence=10,
            action=PolicyTermAction.ACCEPT,
        )
        TermMatch.objects.create(
            term=cls.term, match_type="prefix-list", values=["PLIST-V4-PUBLIC"]
        )
        TermAction.objects.create(
            term=cls.term, action_type="local-preference", value="100"
        )

    def test_relationships(self):
        self.assertEqual(self.policy.terms.count(), 1)
        self.assertEqual(self.term.matches.count(), 1)
        self.assertEqual(self.term.actions.count(), 1)

    def test_preview_resolves_referenced_objects(self):
        preview = render_preview(self.policy)
        # Referenced prefix-list object is rendered alongside the policy.
        self.assertIn('prefix-list "PLIST-V4-PUBLIC" {', preview)
        self.assertIn("prefix 192.0.2.0/24 type exact { }", preview)
        self.assertIn('policy-statement "RMAP-AS1299-EXPORT" {', preview)
        self.assertIn("local-preference 100", preview)
        self.assertTrue(preview.startswith("policy-options {"))

    def test_unique_term_name_per_policy(self):
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            PolicyTerm.objects.create(
                routing_policy=self.policy, name="ACCEPT-PUBLIC", sequence=20
            )


class PolicyTermFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutingPolicy.objects.create(
            name="RMAP-AS174-IMPORT",
            slug="rmap-as174-import",
            type=RoutingPolicyType.IMPORT,
        )

    def test_form_creates_matches_and_actions(self):
        form = PolicyTermForm(
            data={
                "routing_policy": self.policy.pk,
                "name": "TAG-TRANSIT",
                "sequence": 10,
                "action": PolicyTermAction.ACCEPT,
                "description": "",
                "matches": [{"match_type": "community", "values": ["CLIST-TRANSIT"]}],
                "actions": [{"action_type": "local-preference", "value": "100"}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        term = form.save()
        self.assertEqual(term.matches.count(), 1)
        self.assertEqual(term.actions.count(), 1)
        self.assertEqual(term.matches.first().values, ["CLIST-TRANSIT"])

    def test_form_resyncs_children_on_edit(self):
        term = PolicyTerm.objects.create(
            routing_policy=self.policy, name="T1", sequence=10
        )
        TermMatch.objects.create(term=term, match_type="protocol", values=["bgp"])
        form = PolicyTermForm(
            data={
                "routing_policy": self.policy.pk,
                "name": "T1",
                "sequence": 10,
                "action": PolicyTermAction.ACCEPT,
                "description": "",
                "matches": [{"match_type": "as-path", "values": ["ASPATH-CUST"]}],
                "actions": [],
            },
            instance=term,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        term.refresh_from_db()
        self.assertEqual(term.matches.count(), 1)
        self.assertEqual(term.matches.first().match_type, "as-path")


class PolicyTermViewSaveTestCase(TestCase):
    """
    Exercises the full edit-view POST path (incl. the change-logging / webhook
    serialization that the form-only tests skip), which is where structured
    matches/actions get persisted from the editor's JSON.
    """

    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutingPolicy.objects.create(
            name="RMAP-AS3356-EXPORT",
            slug="rmap-as3356-export",
            type=RoutingPolicyType.EXPORT,
        )
        cls.user = get_user_model().objects.create_user(
            username="editor", password="x", is_superuser=True, is_staff=True
        )

    def test_edit_view_persists_matches_and_actions(self):
        client = Client()
        client.force_login(self.user)
        term = PolicyTerm.objects.create(
            routing_policy=self.policy, name="ACCEPT", sequence=10
        )
        resp = client.post(
            reverse("peering:policyterm_edit", kwargs={"pk": term.pk}),
            data={
                "routing_policy": self.policy.pk,
                "name": "ACCEPT",
                "sequence": 10,
                "action": PolicyTermAction.ACCEPT,
                "description": "",
                "matches": json.dumps(
                    [{"match_type": "protocol", "values": ["bgp"]}]
                ),
                "actions": json.dumps(
                    [{"action_type": "local-preference", "value": "200"}]
                ),
            },
        )
        # 302 redirect = saved without the webhook-serialization 500.
        self.assertEqual(resp.status_code, 302)
        term.refresh_from_db()
        self.assertEqual(term.matches.first().match_type, "protocol")
        self.assertEqual(term.actions.first().value, "200")

    def test_editor_page_renders_structured_widgets(self):
        client = Client()
        client.force_login(self.user)
        PrefixList.objects.create(name="PLIST-V4-X", slug="plist-v4-x")
        resp = client.get(reverse("peering:policyterm_add"))
        html = resp.content.decode()
        self.assertContains(resp, 'id="match-rows"')
        self.assertContains(resp, 'id="editor-config"')
        # object names are pre-populated into the editor config
        self.assertIn("PLIST-V4-X", html)

    def test_new_term_is_appended_without_sequence_field(self):
        client = Client()
        client.force_login(self.user)
        PolicyTerm.objects.create(
            routing_policy=self.policy, name="FIRST", sequence=10
        )
        resp = client.post(
            reverse("peering:policyterm_add"),
            data={
                "routing_policy": self.policy.pk,
                "name": "SECOND",
                "action": PolicyTermAction.ACCEPT,
                "description": "",
                "matches": "[]",
                "actions": "[]",
            },
        )
        self.assertEqual(resp.status_code, 302)
        second = PolicyTerm.objects.get(routing_policy=self.policy, name="SECOND")
        self.assertEqual(second.sequence, 20)  # appended after FIRST


class PolicyTermMoveTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutingPolicy.objects.create(
            name="RMAP-AS6939-EXPORT",
            slug="rmap-as6939-export",
            type=RoutingPolicyType.EXPORT,
        )
        cls.a = PolicyTerm.objects.create(
            routing_policy=cls.policy, name="A", sequence=10
        )
        cls.b = PolicyTerm.objects.create(
            routing_policy=cls.policy, name="B", sequence=20
        )
        cls.c = PolicyTerm.objects.create(
            routing_policy=cls.policy, name="C", sequence=30
        )
        cls.user = get_user_model().objects.create_user(
            username="mover", password="x", is_superuser=True, is_staff=True
        )

    def _order(self):
        return [t.name for t in self.policy.terms.all()]

    def test_move_down(self):
        client = Client()
        client.force_login(self.user)
        resp = client.post(
            reverse(
                "peering:policyterm_move", kwargs={"pk": self.a.pk, "direction": "down"}
            )
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self._order(), ["B", "A", "C"])

    def test_move_up(self):
        client = Client()
        client.force_login(self.user)
        client.post(
            reverse(
                "peering:policyterm_move", kwargs={"pk": self.c.pk, "direction": "up"}
            )
        )
        self.assertEqual(self._order(), ["A", "C", "B"])

    def test_move_up_at_top_is_noop(self):
        client = Client()
        client.force_login(self.user)
        client.post(
            reverse(
                "peering:policyterm_move", kwargs={"pk": self.a.pk, "direction": "up"}
            )
        )
        self.assertEqual(self._order(), ["A", "B", "C"])


class RoutingPolicyByDeviceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        from devices.models import Router

        cls.router = Router.objects.create(name="br1-test", hostname="br1.test")
        cls.other = Router.objects.create(name="br2-test", hostname="br2.test")
        cls.imp = RoutingPolicy.objects.create(
            name="RMAP-IMPORT", slug="rmap-import",
            type=RoutingPolicyType.IMPORT, router=cls.router,
        )
        cls.exp = RoutingPolicy.objects.create(
            name="RMAP-EXPORT", slug="rmap-export",
            type=RoutingPolicyType.EXPORT, router=cls.router,
        )
        cls.both = RoutingPolicy.objects.create(
            name="RMAP-BOTH", slug="rmap-both",
            type=RoutingPolicyType.IMPORT_EXPORT, router=cls.router,
        )
        cls.elsewhere = RoutingPolicy.objects.create(
            name="RMAP-OTHER", slug="rmap-other",
            type=RoutingPolicyType.IMPORT, router=cls.other,
        )
        cls.user = get_user_model().objects.create_user(
            username="picker", password="x", is_superuser=True, is_staff=True
        )

    def test_picker_groups_policies_by_device(self):
        client = Client()
        client.force_login(self.user)
        resp = client.get(
            reverse("peering:routingpolicy_bydevice"), {"router": self.router.pk}
        )
        self.assertEqual(resp.status_code, 200)
        imports = set(resp.context["import_policies"].values_list("name", flat=True))
        exports = set(resp.context["export_policies"].values_list("name", flat=True))
        self.assertEqual(imports, {"RMAP-IMPORT", "RMAP-BOTH"})
        self.assertEqual(exports, {"RMAP-EXPORT", "RMAP-BOTH"})
        # a policy owned by another device is not shown
        self.assertNotIn("RMAP-OTHER", imports | exports)

    def test_picker_without_selection(self):
        client = Client()
        client.force_login(self.user)
        resp = client.get(reverse("peering:routingpolicy_bydevice"))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context["router"])


class RoutingPolicyNamingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        from devices.models import Router

        cls.r1 = Router.objects.create(name="rtr-a", hostname="a")
        cls.r2 = Router.objects.create(name="rtr-b", hostname="b")

    def test_same_name_different_device_allowed(self):
        RoutingPolicy.objects.create(
            name="RMAP-DUP", slug="rmap-dup", type=RoutingPolicyType.IMPORT,
            router=self.r1,
        )
        dup = RoutingPolicy(
            name="RMAP-DUP", slug="rmap-dup", type=RoutingPolicyType.IMPORT,
            router=self.r2,
        )
        dup.full_clean()  # must not raise
        dup.save()
        self.assertEqual(RoutingPolicy.objects.filter(name="RMAP-DUP").count(), 2)

    def test_duplicate_name_same_device_rejected(self):
        from django.core.exceptions import ValidationError

        RoutingPolicy.objects.create(
            name="RMAP-X", slug="rmap-x", type=RoutingPolicyType.IMPORT,
            router=self.r1,
        )
        dup = RoutingPolicy(
            name="RMAP-X", slug="rmap-x", type=RoutingPolicyType.IMPORT,
            router=self.r1,
        )
        with self.assertRaises(ValidationError):
            dup.full_clean()


class RoutingPolicyHistoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutingPolicy.objects.create(
            name="RMAP-AS2914-EXPORT",
            slug="rmap-as2914-export",
            type=RoutingPolicyType.EXPORT,
            default_action=PolicyTermAction.REJECT,
        )
        cls.user = get_user_model().objects.create_user(
            username="historian", password="x", is_superuser=True, is_staff=True
        )

    def _add_term(self, name, seq):
        term = PolicyTerm.objects.create(
            routing_policy=self.policy, name=name, sequence=seq
        )
        TermMatch.objects.create(term=term, match_type="protocol", values=["bgp"])
        return term

    def test_snapshot_captures_terms(self):
        self._add_term("T1", 10)
        snap = snapshot_policy(self.policy)
        self.assertEqual(snap["default_action"], PolicyTermAction.REJECT)
        self.assertEqual(len(snap["terms"]), 1)
        self.assertEqual(snap["terms"][0]["matches"][0]["match_type"], "protocol")

    def test_restore_rebuilds_terms(self):
        self._add_term("ORIGINAL", 10)
        version = record(self.policy, comment="checkpoint")
        # Mutate the policy after the checkpoint.
        self.policy.terms.all().delete()
        self._add_term("CHANGED", 10)
        self.assertEqual([t.name for t in self.policy.terms.all()], ["CHANGED"])
        # Roll back.
        restore(self.policy, version)
        self.assertEqual([t.name for t in self.policy.terms.all()], ["ORIGINAL"])
        self.assertEqual(self.policy.terms.first().matches.first().match_type, "protocol")

    def test_prune_keeps_last_20(self):
        from ..policy_history import KEEP

        for i in range(KEEP + 5):
            record(self.policy, comment=f"v{i}")
        self.assertEqual(self.policy.versions.count(), KEEP)

    def test_snapshot_view_creates_version(self):
        self._add_term("T1", 10)
        client = Client()
        client.force_login(self.user)
        resp = client.post(
            reverse("peering:routingpolicy_snapshot", kwargs={"pk": self.policy.pk}),
            data={"comment": "manual save"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.policy.versions.count(), 1)
        self.assertEqual(self.policy.versions.first().comment, "manual save")

    def test_restore_view_rolls_back(self):
        self._add_term("FIRST", 10)
        version = record(self.policy)
        self.policy.terms.all().delete()
        self._add_term("SECOND", 10)
        client = Client()
        client.force_login(self.user)
        resp = client.post(
            reverse(
                "peering:routingpolicy_restore",
                kwargs={"pk": self.policy.pk, "version": version.pk},
            )
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual([t.name for t in self.policy.terms.all()], ["FIRST"])
