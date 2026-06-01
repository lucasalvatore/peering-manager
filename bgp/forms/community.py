from django import forms
from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms import add_blank_choice
from utils.forms.fields import JSONField, TagFilterField
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from ..enums import CommunityType
from ..models import Community
from .mixins import AutoSlugMixin

__all__ = ("CommunityBulkEditForm", "CommunityFilterForm", "CommunityForm")


class CommunityForm(AutoSlugMixin, PeeringManagerModelForm):
    # Built by the row editor in templates/bgp/community/edit.html (one member
    # value per row) and submitted as a JSON list of strings.
    members = JSONField(required=False, widget=forms.HiddenInput())
    tags = TagField(required=False)
    fieldsets = (("Community", ("name", "description")),)

    class Meta:
        model = Community
        fields = (
            "name",
            "description",
            "members",
            "tags",
        )


class CommunityBulkEditForm(PeeringManagerModelBulkEditForm):
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelect,
    )
    local_context_data = JSONField(required=False)

    model = Community
    nullable_fields = ("type", "description", "local_context_data")


class CommunityFilterForm(PeeringManagerModelFilterSetForm):
    model = Community
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelectMultiple,
    )
    tag = TagFilterField(model)
