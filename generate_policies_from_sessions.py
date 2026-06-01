#!/usr/bin/env python
"""
Generate per-device routing policies from direct peering sessions.

For every direct peering session, create (if missing) an import and export
policy named RMAP-AS<peer-asn>-IMPORT / RMAP-AS<peer-asn>-EXPORT owned by the
session's router (device). One pair per (device, peer ASN). Idempotent.

Usage:  uv run python generate_policies_from_sessions.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "peering_manager.settings")
django.setup()

from django.utils.text import slugify  # noqa: E402

from peering.enums import PolicyTermAction, RoutingPolicyType  # noqa: E402
from peering.models import DirectPeeringSession, RoutingPolicy  # noqa: E402

# Collect unique (router, peer-asn) pairs from direct sessions.
pairs = {}  # (router_id, asn) -> (router_obj, asn)
skipped_no_router = skipped_no_as = 0
for s in DirectPeeringSession.objects.select_related("router", "autonomous_system"):
    if s.router is None:
        skipped_no_router += 1
        continue
    if s.autonomous_system is None:
        skipped_no_as += 1
        continue
    pairs[(s.router_id, s.autonomous_system.asn)] = (s.router, s.autonomous_system.asn)

created = existed = 0
for router, asn in pairs.values():
    for suffix, ptype in (
        ("IMPORT", RoutingPolicyType.IMPORT),
        ("EXPORT", RoutingPolicyType.EXPORT),
    ):
        name = f"RMAP-AS{asn}-{suffix}"
        _, made = RoutingPolicy.objects.get_or_create(
            router=router,
            name=name,
            defaults=dict(
                slug=slugify(name),
                type=ptype,
                default_action=PolicyTermAction.REJECT,
                weight=0,
                address_family=0,
            ),
        )
        created += int(made)
        existed += int(not made)

print(f"direct sessions skipped (no router): {skipped_no_router}")
print(f"direct sessions skipped (no peer AS): {skipped_no_as}")
print(f"unique (device, peer-ASN) pairs: {len(pairs)}")
print(f"policies created: {created}   already existed: {existed}")
print(f"total routing policies now: {RoutingPolicy.objects.count()}")
