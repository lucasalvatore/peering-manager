from django import forms
from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms import add_blank_choice
from utils.forms.fields import JSONField, SlugField, TagFilterField
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from ..enums import PrefixListFamily
from ..models import PrefixList

__all__ = (
    "PrefixListBulkEditForm",
    "PrefixListFilterForm",
    "PrefixListForm",
)


class PrefixListForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    family = forms.ChoiceField(
        required=False,
        choices=PrefixListFamily,
        widget=StaticSelect,
        help_text="Address family this prefix-list applies to",
    )
    prefixes = JSONField(
        required=False,
        help_text=(
            "List of prefix members, e.g. "
            '[{"prefix": "192.0.2.0/24", "type": "orlonger"}]'
        ),
    )
    local_context_data = JSONField(required=False)
    tags = TagField(required=False)
    fieldsets = (
        ("Prefix List", ("name", "slug", "description", "family", "prefixes")),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = PrefixList
        fields = (
            "name",
            "slug",
            "description",
            "family",
            "prefixes",
            "local_context_data",
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
