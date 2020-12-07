from django.conf import settings
from django.forms.widgets import *
from django.utils.translation import gettext as _


class UniTicketDateTimeWidget(DateTimeInput):
    template_name = 'widgets/uniticket_datetime.html'

    class Media:
        css = {
            'all': ('css/font-awesome.min.css',
                    'css/bootstrap-datetimepicker.min.css')
        }
        js = ('js/datetimepicker/moment.min.js',
              'js/datetimepicker/bootstrap-datetimepicker.js',)
