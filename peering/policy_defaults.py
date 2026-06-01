"""
Compare a routing policy against the standard generated template, so the UI can
flag policies that have been customised ("modified from the default").

The template mirrors what scripts/add_policy_terms.py applies:
  import: SET-COMMUNITIES (next-entry, community-add CLIST-<SITE>-TRANSIT)
          + ACCEPT-BGP (protocol bgp, accept, local-preference 100)
  export: ACCEPT-PUBLIC-AGGREGATES (prefix-list V4/V6 aggregates, accept)
both with a reject default-action.
"""

from __future__ import annotations

from .enums import PolicyTermAction, RoutingPolicyType

PUBLIC_AGGREGATES = ["PLIST-V4-PUBLIC-AGGREGATES", "PLIST-V6-PUBLIC-AGGREGATES"]


def site_of(router_name: str) -> str:
    """br1-us-sjc01 -> US-SJC01 (drop the brN prefix segment)."""
    parts = router_name.split("-")
    return "-".join(parts[1:]).upper()


def _term(name, action, matches, actions):
    # matches/actions as frozensets so ordering within a term doesn't matter.
    return (
        name,
        action,
        frozenset((m, tuple(v)) for m, v in matches),
        frozenset(actions),
    )


def default_spec(routing_policy):
    """Expected default term spec for a templated policy, or None if the policy
    type isn't one we generate a template for (or lacks the data to derive it)."""
    if routing_policy.type == RoutingPolicyType.IMPORT:
        if not routing_policy.router:
            return None
        community = f"CLIST-{site_of(routing_policy.router.name)}-TRANSIT"
        return {
            "default_action": PolicyTermAction.REJECT,
            "terms": [
                _term("SET-COMMUNITIES", PolicyTermAction.NEXT_ENTRY, [],
                      [("community-add", community)]),
                _term("ACCEPT-BGP", PolicyTermAction.ACCEPT,
                      [("protocol", ["bgp"])], [("local-preference", "100")]),
            ],
        }
    if routing_policy.type == RoutingPolicyType.EXPORT:
        return {
            "default_action": PolicyTermAction.REJECT,
            "terms": [
                _term("ACCEPT-PUBLIC-AGGREGATES", PolicyTermAction.ACCEPT,
                      [("prefix-list", PUBLIC_AGGREGATES)], []),
            ],
        }
    return None


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
    """True/False if the policy is templated, else None (no baseline to compare)."""
    expected = default_spec(routing_policy)
    if expected is None:
        return None
    return actual_spec(routing_policy) != expected
