import os
import pdfkit
import re

from django.conf import settings
from django.http.response import HttpResponse


def response_as_pdf(response, pdf_fname):
    """
    prende un oggetto http response e lo modifica per ottenere un pdf
    """
    html_page = response.content.decode('utf-8')

    production_static_url = settings.HOSTNAME + settings.STATIC_URL
    html_page_rewritten = re.sub(settings.STATIC_URL,
                                 production_static_url, html_page)

    production_media_url = settings.HOSTNAME + settings.MEDIA_URL
    html_page_rewritten = re.sub(settings.MEDIA_URL,
                                 production_media_url, html_page_rewritten)

    pdf_path = settings.TMP_DIR + os.path.sep + pdf_fname

    options = {
        'dpi':70,
        # 'page-width': 2024,
        #'enable-smart-width': True,
        'page-size': 'A4',
        'background': None,
        'quiet': '',
        'no-outline': None,
        'margin-top': '0.2in',
        'margin-right': '0in',
        'margin-bottom': '0.3in',
        'margin-left': '0in',
        'footer-center': '[page] di [topage]',
#        'enable-forms': 1
    }

    pdf_stream = pdfkit.from_string(html_page_rewritten,
                                    pdf_path,
                                    options=options)

    f = open(pdf_path, 'rb')
    response = HttpResponse(f.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=' + pdf_fname
    f.close()
    os.remove(pdf_path)
    return response
