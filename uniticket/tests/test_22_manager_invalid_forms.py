import logging

from organizational_area.models import (OrganizationalStructureOffice,
                                        UserManageOrganizationalStructure)
from uni_ticket.models import (OrganizationalStructureAlert,
                               OrganizationalStructureAllowedUsersList,
                               TicketCategory,
                               TicketCategoryCondition,
                               TicketCategoryDefaultReply,
                               TicketCategoryInputList,
                               TicketCategoryModule,
                               TicketCategoryTask,
                               TicketCategoryWSProtocollo)

from . base_category_office_env import BaseCategoryOfficeEnvironment
from . test_10_manager_views import ManagerViewsMixin


logger = logging.getLogger('my_logger')


# a non empty POST (views check "if request.POST") without required fields
INVALID_DATA = {'invalid_field': 'invalid'}


class ManagerInvalidFormsMixin(ManagerViewsMixin):

    def _error_messages(self, response):
        return [str(m) for m in response.context['messages']
                if m.level_tag == 'error']

    def _assert_invalid_post(self, url, snapshot, data=None):
        """
        POST invalid data: the form is rendered again with error messages
        and nothing changes in the database (snapshot() before == after)
        """
        before = snapshot()
        response = self.client.post(url, data or INVALID_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._error_messages(response))
        self.assertEqual(snapshot(), before)
        return response


def model_snapshot(model, **filters):
    return lambda: list(model.objects.filter(**filters).values())


class Test_ManagerInvalidForms(ManagerInvalidFormsMixin, BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()

    # offices
    def test_office_add_new(self):
        self._assert_invalid_post(self.url('manager_office_add_new'),
                                  model_snapshot(OrganizationalStructureOffice))

    def test_office_edit(self):
        self._assert_invalid_post(self.url('manager_office_edit',
                                           office_slug=self.office_1_str_1.slug),
                                  model_snapshot(OrganizationalStructureOffice))

    # categories
    def test_category_add_new(self):
        self._assert_invalid_post(self.url('manager_category_add_new'),
                                  model_snapshot(TicketCategory))

    def test_category_edit(self):
        self._assert_invalid_post(self.cat_url('manager_category_edit'),
                                  model_snapshot(TicketCategory))

    def test_category_add_ticket_user(self):
        self._assert_invalid_post(self.cat_url('manager_category_add_ticket_user'),
                                  lambda: list(self.category_1_str_1.allowed_users.all()))

    def test_category_add_ticket_users_list(self):
        self._assert_invalid_post(
            self.cat_url('manager_category_add_ticket_users_list'),
            lambda: list(self.category_1_str_1.allowed_users_lists.all())
        )

    # input modules and fields
    def test_category_input_module_new(self):
        self._assert_invalid_post(self.cat_url('manager_category_new_input_module'),
                                  model_snapshot(TicketCategoryModule))

    def test_category_input_module_edit(self):
        self._assert_invalid_post(self.cat_url('manager_category_input_module_edit',
                                               module_id=self.module_2.pk),
                                  model_snapshot(TicketCategoryModule))

    def test_category_input_module_details(self):
        self._assert_invalid_post(self.cat_url('manager_category_input_module',
                                               module_id=self.module_2.pk),
                                  model_snapshot(TicketCategoryInputList))

    def test_category_input_module_preview(self):
        # module form without the required subject/description
        self._assert_invalid_post(self.cat_url('manager_category_input_module_preview',
                                               module_id=self.module_2.pk),
                                  model_snapshot(TicketCategoryInputList))

    def test_category_input_field_edit(self):
        self._assert_invalid_post(self.cat_url('manager_category_input_field_edit',
                                               module_id=self.module_2.pk,
                                               field_id=self.input_field.pk),
                                  model_snapshot(TicketCategoryInputList))

    # conditions
    def test_category_condition_new(self):
        self._assert_invalid_post(self.cat_url('manager_category_condition_new'),
                                  model_snapshot(TicketCategoryCondition))

    def test_category_condition_edit(self):
        condition = TicketCategoryCondition.objects.create(
            category=self.category_1_str_1,
            title='Condition',
            text='text',
        )
        self._assert_invalid_post(self.cat_url('manager_category_condition_edit',
                                               condition_id=condition.pk),
                                  model_snapshot(TicketCategoryCondition))

    # tasks
    def test_category_task_new(self):
        self._assert_invalid_post(self.cat_url('manager_category_task_new'),
                                  model_snapshot(TicketCategoryTask))

    def test_category_task_edit(self):
        task = TicketCategoryTask.objects.create(category=self.category_1_str_1,
                                                 subject='Task',
                                                 description='descr',
                                                 code='task-code',
                                                 created_by=self.staff_1)
        self._assert_invalid_post(self.cat_url('manager_category_task_edit',
                                               task_id=task.code),
                                  model_snapshot(TicketCategoryTask))

    # protocol configurations
    def test_category_protocol_configuration_new(self):
        self._assert_invalid_post(
            self.cat_url('manager_category_protocol_configuration_new'),
            model_snapshot(TicketCategoryWSProtocollo)
        )

    def test_category_protocol_configuration_detail(self):
        configuration = TicketCategoryWSProtocollo.objects.create(
            ticket_category=self.category_1_str_1,
            name='Conf',
            protocollo_cod_titolario='1/1',
            protocollo_fascicolo_numero='1',
        )
        self._assert_invalid_post(
            self.cat_url('manager_category_protocol_configuration_detail',
                         configuration_id=configuration.pk),
            model_snapshot(TicketCategoryWSProtocollo)
        )

    # default replies
    def test_category_default_reply_new(self):
        self._assert_invalid_post(self.cat_url('manager_category_default_reply_new'),
                                  model_snapshot(TicketCategoryDefaultReply))

    def test_category_default_reply_detail(self):
        reply = TicketCategoryDefaultReply.objects.create(
            ticket_category=self.category_1_str_1,
            text='reply',
        )
        self._assert_invalid_post(self.cat_url('manager_category_default_reply_detail',
                                               default_reply_id=reply.pk),
                                  model_snapshot(TicketCategoryDefaultReply))


class Test_ManagerSettingsInvalidForms(ManagerInvalidFormsMixin,
                                       BaseCategoryOfficeEnvironment):

    def setUp(self):
        super().setUp()
        self.structure_1_manager_login()
        self.users_list = OrganizationalStructureAllowedUsersList.objects.create(
            organizational_structure=self.structure_1,
            name='List 1'
        )

    def test_add_manager(self):
        self._assert_invalid_post(self.url('manager_user_settings_add_manager'),
                                  model_snapshot(UserManageOrganizationalStructure))

    def test_structure_alert_new(self):
        self._assert_invalid_post(self.url('manager_structure_alert_new'),
                                  model_snapshot(OrganizationalStructureAlert))

    def test_structure_alert_edit(self):
        alert = OrganizationalStructureAlert.objects.create(
            organizational_structure=self.structure_1,
            name='Alert',
            text='Alert text',
        )
        self._assert_invalid_post(self.url('manager_structure_alert_edit',
                                           alert_id=alert.pk),
                                  model_snapshot(OrganizationalStructureAlert))

    def test_structure_users_list_new(self):
        self._assert_invalid_post(self.url('manager_structure_users_list_new'),
                                  model_snapshot(OrganizationalStructureAllowedUsersList))

    def test_structure_users_list_edit(self):
        self._assert_invalid_post(self.url('manager_structure_users_list_edit',
                                           list_id=self.users_list.pk),
                                  model_snapshot(OrganizationalStructureAllowedUsersList))

    def test_structure_users_list_add_user(self):
        self._assert_invalid_post(self.url('manager_structure_users_list_add_user',
                                           list_id=self.users_list.pk),
                                  lambda: list(self.users_list.allowed_users.all()))
