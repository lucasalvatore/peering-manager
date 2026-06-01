#!/usr/bin/env python
"""
Seed the editable default policy templates (RoutingPolicy is_template=True) that
per-device generation and the "modified from default" comparison read from.

  _DEFAULT-IMPORT : SET-COMMUNITIES (next-entry, community-add CLIST-{site}-TRANSIT)
                    + ACCEPT-BGP (protocol bgp, accept, local-preference 100)
  _DEFAULT-EXPORT : ACCEPT-PUBLIC-AGGREGATES (prefix-list V4/V6 aggregates, accept)

Idempotent (rebuilds the templates' terms each run).

Usage:  uv run python seed_default_templates.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "peering_manager.settings")
django.setup()

from django.utils.text import slugify  # noqa: E402

from peering.enums import PolicyTermAction, RoutingPolicyType  # noqa: E402
from peering.models import RoutingPolicy  # noqa: E402

TEMPLATES = {
    RoutingPolicyType.IMPORT: (
        "_DEFAULT-IMPORT",
        [
            dict(
                name="SET-COMMUNITIES", sequence=10,
                action=PolicyTermAction.NEXT_ENTRY,
                matches=[],
                actions=[("community-add", "CLIST-{site}-TRANSIT")],
            ),
            dict(
                name="ACCEPT-BGP", sequence=20, action=PolicyTermAction.ACCEPT,
                matches=[("protocol", ["bgp"])],
                actions=[("local-preference", "100")],
            ),
        ],
    ),
    RoutingPolicyType.EXPORT: (
        "_DEFAULT-EXPORT",
        [
            dict(
                name="ACCEPT-PUBLIC-AGGREGATES", sequence=10,
                action=PolicyTermAction.ACCEPT,
                matches=[(
                    "prefix-list",
                    ["PLIST-V4-PUBLIC-AGGREGATES", "PLIST-V6-PUBLIC-AGGREGATES"],
                )],
                actions=[],
            ),
        ],
    ),
}

for ptype, (name, terms) in TEMPLATES.items():
    policy, _ = RoutingPolicy.objects.update_or_create(
        name=name, router=None,
        defaults=dict(
            slug=slugify(name), type=ptype, is_template=True,
            default_action=PolicyTermAction.REJECT,
            description="Editable default template",
        ),
    )
    policy.terms.all().delete()
    for spec in terms:
        term = policy.terms.create(
            name=spec["name"], sequence=spec["sequence"], action=spec["action"]
        )
        for match_type, values in spec["matches"]:
            term.matches.create(match_type=match_type, values=values)
        for action_type, value in spec["actions"]:
            term.actions.create(action_type=action_type, value=value)
    print(f"seeded template {name} ({policy.terms.count()} terms)")
