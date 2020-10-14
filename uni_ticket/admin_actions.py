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

from . models import *


def _download_report_csv(modeladmin,
                         request,
                         queryset):

    num = 0
    failed = 0
    msg_err = 'Sono incorsi errori nell\'esportare {}: {}'
    msg_ok = '{} ESPORTATA'

    output = io.BytesIO()
    f = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)

    delimiter='$'
    quotechar='"'

    for cat in queryset:

        try:
            input_modules = TicketCategoryModule.objects.filter(ticket_category=cat)

            for module in input_modules:

                file_name = "{}_MOD_{}.csv".format(cat.name.replace('/','_'),
                                                   module.name.replace('/','_'))

                head = ['created',
                        'user',
                        'status',
                        'subject',
                        'description']

                fields = TicketCategoryInputList.objects.filter(category_module=module)
                for field in fields:
                    head.append(field.name)

                csv_file = HttpResponse(content_type='text/csv')
                csv_file['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
                writer = csv.writer(csv_file,
                                    delimiter = delimiter,
                                    quotechar = quotechar)

                writer.writerow(head)

                richieste = Ticket.objects.filter(input_module=module)

                if not richieste: continue

                for richiesta in richieste:
                    content = richiesta.get_modulo_compilato()
                    status = strip_tags(richiesta.get_status())
                    row = [richiesta.created,
                           richiesta.created_by,
                           status,
                           richiesta.subject,
                           richiesta.description]
                    for k,v in content.items():
                        row.append(v)
                    writer.writerow(row)
                f.writestr(file_name,
                           csv_file.content)
            num += 1
            # messages.add_message(request, messages.SUCCESS, msg_ok.format(cat))
        except:
            # messages.add_message(request,
                                 # messages.ERROR,
                                 # msg_err.format(cat.__str__(), e.__str__()))
            failed += 1

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
