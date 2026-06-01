"""
Default policy templates.

The "default" for a policy type is an editable template policy (a RoutingPolicy
with ``is_template=True`` and no router). Both per-device policy generation and
the "modified from default" comparison read from these templates, so editing a
template in the UI re-bases everything.

Templates use the token ``{site}`` wherever the per-device site belongs (e.g. a
community value ``CLIST-{site}-TRANSIT``); it is expanded to the device's site
(br1-us-sjc01 -> US-SJC01) when generating/comparing.
"""

from __future__ import annotations

SITE_TOKEN = "{site}"


def site_of(router_name: str) -> str:
    """br1-us-sjc01 -> US-SJC01 (drop the brN prefix segment)."""
    parts = router_name.split("-")
    return "-".join(parts[1:]).upper()


def _sub(text, site):
    if isinstance(text, str) and SITE_TOKEN in text:
        return text.replace(SITE_TOKEN, site) if site else text
    return text


def get_template(policy_type, nos="nokia"):
    """The template RoutingPolicy for a (type, NOS), or None."""
    from .models import RoutingPolicy

    return (
        RoutingPolicy.objects.filter(
            is_template=True, type=policy_type, nos=nos
        )
        .order_by("pk")
        .first()
    )


def _spec_from(routing_policy, site):
    terms = []
    for term in routing_policy.terms.all():
        matches = frozenset(
            (m.match_type, tuple(_sub(v, site) for v in (m.values or [])))
            for m in term.matches.all()
        )
        actions = frozenset(
            (a.action_type, _sub(a.value, site)) for a in term.actions.all()
        )
        terms.append((term.name, term.action, matches, actions))
    return {"default_action": routing_policy.default_action, "terms": terms}


def default_spec(routing_policy):
    """Expected default spec for a policy (from the template matching its type
    and the device's NOS, with the device site substituted), or None if there's
    no matching template / no site."""
    from .policy_render import device_nos

    nos = device_nos(routing_policy.router) if routing_policy.router else "nokia"
    template = get_template(routing_policy.type, nos)
    if template is None:
        return None
    site = site_of(routing_policy.router.name) if routing_policy.router else None
    # If the template references {site} but we have no device, we can't compare.
    if site is None and _template_needs_site(template):
        return None
    return _spec_from(template, site)


def _template_needs_site(template):
    for term in template.terms.all():
        if any(SITE_TOKEN in (a.value or "") for a in term.actions.all()):
            return True
        for m in term.matches.all():
            if any(SITE_TOKEN in v for v in (m.values or [])):
                return True
    return False


def actual_spec(routing_policy):
    terms = []
    for term in routing_policy.terms.all():
        matches = frozenset(
            (m.match_type, tuple(m.values or [])) for m in term.matches.all()
        )
        actions = frozenset((a.action_type, a.value) for a in term.actions.all())
        terms.append((term.name, term.action, matches, actions))
    return {"default_action": routing_policy.default_action, "terms": terms}


def is_modified(routing_policy):
    """True/False if the policy has a template baseline, else None.

    Templates themselves are never flagged as modified."""
    if routing_policy.is_template:
        return None
    expected = default_spec(routing_policy)
    if expected is None:
        return None
    return actual_spec(routing_policy) != expected
