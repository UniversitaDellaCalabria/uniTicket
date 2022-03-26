import io
import zipfile


from django.http import HttpResponse
from django.utils import timezone


from .utils import export_category_zip


def _download_report_csv(modeladmin, request, queryset):

    output = io.BytesIO()
    f = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)

    for cat in queryset:
        try:
            cat_zip = export_category_zip(cat)
            if queryset.count() == 1:
                return cat_zip
            f.writestr(cat.name.replace("/", "_") + ".zip", cat_zip.content)
        except:
            continue
    f.close()
    response = HttpResponse(output.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="uniticket_{}.zip"'.format(
        timezone.localtime()
    )
    return response


def download_report_csv(modeladmin, request, queryset):
    """ """
    return _download_report_csv(
        modeladmin=modeladmin, request=request, queryset=queryset
    )


download_report_csv.short_description = "Download CSV"
