import os
import re

from django.conf import settings
from django.http import HttpResponse

from weasyprint import HTML

def response_as_pdf(response, pdf_fname):
    html_page = response.content.decode('utf-8')
    protocol = 'http://' if settings.DEBUG else 'https://'
    hostname = 'localhost:8000' if settings.DEBUG else settings.HOSTNAME

    production_static_url = protocol + hostname + settings.STATIC_URL
    html_page_rewritten = re.sub(settings.STATIC_URL,
                                 production_static_url,
                                 html_page)

    # production_media_url = protocol + hostname + settings.MEDIA_URL
    # html_page_rewritten = re.sub(settings.MEDIA_URL,
                                 # production_media_url,
                                 # html_page_rewritten)

    html = HTML(string=html_page_rewritten)
    pdf_path = settings.TMP_DIR + os.path.sep + pdf_fname
    html.write_pdf(target=pdf_path);

    f = open(pdf_path, 'rb')
    response = HttpResponse(f.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=' + pdf_fname
    f.close()
    os.remove(pdf_path)
    return response
