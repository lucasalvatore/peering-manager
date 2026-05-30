from django import forms
from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms.fields import JSONField, TagFilterField

from ..models import ASPath
from .mixins import AutoSlugMixin

__all__ = ("ASPathBulkEditForm", "ASPathFilterForm", "ASPathForm")


class ASPathForm(AutoSlugMixin, PeeringManagerModelForm):
    # Built by the row editor in templates/bgp/aspath/edit.html (one regexp per
    # row) and submitted as a JSON list of strings.
    regexps = JSONField(required=False, widget=forms.HiddenInput())
    tags = TagField(required=False)
    fieldsets = (("AS Path", ("name", "description")),)

    class Meta:
        model = ASPath
        fields = (
            "name",
            "description",
            "regexps",
            "tags",
        )


class ASPathBulkEditForm(PeeringManagerModelBulkEditForm):
    local_context_data = JSONField(required=False)

    model = ASPath
    nullable_fields = ("description", "local_context_data")


class ASPathFilterForm(PeeringManagerModelFilterSetForm):
    model = ASPath
    tag = TagFilterField(model)
