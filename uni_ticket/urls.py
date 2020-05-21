from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.utils.text import slugify
from django.views.generic import RedirectView

from . decorators import is_manager, is_operator, is_the_owner
from . views import (datatables, generic, management,
                     manager, operator, user)

app_name="uni_ticket"

_dashboard_name = 'dashboard'

# System/Generic URLs
# ticket = 'ticket/<str:ticket_id>'
ticket = 'tickets/<str:ticket_id>'
urlpatterns = [
    path('', RedirectView.as_view(url='/{}/'.format(_dashboard_name))),

    # Router url di responsabilità su struttura (manager/operator/user)
    re_path(r'^manage/(?:(?P<structure_slug>[-\w]+))?$', generic.manage, name='manage'),

    # Attachments download
    path('{}/download/attachment/<str:attachment>/'.format(ticket), generic.download_attachment, name='download_attachment'),
    path('{}/messages/<str:reply_id>/download/attachment/'.format(ticket), generic.download_message_attachment, name='download_message_attachment'),
    path('{}/tasks/<str:task_id>/download/attachment/'.format(ticket), generic.download_task_attachment, name='download_task_attachment'),
    path('categories/<str:category_slug>/conditions/<int:condition_id>/download/attachment', generic.download_condition_attachment, name='download_condition_attachment'),

    # Delete ticket message
    path('messages/delete/<str:ticket_message_id>/', generic.ticket_message_delete, name='message_delete'),

    path('email-notify/update/', generic.email_notify_change, name='email_notify_change'),
    path('print/ticket/<str:ticket_id>/', generic.ticket_detail_print, name='ticket_detail_print'),
]

# Datatables URLs
structure = '<str:structure_slug>'
urlpatterns += [
    # User json
    path('user_all_tickets.json', datatables.user_all_tickets, name='user_all_tickets_json'),
    path('user_opened_ticket.json', datatables.user_opened_ticket, name='user_opened_ticket_json'),
    path('user_closed_ticket.json', datatables.user_closed_ticket, name='user_closed_ticket_json'),
    path('user_unassigned_ticket.json', datatables.user_unassigned_ticket, name='user_unassigned_ticket_json'),

    # Manager json
    path('{}/manager_unassigned_ticket.json'.format(structure), datatables.manager_unassigned_ticket, name='manager_unassigned_ticket_json'),
    path('{}/manager_opened_ticket.json'.format(structure), datatables.manager_opened_ticket, name='manager_opened_ticket_json'),
    path('{}/my/manager_opened_ticket.json'.format(structure), datatables.manager_my_opened_ticket, name='manager_my_opened_ticket_json'),
    path('{}/manager_closed_ticket.json'.format(structure), datatables.manager_closed_ticket, name='manager_closed_ticket_json'),
    path('{}/manager_not_closed_ticket.json'.format(structure), datatables.manager_not_closed_ticket, name='manager_not_closed_ticket_json'),

    # Operator json
    path('{}/operator_unassigned_ticket.json'.format(structure), datatables.operator_unassigned_ticket, name='operator_unassigned_ticket_json'),
    path('{}/operator_opened_ticket.json'.format(structure), datatables.operator_opened_ticket, name='operator_opened_ticket_json'),
    path('{}/my/operator_opened_ticket.json'.format(structure), datatables.operator_my_opened_ticket, name='operator_my_opened_ticket_json'),
    path('{}/operator_closed_ticket.json'.format(structure), datatables.operator_closed_ticket, name='operator_closed_ticket_json'),
    path('{}/operator_not_closed_ticket.json'.format(structure), datatables.operator_not_closed_ticket, name='operator_not_closed_ticket_json'),
]

# Management URLs (manager and operator)
base = 'manage/<str:structure_slug>'
tickets = '{}/tickets'.format(base)
# ticket = '{}'.format(tickets)
ticket_id = '{}/<str:ticket_id>'.format(tickets)
task = '{}/tasks'.format(ticket_id)
task_id = '{}/<str:task_id>'.format(task)

urlpatterns += [
    # Ticket
    path('{}/opened/'.format(tickets), management.manage_opened_ticket_url, name='manage_opened_ticket_url'),
    path('{}/unassigned/'.format(tickets), management.manage_unassigned_ticket_url, name='manage_unassigned_ticket_url'),
    path('{}/closed/'.format(tickets), management.manage_closed_ticket_url, name='manage_closed_ticket_url'),
    path('{}/'.format(tickets), management.manage_not_closed_ticket_url, name='manage_not_closed_ticket_url'),
    path('{}/'.format(tickets), management.manage_ticket_url, name='manage_ticket_url'),
    path('{}/'.format(ticket_id), management.manage_ticket_url_detail, name='manage_ticket_url_detail'),
    path('{}/messages/'.format(ticket_id), management.ticket_message_url, name='manage_ticket_message_url'),
    path('{}/competence/add/'.format(ticket_id), management.ticket_competence_add_url, name='add_ticket_competence_url'),
    path('{}/competence/leave/'.format(ticket_id), management.ticket_competence_leave, name='leave_ticket_competence'),
    path('{}/dependence/add/'.format(ticket_id), management.ticket_dependence_add_url, name='add_ticket_dependence_url'),
    path('{}/dependence/remove/<str:master_ticket_id>/'.format(ticket_id), management.ticket_dependence_remove, name='remove_ticket_dependence'),
    # Non usato
    # path('{}/take/'.format(ticket_id), management.ticket_take, name='prendi_ticket_in_carico'),
    path('{}/close/'.format(ticket_id), management.ticket_close_url, name='close_ticket'),
    path('{}/reopen/'.format(ticket_id), management.ticket_reopen, name='reopen_ticket'),
    path('{}/assign-offices/'.format(ticket_id), management.ticket_taken_by_unassigned_offices, name='ticket_taken_by_unassigned_offices'),
    # path('{}/assign/<str:destination_structure_slug>/<str:office_slug>/'.format(ticket_id), management.ticket_taken_by_unassigned_office, name='ticket_taken_by_unassigned_office'),

    # Task
    path('{}/add/'.format(task), management.task_add_new_url, name='add_ticket_task_url'),
    path('{}/'.format(task_id), management.task_detail_url, name='manage_task_detail_url'),
    path('{}/close/'.format(task_id), management.task_close_url, name='close_task'),
    path('{}/delete/'.format(task_id), management.task_remove, name='task_remove'),
    path('{}/riapri/'.format(task_id), management.task_reopen, name='reopen_task'),
    path('{}/edit/remove-attachment/'.format(task_id), management.task_attachment_delete, name='manage_elimina_allegato_task'),
    path('{}/edit/'.format(task_id), management.task_edit_url, name='edit_task'),
]

# Manager URLs
base = '{}/<str:structure_slug>'.format(slugify(settings.MANAGEMENT_URL_PREFIX['manager']))
tickets = '{}/tickets'.format(base)
ticket_id = '{}/<str:ticket_id>'.format(tickets)
task = '{}/tasks'.format(ticket_id)
task_id = '{}/<str:task_id>'.format(task)
offices = '{}/offices'.format(base)
office = '{}/office'.format(offices)
office_id = '{}/<str:office_slug>'.format(office)
categories = '{}/categories'.format(base)
# category = '{}/category'.format(categories)
category_id = '{}/<str:category_slug>'.format(categories)
cat_input = '{}/input'.format(category_id)
cat_input_id = '{}/<int:module_id>'.format(cat_input)
condition = '{}/conditions'.format(category_id)
condition_id = '{}/<int:condition_id>'.format(condition)
category_task = '{}/default-tasks'.format(category_id)
category_task_id = '{}/<str:task_id>'.format(category_task)

structure_protocol_configurations = '{}/settings/protocol-configurations'.format(base)
structure_protocol_configuration = '{}/<int:configuration_id>'.format(structure_protocol_configurations)

category_protocol_configurations = '{}/protocol-configurations'.format(category_id)
category_protocol_configuration = '{}/<int:configuration_id>'.format(category_protocol_configurations)

urlpatterns += [
    path('{}/{}/'.format(base, _dashboard_name), manager.dashboard, name='manager_dashboard'),

    # Ticket
    path('{}/opened/'.format(tickets), login_required(is_manager(generic.opened_ticket)), name='manager_opened_ticket'),
    path('{}/opened/my/'.format(tickets), login_required(is_manager(generic.my_opened_ticket)), name='manager_my_opened_ticket'),
    path('{}/unassigned/'.format(tickets), login_required(is_manager(generic.unassigned_ticket)), name='manager_unassigned_ticket'),
    path('{}/closed/'.format(tickets), login_required(is_manager(generic.closed_ticket)), name='manager_closed_ticket'),
    path('{}/'.format(tickets), login_required(is_manager(management.tickets)), name='manager_tickets'),
    path('{}/'.format(ticket_id), login_required(is_manager(management.ticket_detail)), name='manager_manage_ticket'),
    path('{}/messages/'.format(ticket_id), login_required(is_manager(management.ticket_message)), name='manager_ticket_message'),
    path('{}/competence/add/'.format(ticket_id), login_required(is_manager(management.ticket_competence_add_new)), name='manager_add_ticket_competence'),
    path('{}/competence/add/<str:new_structure_slug>/'.format(ticket_id), login_required(is_manager(management.ticket_competence_add_final)), name='manager_add_ticket_competence'),
    path('{}/dependence/add/'.format(ticket_id), login_required(is_manager(management.ticket_dependence_add_new)), name='manager_add_ticket_dependence'),
    path('{}/close/'.format(ticket_id), login_required(is_manager(management.ticket_close)), name='manager_close_ticket'),

    # Task
    path('{}/add/'.format(task), login_required(is_manager(management.task_add_new)), name='manager_add_ticket_task'),
    path('{}/'.format(task_id), login_required(is_manager(management.task_detail)), name='manager_task_detail'),
    path('{}/close/'.format(task_id), login_required(is_manager(management.task_close)), name='manager_close_task'),
    path('{}/edit/'.format(task_id), login_required(is_manager(management.task_edit)), name='manager_edit_task'),

    # Offices
    path('{}/new/'.format(office), manager.office_add_new, name='manager_office_add_new'),
    path('{}/'.format(office_id), manager.office_detail, name='manager_office_detail'),
    path('{}/edit/'.format(office_id), manager.office_edit, name='manager_office_edit'),
    path('{}/remove-operator/<int:employee_id>/'.format(office_id), manager.office_remove_operator, name='manager_remove_office_operator'),
    path('{}/add-category/'.format(office_id), manager.office_add_category, name='manager_add_office_category'),
    path('{}/remove-category/<str:category_slug>/'.format(office_id), manager.office_remove_category, name='manager_remove_office_category'),
    path('{}/disable/'.format(office_id), manager.office_disable, name='manager_disable_office'),
    path('{}/enable/'.format(office_id), manager.office_enable, name='manager_enable_office'),
    path('{}/delete/'.format(office_id), manager.office_delete, name='manager_delete_office'),
    path('{}/'.format(offices), manager.offices, name='manager_offices'),

    # Categories
    path('{}/'.format(categories), manager.categories, name='manager_categories'),
    path('{}/new/'.format(categories), manager.category_add_new, name='manager_category_add_new'),
    path('{}/'.format(category_id), manager.category_detail, name='manager_category_detail'),
    path('{}/remove-office/<str:office_slug>/'.format(category_id), manager.category_remove_office, name='manager_remove_category_office'),
    path('{}/edit/'.format(category_id), manager.category_edit, name='manager_category_edit'),
    path('{}/disable/'.format(category_id), manager.category_disable, name='manager_disable_category'),
    path('{}/enable/'.format(category_id), manager.category_enable, name='manager_enable_category'),
    path('{}/delete/'.format(category_id), manager.category_delete, name='manager_delete_category'),

    # Category input modules
    path('{}/new/'.format(cat_input), manager.category_input_module_new, name='manager_category_new_input_module'),
    path('{}/'.format(cat_input_id), manager.category_input_module_details, name='manager_category_input_module'),
    path('{}/edit/'.format(cat_input_id), manager.category_input_module_edit, name='manager_category_input_module_edit'),
    path('{}/enable/'.format(cat_input_id), manager.category_input_module_enable, name='manager_category_input_module_enable'),
    path('{}/disable/'.format(cat_input_id), manager.category_input_module_disable, name='manager_category_input_module_disable'),
    path('{}/delete/'.format(cat_input_id), manager.category_input_module_delete, name='manager_category_input_module_delete'),
    path('{}/clone/'.format(cat_input_id), manager.category_input_module_clone_preload, name='manager_category_input_module_clone_preload'),
    path('{}/clone/<str:selected_structure_slug>/'.format(cat_input_id), manager.category_input_module_clone_preload, name='manager_category_input_module_clone_preload'),
    path('{}/clone/<str:selected_structure_slug>/<str:selected_category_slug>/'.format(cat_input_id), manager.category_input_module_clone_preload, name='manager_category_input_module_clone_preload'),
    path('{}/clone/<str:selected_structure_slug>/<str:selected_category_slug>/confirm/'.format(cat_input_id), manager.category_input_module_clone, name='manager_category_input_module_clone'),
    path('{}/preview/'.format(cat_input_id), manager.category_input_module_preview, name='manager_category_input_module_preview'),
    path('{}/field/<int:field_id>/delete/'.format(cat_input_id), manager.category_input_field_delete, name='manager_category_input_field_delete'),
    path('{}/field/<int:field_id>/edit/'.format(cat_input_id), manager.category_input_field_edit, name='manager_category_input_field_edit'),

    # Category conditions
    path('{}/new/'.format(condition), manager.category_condition_new, name='manager_category_condition_new'),
    path('{}/edit/'.format(condition_id), manager.category_condition_edit, name='manager_category_condition_edit'),
    path('{}/delete/'.format(condition_id), manager.category_condition_delete, name='manager_category_condition_delete'),
    path('{}/disable/'.format(condition_id), manager.category_condition_disable, name='manager_category_condition_disable'),
    path('{}/enable/'.format(condition_id), manager.category_condition_enable, name='manager_category_condition_enable'),
    path('{}/'.format(condition_id), manager.category_condition_detail, name='manager_category_condition_detail'),

    # Category default tasks
    path('{}/new/'.format(category_task), manager.category_task_new, name='manager_category_task_new'),
    path('{}/edit/'.format(category_task_id), manager.category_task_edit, name='manager_category_task_edit'),
    path('{}/edit/remove-attachment/'.format(category_task_id), manager.category_task_attachment_delete, name='category_task_attachment_delete'),
    path('{}/delete/'.format(category_task_id), manager.category_task_delete, name='manager_category_task_delete'),
    path('{}/disable/'.format(category_task_id), manager.category_task_disable, name='manager_category_task_disable'),
    path('{}/enable/'.format(category_task_id), manager.category_task_enable, name='manager_category_task_enable'),
    path('{}/'.format(category_task_id), manager.category_task_detail, name='manager_category_task_detail'),
    path('{}/download/attachment/'.format(category_task_id), manager.category_task_download_attachment, name='category_task_download_attachment'),

    # Structure Protocol configurations
    path('{}/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_detail, name='manager_structure_protocol_configuration_detail'),
    path('{}/new/'.format(structure_protocol_configurations), manager.structure_protocol_configuration_new, name='manager_structure_protocol_configuration_new'),
    path('{}/delete/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_delete, name='manager_structure_protocol_configuration_delete'),
    path('{}/disable/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_disable, name='manager_structure_protocol_configuration_disable'),
    path('{}/enable/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_enable, name='manager_structure_protocol_configuration_enable'),

    # Category Protocol configurations
    path('{}/'.format(category_protocol_configuration), manager.category_protocol_configuration_detail, name='manager_category_protocol_configuration_detail'),
    path('{}/new/'.format(category_protocol_configurations), manager.category_protocol_configuration_new, name='manager_category_protocol_configuration_new'),
    path('{}/delete/'.format(category_protocol_configuration), manager.category_protocol_configuration_delete, name='manager_category_protocol_configuration_delete'),
    path('{}/disable/'.format(category_protocol_configuration), manager.category_protocol_configuration_disable, name='manager_category_protocol_configuration_disable'),
    path('{}/enable/'.format(category_protocol_configuration), manager.category_protocol_configuration_enable, name='manager_category_protocol_configuration_enable'),

    # Settings
    path('{}/settings/'.format(base), manager.settings, name='manager_user_settings'),

    # Others generic
    path('{}/messages/'.format(base), login_required(is_manager(generic.ticket_messages)), name='manager_messages'),
]

# Operator URLs
base = '{}/<str:structure_slug>'.format(slugify(settings.MANAGEMENT_URL_PREFIX['operator']))
tickets = '{}/tickets'.format(base)
ticket_id = '{}/<str:ticket_id>'.format(tickets)
task = '{}/tasks'.format(ticket_id)
task_id = '{}/<str:task_id>'.format(task)

urlpatterns += [
    path('{}/{}/'.format(base, _dashboard_name), operator.dashboard, name='operator_dashboard'),

    # Ticket
    path('{}/opened/'.format(tickets), login_required(is_operator(generic.opened_ticket)), name='operator_opened_ticket'),
    path('{}/opened/my/'.format(tickets), login_required(is_operator(generic.my_opened_ticket)), name='operator_my_opened_ticket'),
    path('{}/unassigned/'.format(tickets), login_required(is_operator(generic.unassigned_ticket)), name='operator_unassigned_ticket'),
    path('{}/closed/'.format(tickets), login_required(is_operator(generic.closed_ticket)), name='operator_closed_ticket'),
    path('{}/'.format(tickets), login_required(is_operator(management.tickets)), name='operator_tickets'),
    path('{}/'.format(ticket_id), login_required(is_operator(management.ticket_detail)), name='operator_manage_ticket'),
    path('{}/messages/'.format(ticket_id), login_required(is_operator(management.ticket_message)), name='operator_ticket_message'),
    path('{}/competence/add/'.format(ticket_id), login_required(is_operator(management.ticket_competence_add_new)), name='operator_add_ticket_competence'),
    path('{}/competence/add/<str:new_structure_slug>/'.format(ticket_id), login_required(is_operator(management.ticket_competence_add_final)), name='operator_add_ticket_competence'),
    path('{}/dependence/add/'.format(ticket_id), login_required(is_operator(management.ticket_dependence_add_new)), name='operator_add_ticket_dependence'),
    path('{}/close/'.format(ticket_id), login_required(is_operator(management.ticket_close)), name='operator_close_ticket'),

    # Task
    path('{}/add/'.format(task), login_required(is_operator(management.task_add_new)), name='operator_add_ticket_task'),
    path('{}/'.format(task_id), login_required(is_operator(management.task_detail)), name='operator_task_detail'),
    path('{}/close/'.format(task_id), login_required(is_operator(management.task_close)), name='operator_close_task'),
    path('{}/edit/'.format(task_id), login_required(is_operator(management.task_edit)), name='operator_edit_task'),

    path('{}/settings/'.format(base), login_required(is_operator(generic.user_settings)), name='operator_user_settings'),
    path('{}/messages/'.format(base), login_required(is_operator(generic.ticket_messages)), name='operator_messages'),
]

# User URLs
tickets = 'tickets'
# ticket = '{}'.format(tickets)
ticket_id = '{}/<str:ticket_id>'.format(tickets)

urlpatterns += [
    path('{}/'.format(_dashboard_name), user.dashboard, name='user_dashboard'),
    path('{}/opened/'.format(tickets), generic.opened_ticket, name='user_opened_ticket'),
    path('{}/unassigned/'.format(tickets), generic.unassigned_ticket, name='user_unassigned_ticket'),
    path('{}/closed/'.format(tickets), generic.closed_ticket, name='user_closed_ticket'),
    path('{}/'.format(tickets), user.ticket_url, name='user_ticket_url'),
    path('{}/new/'.format(tickets), user.ticket_new_preload, name='new_ticket_preload'),
    path('{}/new/<str:structure_slug>/'.format(tickets), user.ticket_new_preload, name='new_ticket_preload'),
    path('{}/new/<str:structure_slug>/<str:category_slug>/'.format(tickets), user.ticket_add_new, name='add_new_ticket'),
    path('{}/messages/'.format(ticket_id), user.ticket_message, name='ticket_message'),
    path('{}/edit/'.format(ticket_id), user.ticket_edit, name='ticket_edit'),
    path('{}/edit/remove-attachment/<str:attachment>/'.format(ticket_id), user.delete_my_attachment, name='delete_my_attachment'),
    path('{}/delete/'.format(ticket_id), user.ticket_delete, name='ticket_delete'),
    path('{}/close/'.format(ticket_id), user.ticket_close, name='user_close_ticket'),
    path('{}/clone/'.format(ticket_id), user.ticket_clone, name='user_clone_ticket'),
    path('{}/tasks/<str:task_id>/'.format(ticket_id), user.task_detail, name='task_detail'),
    path('{}/'.format(ticket_id), login_required(is_the_owner(user.ticket_detail)), name='ticket_detail'),
    path('settings/', generic.user_settings, name='user_settings'),
    path('messages/', generic.ticket_messages, name='messages'),
]

if 'chat' in settings.INSTALLED_APPS:
        urlpatterns += [path('chat/new/', user.chat_new_preload, name='new_chat_preload'),
                        path('chat/new/<str:structure_slug>/', user.chat_new_preload, name='new_chat_preload'),]
