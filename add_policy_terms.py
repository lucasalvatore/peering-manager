#!/usr/bin/env python
"""
Populate the generated per-device policies with their standard terms.

Import policies (RMAP-AS<asn>-IMPORT) get two terms above the default-action:
  SET-COMMUNITIES : action next-entry, community add [CLIST-<SITE>-TRANSIT]
  ACCEPT-BGP      : from protocol bgp, action accept, local-preference 100
Export policies (RMAP-AS<asn>-EXPORT) get one term:
  ACCEPT-PUBLIC-AGGREGATES : from prefix-list [V4/V6 public aggregates], accept

<SITE> is the device name minus its br1/br2 prefix, uppercased
(br1-us-sjc01 -> US-SJC01). Idempotent.

Usage:  uv run python add_policy_terms.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "peering_manager.settings")
django.setup()

from peering.enums import PolicyTermAction  # noqa: E402
from peering.models import PolicyTerm, RoutingPolicy  # noqa: E402


def site_of(router_name):
    """br1-us-sjc01 -> US-SJC01 (drop the brN prefix segment)."""
    parts = router_name.split("-")
    return "-".join(parts[1:]).upper()


imp_created = exp_created = 0

# ---- import policies -------------------------------------------------------
for policy in RoutingPolicy.objects.filter(
    name__regex=r"^RMAP-AS[0-9]+-IMPORT$", router__isnull=False
).select_related("router"):
    community = f"CLIST-{site_of(policy.router.name)}-TRANSIT"

    t1, made = PolicyTerm.objects.get_or_create(
        routing_policy=policy, name="SET-COMMUNITIES",
        defaults=dict(sequence=10, action=PolicyTermAction.NEXT_ENTRY),
    )
    if made:
        t1.actions.create(action_type="community-add", value=community)
        imp_created += 1

    t2, made = PolicyTerm.objects.get_or_create(
        routing_policy=policy, name="ACCEPT-BGP",
        defaults=dict(sequence=20, action=PolicyTermAction.ACCEPT),
    )
    if made:
        t2.matches.create(match_type="protocol", values=["bgp"])
        t2.actions.create(action_type="local-preference", value="100")
        imp_created += 1

# ---- export policies -------------------------------------------------------
for policy in RoutingPolicy.objects.filter(name__regex=r"^RMAP-AS[0-9]+-EXPORT$"):
    t, made = PolicyTerm.objects.get_or_create(
        routing_policy=policy, name="ACCEPT-PUBLIC-AGGREGATES",
        defaults=dict(sequence=10, action=PolicyTermAction.ACCEPT),
    )
    if made:
        t.matches.create(
            match_type="prefix-list",
            values=["PLIST-V4-PUBLIC-AGGREGATES", "PLIST-V6-PUBLIC-AGGREGATES"],
        )
        exp_created += 1

print(f"import policy terms created: {imp_created}")
print(f"export policy terms created: {exp_created}")
print(f"total policy terms now: {PolicyTerm.objects.count()}")
