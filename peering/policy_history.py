"""Save/restore version history for structured routing policies.

A `RoutingPolicyVersion` captures a point-in-time snapshot of a policy's
default-action and terms (with their matches/actions). Versions are recorded
explicitly ("Save version") and a policy can be rolled back to any saved
version. The most recent ``KEEP`` versions per policy are retained.
"""

from __future__ import annotations

from django.db import transaction

from .models import RoutingPolicyVersion

# Number of versions to keep per routing policy.
KEEP = 20


def snapshot_policy(routing_policy) -> dict:
    """Serialise a policy's structured content to a plain dict."""
    return {
        "default_action": routing_policy.default_action,
        "terms": [
            {
                "name": term.name,
                "sequence": term.sequence,
                "action": term.action,
                "description": term.description,
                "matches": [
                    {"match_type": m.match_type, "values": m.values}
                    for m in term.matches.all()
                ],
                "actions": [
                    {"action_type": a.action_type, "value": a.value}
                    for a in term.actions.all()
                ],
            }
            for term in routing_policy.terms.all()
        ],
    }


def _prune(routing_policy) -> None:
    stale = routing_policy.versions.all()[KEEP:]
    ids = [v.pk for v in stale]
    if ids:
        RoutingPolicyVersion.objects.filter(pk__in=ids).delete()


def record(routing_policy, comment: str = "") -> RoutingPolicyVersion:
    """Snapshot the policy's current state as a new version, then prune."""
    version = RoutingPolicyVersion.objects.create(
        routing_policy=routing_policy,
        comment=comment,
        snapshot=snapshot_policy(routing_policy),
    )
    _prune(routing_policy)
    return version


@transaction.atomic
def restore(routing_policy, version) -> RoutingPolicyVersion:
    """
    Replace the policy's structured content with ``version``'s snapshot and
    record the restore as a new version (so it too can be rolled back).
    """
    data = version.snapshot or {}

    routing_policy.terms.all().delete()
    if "default_action" in data:
        routing_policy.default_action = data["default_action"]
        routing_policy.save()

    for term_data in data.get("terms", []):
        term = routing_policy.terms.create(
            name=term_data["name"],
            sequence=term_data.get("sequence", 0),
            action=term_data.get("action", "accept"),
            description=term_data.get("description", ""),
        )
        for m in term_data.get("matches", []):
            term.matches.create(
                match_type=m["match_type"], values=m.get("values") or []
            )
        for a in term_data.get("actions", []):
            term.actions.create(action_type=a["action_type"], value=a.get("value"))

    return record(
        routing_policy,
        comment=f"Restored from version of {version.created:%Y-%m-%d %H:%M}",
    )
