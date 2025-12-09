from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from api_rest.models import AuthorizationToken
from organizational_area.models import *
from rest_framework import status
from tests.base_ticket_env import BaseTicketEnvironment
from uni_ticket.models import Ticket, TicketCategory, TicketCategoryInputList, TicketCategoryModule, TicketReply
from tests.base import BaseTest


class uniTicketAPIManagerTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.staff1_at = AuthorizationToken.objects.create(
            name = "test op AT",
            user = self.staff_1,
            active_until = timezone.localtime() + timezone.timedelta(hours = 1)
        )
        self.user1_at = AuthorizationToken.objects.create(
            name = "test user AT",
            user = self.user_1,
            active_until = timezone.localtime() + timezone.timedelta(hours = 1)
        )
        

    def _test_manager_api(self, url):
        req = Client()

        # no auth
        res = req.get(url)
        self.assertEqual(res.status_code,  401)

        # no manager
        res = req.get(url, **self.user1_at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        # auth
        res = req.get(url, **self.staff1_at.as_http_header)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_manager_api(self):
        url1 = reverse(
            'api_rest:api-manager-tickets-unassigned-count',
            kwargs={'structure_slug': self.structure_1.slug}
        )
        self._test_manager_api(url1)
        
        url2 = reverse(
            'api_rest:api-manager-tickets-open-count',
            kwargs={'structure_slug': self.structure_1.slug}
        )
        self._test_manager_api(url2)
        
        url3 = reverse(
            'api_rest:api-manager-tickets-my-open-count',
            kwargs={'structure_slug': self.structure_1.slug}
        )
        self._test_manager_api(url3)
        
        url4 = reverse(
            'api_rest:api-manager-tickets-messages-count',
            kwargs={'structure_slug': self.structure_1.slug}
        )
        self._test_manager_api(url4)
