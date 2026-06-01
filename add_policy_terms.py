#!/usr/bin/env python
"""
Populate the generated per-device policies with terms cloned from the editable
default templates (see seed_default_templates.py). The {site} token in the
template is expanded to each device's site (br1-us-sjc01 -> US-SJC01).

Only policies that have no terms yet are populated, so this won't clobber
customised policies. Idempotent.

Usage:  uv run python add_policy_terms.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "peering_manager.settings")
django.setup()

from peering.models import RoutingPolicy  # noqa: E402
from peering.policy_defaults import SITE_TOKEN, get_template, site_of  # noqa: E402


def clone_template_terms(policy, template, site):
    def sub(text):
        if isinstance(text, str) and site:
            return text.replace(SITE_TOKEN, site)
        return text

    for term in template.terms.all():
        new_term = policy.terms.create(
            name=term.name, sequence=term.sequence, action=term.action,
            description=term.description,
        )
        for m in term.matches.all():
            new_term.matches.create(
                match_type=m.match_type, values=[sub(v) for v in (m.values or [])]
            )
        for a in term.actions.all():
            new_term.actions.create(action_type=a.action_type, value=sub(a.value))


created = skipped_has_terms = skipped_no_template = 0
for policy in RoutingPolicy.objects.filter(
    name__regex=r"^RMAP-AS[0-9]+-(IMPORT|EXPORT)$", is_template=False
).select_related("router"):
    if policy.terms.exists():
        skipped_has_terms += 1
        continue
    template = get_template(policy.type)
    if template is None:
        skipped_no_template += 1
        continue
    site = site_of(policy.router.name) if policy.router else None
    clone_template_terms(policy, template, site)
    created += 1

print(f"policies populated from template: {created}")
print(f"skipped (already have terms):     {skipped_has_terms}")
print(f"skipped (no template for type):   {skipped_no_template}")
