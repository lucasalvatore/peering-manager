"""Human-readable preview renderer for structured routing policies.

This reconstructs an on-device ``policy-statement`` syntax (Nokia SR OS /
MD-CLI style) from the structured `RoutingPolicy` / `PolicyTerm` model purely
as a *preview* so
operators can eyeball what they've entered. It is NOT an authoritative config
generator — Peering Manager renders real device config from its Jinja2
templates; this just visualises the structured policy.

A few match/action kinds render as nested blocks to match the device syntax:
  - match  ``protocol``         -> ``protocol { name [bgp] }``      (unquoted)
  - action ``community-add``    -> ``community { add ["CLIST-..."] }``
  - action ``community-remove`` -> ``community { remove ["..."] }``
Everything else renders flat: ``<type> ["A" "B"]`` for matches, ``<type> <value>``
for action modifiers (local-preference, as-path-prepend, metric, ...).

Core rendering functions are duck-typed (they read plain attributes and accept
either Django related managers or plain iterables) so they can be unit-tested
without a database.
"""

from __future__ import annotations

INDENT = "    "

COMMUNITY_ADD_TYPES = {"community-add", "community add", "community_add"}
COMMUNITY_REMOVE_TYPES = {"community-remove", "community remove", "community_remove"}

# prefix-list member match type -> ordered sub-fields it takes.
PREFIX_TYPE_PARAMS = {
    "exact": [],
    "longer": [],
    "orlonger": [],
    "upto": ["upto-length"],
    "through": ["through-length"],
    "prefix-length-range": ["start-length", "end-length"],
    "address-mask": ["mask-pattern"],
}

# Which match/action kinds reference which object type (by name).
_MATCH_OBJECT = {
    "prefix-list": "prefix-list",
    "community": "community",
    "as-path": "as-path",
}
_ACTION_OBJECT = {
    "community-add": "community",
    "community-remove": "community",
    "community add": "community",
    "community remove": "community",
}


def _items(related):
    """Accept a Django related manager or a plain iterable."""
    if related is None:
        return []
    return related.all() if hasattr(related, "all") else related


def _fmt_values(values, quote: bool = True) -> str:
    inner = " ".join(f'"{v}"' if quote else f"{v}" for v in values)
    return f"[{inner}]"


def _render_match(match, depth: int) -> list[str]:
    pad = INDENT * depth
    values = list(match.values or [])
    if match.match_type == "protocol":
        return [
            f"{pad}protocol {{",
            f"{pad}{INDENT}name {_fmt_values(values, quote=False)}",
            f"{pad}}}",
        ]
    return [f"{pad}{match.match_type} {_fmt_values(values)}"]


def _render_term(term, depth: int) -> list[str]:
    pad = INDENT * depth
    lines = [f'{pad}named-entry "{term.name}" {{']

    matches = list(_items(term.matches))
    if matches:
        lines.append(f"{pad}{INDENT}from {{")
        for m in matches:
            lines += _render_match(m, depth + 2)
        lines.append(f"{pad}{INDENT}}}")

    lines.append(f"{pad}{INDENT}action {{")
    lines.append(f"{pad}{INDENT * 2}action-type {term.action}")

    comm_add, comm_remove, others = [], [], []
    for a in _items(term.actions):
        if a.action_type in COMMUNITY_ADD_TYPES and a.value:
            comm_add.append(a.value)
        elif a.action_type in COMMUNITY_REMOVE_TYPES and a.value:
            comm_remove.append(a.value)
        else:
            others.append(a)

    for a in others:
        if a.value not in (None, ""):
            lines.append(f"{pad}{INDENT * 2}{a.action_type} {a.value}")
        else:
            lines.append(f"{pad}{INDENT * 2}{a.action_type}")

    if comm_add or comm_remove:
        lines.append(f"{pad}{INDENT * 2}community {{")
        if comm_add:
            lines.append(f"{pad}{INDENT * 3}add {_fmt_values(comm_add)}")
        if comm_remove:
            lines.append(f"{pad}{INDENT * 3}remove {_fmt_values(comm_remove)}")
        lines.append(f"{pad}{INDENT * 2}}}")

    lines.append(f"{pad}{INDENT}}}")
    lines.append(f"{pad}}}")
    return lines


def render_prefix_list(obj) -> str:
    """Preview a `bgp.PrefixList` in device syntax."""
    lines = [f'prefix-list "{obj.name}" {{']
    for m in obj.prefixes or []:
        if not isinstance(m, dict):  # legacy free-form member
            lines.append(f"{INDENT}prefix {m} type exact {{ }}")
            continue
        p, ty = m.get("prefix", ""), m.get("type", "exact")
        params = m.get("params") or {}
        present = [
            (k, params[k]) for k in PREFIX_TYPE_PARAMS.get(ty, []) if params.get(k)
        ]
        if present:
            lines.append(f"{INDENT}prefix {p} type {ty} {{")
            for k, v in present:
                lines.append(f"{INDENT * 2}{k} {v}")
            lines.append(f"{INDENT}}}")
        else:
            lines.append(f"{INDENT}prefix {p} type {ty} {{ }}")
    lines.append("}")
    return "\n".join(lines)


def render_as_path(obj) -> str:
    """Preview a `bgp.ASPath` in device syntax."""
    lines = [f'as-path "{obj.name}" {{']
    for expr in obj.regexps or []:
        lines.append(f'{INDENT}expression "{expr}"')
    lines.append("}")
    return "\n".join(lines)


def render_community(obj) -> str:
    """Preview a `bgp.Community` in device syntax."""
    return f'community "{obj.name}" {{\n{INDENT}member "{obj.value}" {{ }}\n}}'


def referenced_object_keys(routing_policy) -> set:
    """Return the (obj_type, name) pairs a policy references in matches/actions."""
    keys = set()
    for term in _items(routing_policy.terms):
        for m in _items(term.matches):
            t = _MATCH_OBJECT.get(m.match_type)
            if t:
                for v in m.values or []:
                    keys.add((t, v))
        for a in _items(term.actions):
            t = _ACTION_OBJECT.get(a.action_type)
            if t and a.value:
                keys.add((t, a.value))
    return keys


def _indent(text: str, levels: int = 1) -> str:
    pad = INDENT * levels
    return "\n".join((pad + ln) if ln else ln for ln in text.split("\n"))


def render_policy(routing_policy) -> str:
    """Return the body of a ``policy-statement`` (entry-type, terms, default)."""
    lines = [f"{INDENT}entry-type named"]
    for term in _items(routing_policy.terms):
        lines += _render_term(term, depth=1)
    lines.append(f"{INDENT}default-action {{")
    lines.append(f"{INDENT * 2}action-type {routing_policy.default_action}")
    lines.append(f"{INDENT}}}")
    return "\n".join(lines)


def render_policy_statement(routing_policy) -> str:
    """The ``policy-statement "NAME" { ... }`` block (braces included)."""
    return (
        f'policy-statement "{routing_policy.name}" {{\n'
        f"{render_policy(routing_policy)}\n}}"
    )


def _render_object_keys(keys) -> list[str]:
    """Render the given (obj_type, name) objects (DB lookup, deduped, sorted).

    Imported lazily so the pure rendering helpers above stay import-safe
    without Django configured.
    """
    from bgp.models import ASPath, Community, PrefixList

    fetch = {
        "prefix-list": lambda n: PrefixList.objects.filter(name=n).first(),
        "as-path": lambda n: ASPath.objects.filter(name=n).first(),
        "community": lambda n: Community.objects.filter(name=n).first(),
    }
    render = {
        "prefix-list": render_prefix_list,
        "as-path": render_as_path,
        "community": render_community,
    }
    parts = []
    for obj_type, name in sorted(keys):
        obj = fetch[obj_type](name)
        if obj is not None:
            parts.append(render[obj_type](obj))
    return parts


def render_objects_preview(routing_policy) -> list[str]:
    """Render every reusable object referenced by a single policy."""
    return _render_object_keys(referenced_object_keys(routing_policy))


def render_preview(routing_policy) -> str:
    """Full preview: referenced objects + the policy, under ``policy-options``."""
    parts = render_objects_preview(routing_policy)
    parts.append(render_policy_statement(routing_policy))
    inner = "\n".join(parts)
    return "policy-options {\n" + _indent(inner, 1) + "\n}"


def render_policies(routing_policies) -> str:
    """Render many policies (e.g. all owned by a device) under one
    ``policy-options`` block, with referenced objects deduped across them."""
    policies = list(routing_policies)
    if not policies:
        return "policy-options {\n}"
    keys = set()
    for policy in policies:
        keys |= referenced_object_keys(policy)
    parts = _render_object_keys(keys)
    parts.extend(render_policy_statement(p) for p in policies)
    inner = "\n".join(parts)
    return "policy-options {\n" + _indent(inner, 1) + "\n}"
