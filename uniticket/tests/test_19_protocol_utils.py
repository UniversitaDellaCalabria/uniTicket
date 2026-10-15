import os
import shutil
import tempfile

from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from uni_ticket.protocol_utils import ticket_protocol


PROTOCOL_CLIENT = 'titulus_ws.protocollo.Protocollo'
VALID_UO = settings.UO_DICT[0][0]


@override_settings(PROTOCOL_TEST_UO=VALID_UO)
class Test_ProtocolUtils(TestCase):
    """
    ticket_protocol() with a mocked protocol web service client
    """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='protocol-user',
            password='passw',
            first_name='Mario',
            last_name='Rossi',
            email='mario.rossi@test.it',
            taxpayer_id='RSSMRA80A01H501U'
        )
        self.structure_conf = mock.Mock(protocollo_username='user',
                                        protocollo_password='passw',
                                        protocollo_aoo='aoo',
                                        protocollo_agd='agd')
        self.conf = mock.Mock(protocollo_uo=VALID_UO,
                              protocollo_uo_rpa='rpa',
                              protocollo_uo_rpa_username='rpa_user',
                              protocollo_uo_rpa_matricola='0001',
                              protocollo_send_email=False,
                              protocollo_email='',
                              protocollo_cod_titolario='1/1',
                              protocollo_fascicolo_numero='',
                              protocollo_fascicolo_anno=2026)

    def _client(self, client_class, numero='2026/0001'):
        wsclient = client_class.return_value
        wsclient.numero = numero
        return wsclient

    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_test_mode(self, client_class):
        wsclient = self._client(client_class)
        result = ticket_protocol(user=self.user, subject='subject', test=True)

        self.assertEqual(result['numero'], '2026/0001')
        # test fascicolo is defined in test settings: separate filing
        self.assertIn('Fascicolazione avvenuta', result['message'])
        wsclient.fascicolaDocumento.assert_called_once()
        wsclient.protocolla.assert_called_once_with(test=True)
        kwargs = client_class.call_args.kwargs
        self.assertEqual(kwargs['wsdl_url'], settings.PROTOCOL_TEST_URL)
        self.assertEqual(kwargs['username'], settings.PROTOCOL_TEST_LOGIN)
        # subject is upper-cased
        self.assertEqual(kwargs['oggetto'].strip(), 'SUBJECT')
        doc_kwargs = wsclient.aggiungi_docPrinc.call_args.kwargs
        self.assertEqual(doc_kwargs['nome_doc'], 'test name.pdf')
        self.assertEqual(doc_kwargs['fopen'].read(), b'Test')
        wsclient.aggiungi_allegato.assert_not_called()

    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_filing_failure(self, client_class):
        wsclient = self._client(client_class)
        wsclient.fascicolaDocumento.side_effect = Exception('ws error')
        result = ticket_protocol(user=self.user, subject='subject', test=True)
        self.assertIn('Fascicolazione fallita', result['message'])
        self.assertIn('ws error', result['message'])

    @override_settings(FASCICOLAZIONE_SEPARATA=False)
    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_without_separate_filing(self, client_class):
        wsclient = self._client(client_class)
        result = ticket_protocol(user=self.user, subject='subject', test=True)
        self.assertEqual(result, {'numero': '2026/0001'})
        wsclient.fascicolaDocumento.assert_not_called()

    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_without_number(self, client_class):
        self._client(client_class, numero=None)
        with self.assertRaises(AssertionError):
            ticket_protocol(user=self.user, subject='subject', test=True)

    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_production_missing_configuration(self, client_class):
        with self.assertRaises(Exception) as cm:
            ticket_protocol(user=self.user, subject='subject')
        self.assertIn('Missing XML configuration', str(cm.exception))
        client_class.assert_not_called()

    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_production_with_attachments(self, client_class):
        wsclient = self._client(client_class)
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root)
        os.makedirs(os.path.join(media_root, 'folder'))
        with open(os.path.join(media_root, 'folder', 'file.txt'), 'wb') as f:
            f.write(b'attachment content')

        with override_settings(MEDIA_ROOT=media_root):
            result = ticket_protocol(user=self.user,
                                     subject='subject',
                                     structure_configuration=self.structure_conf,
                                     configuration=self.conf,
                                     file_name='ticket',
                                     response=b'pdf content',
                                     attachments_folder='folder',
                                     attachments_dict={'file_1': 'file.txt'})

        # no fascicolo number in configuration: no separate filing
        self.assertEqual(result, {'numero': '2026/0001'})
        kwargs = client_class.call_args.kwargs
        self.assertEqual(kwargs['wsdl_url'], settings.PROTOCOL_URL)
        self.assertEqual(kwargs['username'], 'user')
        self.assertEqual(kwargs['password'], 'passw')
        doc_kwargs = wsclient.aggiungi_docPrinc.call_args.kwargs
        self.assertEqual(doc_kwargs['nome_doc'], 'ticket.pdf')
        self.assertEqual(doc_kwargs['fopen'].read(), b'pdf content')
        att_kwargs = wsclient.aggiungi_allegato.call_args.kwargs
        self.assertEqual(att_kwargs['nome'], 'file.txt')
        self.assertEqual(att_kwargs['descrizione'], 'SUBJECT')
        self.assertEqual(att_kwargs['fopen'].read(), b'attachment content')
        self.assertFalse(att_kwargs['test'])
        wsclient.protocolla.assert_called_once_with(test=False)

    @mock.patch(PROTOCOL_CLIENT)
    def test_protocol_attachments_default_folder(self, client_class):
        # without attachments_folder, files are read from MEDIA_ROOT
        wsclient = self._client(client_class)
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root)
        with open(os.path.join(media_root, 'file.txt'), 'wb') as f:
            f.write(b'attachment content')

        with override_settings(MEDIA_ROOT=media_root):
            ticket_protocol(user=self.user,
                            subject='subject',
                            structure_configuration=self.structure_conf,
                            configuration=self.conf,
                            file_name='ticket',
                            response=b'pdf content',
                            attachments_dict={'file_1': 'file.txt'})

        att_kwargs = wsclient.aggiungi_allegato.call_args.kwargs
        self.assertEqual(att_kwargs['nome'], 'file.txt')
        self.assertEqual(att_kwargs['fopen'].read(), b'attachment content')
