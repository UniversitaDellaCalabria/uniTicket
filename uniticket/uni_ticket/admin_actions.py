import io
import zipfile


from django.http import HttpResponse
from django.utils import timezone


from .utils import export_category_zip


def _download_report_csv(modeladmin, request, queryset):
    """
    Exports the selected ticket categories as a zip file.

    If a single category is selected, its zip is returned as is.
    Otherwise the zip of each category is added to a new zip archive;
    categories whose export fails are skipped.

    Args:
        modeladmin: The TicketCategoryAdmin running the action.
        request: The current request.
        queryset: The selected TicketCategory objects.

    Returns:
        An HttpResponse with the zip file as attachment.
    """

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
    """
    Admin action that downloads the selected categories as a zip file.

    Returns:
        The response built by _download_report_csv.
    """
    return _download_report_csv(
        modeladmin=modeladmin, request=request, queryset=queryset
    )


download_report_csv.short_description = "Download CSV"
