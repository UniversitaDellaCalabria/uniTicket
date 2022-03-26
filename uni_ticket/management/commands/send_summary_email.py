from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from uni_ticket.utils import send_summary_email

from organizational_area.models import OrganizationalStructureOfficeEmployee


class Command(BaseCommand):
    help = "Send a summary of open tickets to Operators"

    def add_arguments(self, parser):
        # parser.add_argument('-test', required=False, action="store_true",
        # help="do send any email, just test")
        parser.add_argument(
            "-debug", required=False, action="store_true", help="see debug message"
        )

    def handle(self, *args, **options):
        users = OrganizationalStructureOfficeEmployee.objects.filter(
            employee__is_active=True, employee__email_notify=True
        ).values_list("employee")
        status = send_summary_email(
            users=[get_user_model().objects.get(pk=user[0]) for user in set(users)]
        )
        msg = "Successfully sent {} email".format(len(status["success"]))
        self.stdout.write(self.style.SUCCESS(msg))
        if status["failed"]:
            msg_err = "Failed to sent {} email".format(len(status["failed"]))
            self.stdout.write(self.style.ERROR(msg_err))
            print(status["failed"])
