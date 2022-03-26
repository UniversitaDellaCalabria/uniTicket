import logging
import os
import re

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML
except ModuleNotFoundError as e:
    logger.warning(
        "weasyprint not found - please install it top enable PDF exports. "
        "pip install WeasyPrint"
    )


def response_as_pdf(response, pdf_fname):
    html_page = response.content.decode('utf-8')

    # if ASGI
    # asgiref lock static files URLs calling
    # if channels runs on same project server
    if not settings.DEBUG or not hasattr(settings, 'ASGI_APPLICATION'):
        protocol = 'http://' if settings.DEBUG else 'https://'
        production_static_url = protocol + settings.HOSTNAME + settings.STATIC_URL
        # set full path to static files
        html_page = re.sub(settings.STATIC_URL,
                           production_static_url,
                           html_page)
    html = HTML(string=html_page)

    pdf_path = settings.TMP_DIR + os.path.sep + pdf_fname
    html.write_pdf(target=pdf_path)

    f = open(pdf_path, 'rb')
    response = HttpResponse(f.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=' + pdf_fname
    f.close()
    os.remove(pdf_path)
    return response
