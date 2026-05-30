from django.utils.text import slugify

__all__ = ("AutoSlugMixin",)


class AutoSlugMixin:
    """
    Derive the (required, unique) slug from the name so the slug field need not
    be shown in the form. Existing slugs are preserved on edit.
    """

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if name and not self.instance.slug:
            self.instance.slug = slugify(name)
        return cleaned_data
