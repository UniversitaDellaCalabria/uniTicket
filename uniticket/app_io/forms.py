from django import forms
from django.utils.translation import gettext_lazy as _

from . models import IOServiceTicketCategory


class IOServiceTicketCategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category')
        super().__init__(*args, **kwargs)
        services = IOServiceTicketCategory.objects.filter(category=category).values_list('service__pk', flat=True)
        if self.instance.id:
            services = services.exclude(service=self.instance.service)
        self.fields["service"].queryset = self.fields["service"].queryset.exclude(pk__in=services)

    class Meta:
        model = IOServiceTicketCategory
        fields = [
            "service",
            "note",
        ]
        labels = {
            "service": _("Servizio"),
            "note": _("Note"),
        }
        widgets = {
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    class Media:
        js = ("js/textarea-autosize.js",)
