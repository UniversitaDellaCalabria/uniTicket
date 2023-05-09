from django.forms.widgets import DateTimeInput


class UniTicketDateTimeWidget(DateTimeInput):
    template_name = "widgets/uniticket_datetime.html"

    class Media:
        css = {
            "all": ("css/font-awesome.min.css",
                    "css/bootstrap-datetimepicker.min.css")
        }
        js = (
            "js/datetimepicker/moment.min.js",
            "js/datetimepicker/bootstrap-datetimepicker.js",
        )
