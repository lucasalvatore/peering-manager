from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms.fields import JSONField, SlugField, TagFilterField

from ..models import ASPath

__all__ = ("ASPathBulkEditForm", "ASPathFilterForm", "ASPathForm")


class ASPathForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    regexps = JSONField(
        required=False,
        help_text='List of AS-path regular expressions, e.g. ["^1299 .*", ".* 174$"]',
    )
    local_context_data = JSONField(required=False)
    tags = TagField(required=False)
    fieldsets = (
        ("AS Path", ("name", "slug", "description", "regexps")),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = ASPath
        fields = (
            "name",
            "slug",
            "description",
            "regexps",
            "local_context_data",
            "tags",
        )


class ASPathBulkEditForm(PeeringManagerModelBulkEditForm):
    local_context_data = JSONField(required=False)

    model = ASPath
    nullable_fields = ("description", "local_context_data")


class ASPathFilterForm(PeeringManagerModelFilterSetForm):
    model = ASPath
    tag = TagFilterField(model)
