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

from ..enums import PrefixListFamily
from ..models import PrefixList
from .mixins import AutoSlugMixin

__all__ = (
    "PrefixListBulkEditForm",
    "PrefixListFilterForm",
    "PrefixListForm",
)


class PrefixListForm(AutoSlugMixin, PeeringManagerModelForm):
    family = forms.ChoiceField(
        required=False,
        choices=PrefixListFamily,
        widget=StaticSelect,
        help_text="Address family this prefix-list applies to",
    )
    # Built by the structured row editor in templates/bgp/prefixlist/edit.html
    # (prefix + match-type dropdown + per-type params) and submitted as JSON.
    prefixes = JSONField(required=False, widget=forms.HiddenInput())
    tags = TagField(required=False)
    fieldsets = (("Prefix List", ("name", "description", "family")),)

    class Meta:
        model = PrefixList
        fields = (
            "name",
            "description",
            "family",
            "prefixes",
            "tags",
        )


class PrefixListBulkEditForm(PeeringManagerModelBulkEditForm):
    family = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(PrefixListFamily),
        widget=StaticSelect,
    )
    local_context_data = JSONField(required=False)

    model = PrefixList
    nullable_fields = ("description", "local_context_data")


class PrefixListFilterForm(PeeringManagerModelFilterSetForm):
    model = PrefixList
    family = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(PrefixListFamily),
        widget=StaticSelectMultiple,
    )
    tag = TagFilterField(model)
