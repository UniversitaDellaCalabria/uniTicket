import sys
import types
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from chat.consumers import ChatConsumer
from uni_ticket.dynamic_form import DynamicForm
from uni_ticket.forms import TaskCloseForm
from uni_ticket.templatetags import uni_ticket_tags as tags


class ChatConsumerTest(TestCase):
    """
    Checks the chat consumer with anonymous users and missing data
    """

    def _consumer(self, user):
        consumer = ChatConsumer()
        consumer.scope = {'user': user,
                          'url_route': {'kwargs': {'room_name': 'room'}}}
        consumer.channel_name = 'channel'
        consumer.channel_layer = mock.Mock()
        consumer.close = mock.Mock()
        consumer.accept = mock.Mock()
        consumer.send = mock.Mock()
        return consumer

    def test_connect_anonymous(self):
        consumer = self._consumer(AnonymousUser())
        consumer.connect()
        consumer.close.assert_called_once()
        consumer.accept.assert_not_called()
        # disconnect after a refused connection doesn't fail
        consumer.disconnect(close_code=1000)

    def test_join_room_not_existent_user(self):
        user = get_user_model().objects.create_user(username='chat-user')
        consumer = self._consumer(user)
        consumer.user = user
        # the current user is an operator: the joining user data are sent
        with mock.patch('chat.consumers.chat_operator', return_value=True):
            consumer.join_room({'room': 'room', 'user': 999999})
        consumer.send.assert_not_called()

    def test_receive(self):
        consumer = self._consumer(AnonymousUser())
        # frame sent by the client: ignored
        consumer.receive(text_data='{"message": "hi"}')
        consumer.send.assert_not_called()
        # event sent through the channel layer
        consumer.receive({'message': 'hi',
                          'user_fullname': 'name',
                          'is_operator': False,
                          'operator_status': True})
        consumer.send.assert_called_once()


class Saml2BackendTest(TestCase):
    """
    Checks the custom SAML2 backend
    """

    def setUp(self):
        # saml2_sp settings are local and not available in tests
        fake_settings = types.ModuleType('saml2_sp.settings')
        fake_settings.SAML_ATTRIBUTE_MAPPING = {'email': ('email',)}
        patcher = mock.patch.dict(sys.modules, {'saml2_sp.settings': fake_settings})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop('saml2_sp.backends', None)
        self.addCleanup(sys.modules.pop, 'saml2_sp.backends', None)
        from saml2_sp import backends
        self.backends = backends

    def test_authenticate_failed(self):
        backend = self.backends.CustomSaml2Backend()
        with mock.patch.object(self.backends.Saml2Backend, 'authenticate',
                               return_value=None):
            self.assertIsNone(backend.authenticate(None, session_info=None))

    def test_update_user_keeps_attributes(self):
        backend = self.backends.CustomSaml2Backend()
        user = get_user_model().objects.create_user(username='saml-user')
        attributes = {'email': ['saml@test.it'], 'other': ['value']}
        with mock.patch.object(self.backends.Saml2Backend, '_update_user') as parent:
            backend._update_user(user, attributes, {})
        # the caller's dict is not changed
        self.assertEqual(attributes, {'email': ['saml@test.it'], 'other': ['value']})
        # the editable attribute is handled here, not by the parent backend
        self.assertNotIn('email', parent.call_args.args[1])
        self.assertEqual(user.email, 'saml@test.it')


class OptionalParamsTest(TestCase):
    """
    Checks forms and template tags without optional parameters
    """

    def test_task_close_form_without_offices(self):
        form = TaskCloseForm()
        self.assertEqual(form.fields['mail_to_offices'].choices, [])

    def test_dynamic_form_without_params(self):
        form = DynamicForm()
        self.assertIn('ticket_subject', form.fields)

    def test_user_from_pk_not_existent(self):
        self.assertFalse(tags.user_from_pk(999999))
