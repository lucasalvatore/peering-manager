#!/usr/bin/env python
"""
One-off importer: pull data from a production peering-manager (v1.9.7) REST API
(optionally over a SOCKS proxy) and load it into this dev database via the ORM.

Reads objects in dependency order, mapping each prod object id -> local object
so foreign keys / M2M relations resolve. Idempotent (update_or_create on natural
keys). Runs as a script, so change-logging/webhook signals are inert.

Configuration is read from ~/.pm_prod_token (gitignored) or the environment, so
no instance-specific URL is committed:

    PM_TOKEN=<read-only API token>      (required)
    PM_URL=https://peering-manager...   (required; or env PM_PROD_URL)
    PM_PROXY=socks5h://127.0.0.1:8080   (optional; default shown)

Usage:  uv run python import_from_prod.py
"""

import json
import os
import subprocess
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "peering_manager.settings")
django.setup()

from bgp.models import Relationship  # noqa: E402
from devices.models import Platform, Router  # noqa: E402
from net.models import Connection  # noqa: E402
from peering.models import (  # noqa: E402
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)

_conf = {}
_path = os.path.expanduser("~/.pm_prod_token")
if os.path.exists(_path):
    with open(_path) as fh:
        for line in fh:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                _conf[k] = v

TOKEN = os.environ.get("PM_TOKEN") or _conf.get("PM_TOKEN")
BASE = (os.environ.get("PM_PROD_URL") or _conf.get("PM_URL") or "").rstrip("/")
PROXY = os.environ.get("PM_PROXY") or _conf.get("PM_PROXY", "socks5h://127.0.0.1:8080")
if not TOKEN or not BASE:
    sys.exit("Set PM_TOKEN and PM_URL in ~/.pm_prod_token (or PM_PROD_URL env).")

idmap = {}  # idmap[name][prod_id] = local_obj


def fetch_all(path):
    url = f"{BASE}{path}?limit=500"
    rows = []
    while url:
        raw = subprocess.run(
            ["curl", "-sS", "-m", "90", "-k", "-x", PROXY,
             "-H", f"Authorization: Token {TOKEN}", url],
            capture_output=True, text=True,
        ).stdout
        data = json.loads(raw)
        rows.extend(data["results"])
        url = data.get("next")
    return rows


def cv(x):
    """Choice fields arrive as {value,label}."""
    return x["value"] if isinstance(x, dict) and "value" in x else x


def ref(x):
    return x["id"] if isinstance(x, dict) and x else None


def local(kind, prod):
    return idmap.get(kind, {}).get(ref(prod))


def m2m(kind, lst):
    return [o for o in (idmap.get(kind, {}).get(r["id"]) for r in (lst or [])) if o]


def run(label, kind, rows, fn):
    idmap.setdefault(kind, {})
    ok = err = 0
    errors = []
    for row in rows:
        try:
            obj = fn(row)
            if obj is not None:
                idmap[kind][row["id"]] = obj
                ok += 1
        except Exception as e:  # noqa: BLE001
            err += 1
            if len(errors) < 3:
                errors.append(f"{row.get('display', row.get('id'))}: {e}")
    print(f"{label:32s} ok={ok:4d} err={err:3d}" + (f"  e.g. {errors}" if errors else ""))


# ---- importers -------------------------------------------------------------

def imp_platform(r):
    obj, _ = Platform.objects.update_or_create(
        slug=r["slug"],
        defaults=dict(
            name=r["name"], description=r.get("description", "") or "",
            napalm_driver=r.get("napalm_driver", "") or "",
            napalm_args=r.get("napalm_args"),
            password_algorithm=r.get("password_algorithm") or "",
        ),
    )
    return obj


def imp_relationship(r):
    obj, _ = Relationship.objects.update_or_create(
        slug=r["slug"],
        defaults=dict(name=r["name"], description=r.get("description", "") or "",
                      color=r.get("color", "") or "000000"),
    )
    return obj


def imp_rpolicy(r):
    obj, _ = RoutingPolicy.objects.update_or_create(
        slug=r["slug"], router=None,
        defaults=dict(
            name=r["name"], description=r.get("description", "") or "",
            type=cv(r["type"]), weight=r.get("weight", 0) or 0,
            address_family=cv(r.get("address_family", 0)) or 0,
            local_context_data=r.get("local_context_data"),
        ),
    )
    return obj


def imp_asn(r):
    obj, _ = AutonomousSystem.objects.update_or_create(
        asn=r["asn"],
        defaults=dict(
            name=r["name"], affiliated=r.get("affiliated", False) or False,
            irr_as_set=r.get("irr_as_set"),
            ipv6_max_prefixes=r.get("ipv6_max_prefixes") or 0,
            ipv4_max_prefixes=r.get("ipv4_max_prefixes") or 0,
            description=r.get("description", "") or "", comments=r.get("comments", "") or "",
            local_context_data=r.get("local_context_data"),
        ),
    )
    obj.import_routing_policies.set(m2m("rpolicy", r.get("import_routing_policies")))
    obj.export_routing_policies.set(m2m("rpolicy", r.get("export_routing_policies")))
    return obj


def imp_router(r):
    obj, _ = Router.objects.update_or_create(
        name=r["name"],
        defaults=dict(
            hostname=r.get("hostname", "") or "",
            platform=local("platform", r.get("platform")),
            local_autonomous_system=local("asn", r.get("local_autonomous_system")),
            status=cv(r.get("status")) or "enabled",
            encrypt_passwords=r.get("encrypt_passwords", False) or False,
            poll_bgp_sessions_state=r.get("poll_bgp_sessions_state", False) or False,
            comments=r.get("comments", "") or "", description=r.get("description", "") or "",
            netbox_device_id=r.get("netbox_device_id") or 0,
            local_context_data=r.get("local_context_data"),
        ),
    )
    return obj


def imp_ix(r):
    obj, _ = InternetExchange.objects.update_or_create(
        slug=r["slug"],
        defaults=dict(
            name=r["name"], description=r.get("description", "") or "",
            status=cv(r.get("status")) or "enabled",
            local_autonomous_system=local("asn", r.get("local_autonomous_system")),
            local_context_data=r.get("local_context_data"),
        ),
    )
    obj.import_routing_policies.set(m2m("rpolicy", r.get("import_routing_policies")))
    obj.export_routing_policies.set(m2m("rpolicy", r.get("export_routing_policies")))
    return obj


def imp_group(r):
    obj, _ = BGPGroup.objects.update_or_create(
        slug=r["slug"],
        defaults=dict(
            name=r["name"], description=r.get("description", "") or "",
            status=cv(r.get("status")) or "enabled",
            local_context_data=r.get("local_context_data"),
        ),
    )
    obj.import_routing_policies.set(m2m("rpolicy", r.get("import_routing_policies")))
    obj.export_routing_policies.set(m2m("rpolicy", r.get("export_routing_policies")))
    return obj


def imp_connection(r):
    # Connection has no name/slug; key on (IXP, router, ipv4) which is unique
    # in practice.
    obj, _ = Connection.objects.update_or_create(
        internet_exchange_point=local("ix", r.get("internet_exchange_point")),
        router=local("router", r.get("router")),
        ipv4_address=r.get("ipv4_address") or None,
        defaults=dict(
            status=cv(r.get("status")) or "enabled",
            vlan=r.get("vlan"), mac_address=r.get("mac_address") or None,
            ipv6_address=r.get("ipv6_address") or None,
            interface=r.get("interface", "") or "",
            description=r.get("description", "") or "", comments=r.get("comments", "") or "",
            local_context_data=r.get("local_context_data"),
        ),
    )
    return obj


def imp_direct(r):
    # Plain create for a faithful 1:1 copy (prod has near-duplicate sessions
    # with no distinguishing natural key); sessions are cleared before import.
    obj = DirectPeeringSession.objects.create(
        router=local("router", r.get("router")),
        ip_address=r["ip_address"],
        autonomous_system=local("asn", r.get("autonomous_system")),
        bgp_group=local("group", r.get("bgp_group")),
        local_autonomous_system=local("asn", r.get("local_autonomous_system")),
        local_ip_address=r.get("local_ip_address") or None,
        status=cv(r.get("status")) or "enabled",
        relationship=local("relationship", r.get("relationship")),
        password=r.get("password"), encrypted_password=r.get("encrypted_password"),
        multihop_ttl=r.get("multihop_ttl") or 1, passive=r.get("passive", False) or False,
        connection=local("connection", r.get("connection")),
        service_reference=r.get("service_reference"),
        comments=r.get("comments", "") or "", description=r.get("description", "") or "",
        local_context_data=r.get("local_context_data"),
    )
    obj.import_routing_policies.set(m2m("rpolicy", r.get("import_routing_policies")))
    obj.export_routing_policies.set(m2m("rpolicy", r.get("export_routing_policies")))
    return obj


def imp_ixsession(r):
    obj = InternetExchangePeeringSession.objects.create(
        ip_address=r["ip_address"],
        ixp_connection=local("connection", r.get("ixp_connection")),
        autonomous_system=local("asn", r.get("autonomous_system")),
        status=cv(r.get("status")) or "enabled",
        password=r.get("password"), encrypted_password=r.get("encrypted_password"),
        multihop_ttl=r.get("multihop_ttl") or 1, passive=r.get("passive", False) or False,
        is_route_server=r.get("is_route_server", False) or False,
        service_reference=r.get("service_reference"),
        comments=r.get("comments", "") or "", description=r.get("description", "") or "",
        local_context_data=r.get("local_context_data"),
    )
    obj.import_routing_policies.set(m2m("rpolicy", r.get("import_routing_policies")))
    obj.export_routing_policies.set(m2m("rpolicy", r.get("export_routing_policies")))
    return obj


PLAN = [
    ("Platforms", "platform", "/api/devices/platforms/", imp_platform),
    ("Relationships", "relationship", "/api/bgp/relationships/", imp_relationship),
    ("Routing policies", "rpolicy", "/api/peering/routing-policies/", imp_rpolicy),
    ("Autonomous systems", "asn", "/api/peering/autonomous-systems/", imp_asn),
    ("Routers", "router", "/api/devices/routers/", imp_router),
    ("Internet exchanges", "ix", "/api/peering/internet-exchanges/", imp_ix),
    ("BGP groups", "group", "/api/peering/bgp-groups/", imp_group),
    ("Connections", "connection", "/api/net/connections/", imp_connection),
    ("Direct sessions", "direct", "/api/peering/direct-peering-sessions/", imp_direct),
    ("IX sessions", "ixsession", "/api/peering/internet-exchange-peering-sessions/", imp_ixsession),
]

if __name__ == "__main__":
    # Sessions are imported with plain create(), so clear them first to keep
    # re-runs idempotent.
    DirectPeeringSession.objects.all().delete()
    InternetExchangePeeringSession.objects.all().delete()
    for label, kind, path, fn in PLAN:
        rows = fetch_all(path)
        run(label, kind, rows, fn)
    print("done.")
