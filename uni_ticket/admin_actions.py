import io
import os
import zipfile

from django.apps import apps
import csv

from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import strip_tags

from django_form_builder.utils import format_field_name

from . models import *
from . utils import export_category_zip


def _download_report_csv(modeladmin,
                         request,
                         queryset):

    output = io.BytesIO()
    f = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)

    for cat in queryset:
        try:
            cat_zip = export_category_zip(cat)
            if queryset.count() == 1:
                return cat_zip
            f.writestr(cat.name.replace('/','_') + '.zip', cat_zip.content)
        except: continue
    f.close()
    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="uniticket_{}.zip"'.format(timezone.localtime())
    return response


def download_report_csv(modeladmin, request, queryset):
    """
    """
    return _download_report_csv(modeladmin=modeladmin,
                                request=request,
                                queryset=queryset)
download_report_csv.short_description = "Download CSV"
