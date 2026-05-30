from __future__ import annotations

from django.db import models

from peering_manager.models import OrganisationalModel

from ..enums import PrefixListFamily

__all__ = ("PrefixList",)


class PrefixList(OrganisationalModel):
    """
    A named list of IP prefixes referenced by routing-policy term matches.

    Members are stored as a list of dicts so the per-member match qualifier
    (exact / longer / through / range / ...) can be preserved without a schema
    change. Each member looks like::

        {"prefix": "192.0.2.0/24", "type": "orlonger", "params": {...}}
    """

    family = models.PositiveSmallIntegerField(
        default=PrefixListFamily.ANY,
        choices=PrefixListFamily,
        help_text="Address family this prefix-list applies to",
    )
    prefixes = models.JSONField(
        blank=True,
        default=list,
        help_text="List of prefix members with their match qualifiers",
    )

    class Meta:
        verbose_name = "prefix list"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
