from __future__ import annotations

from django.db import models

from peering_manager.models import OrganisationalModel

__all__ = ("ASPath",)


class ASPath(OrganisationalModel):
    """
    A named AS-path access list referenced by routing-policy term matches.

    ``regexps`` is a list of AS-path regular expression strings (e.g.
    ``["^1299 .*", ".* 174$"]``); the policy preview renders one ``expression``
    entry per item.
    """

    regexps = models.JSONField(
        blank=True,
        default=list,
        help_text="List of AS-path regular expressions",
    )

    class Meta:
        verbose_name = "AS path"
        verbose_name_plural = "AS paths"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
