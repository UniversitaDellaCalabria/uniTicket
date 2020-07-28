import logging

from django.conf import settings
from io import BytesIO

logger = logging.getLogger(__name__)


def ticket_protocol(user,
                    subject,
                    structure_configuration=None,
                    configuration=None,
                    file_name='test_name',
                    response=b'',
                    attachments_folder=settings.MEDIA_ROOT,
                    attachments_dict={},
                    test=False):

    valid_conf = structure_configuration and configuration

    # Check only if protocol system works
    # if test and not configuration:
    if test:
        prot_url = settings.PROT_URL
        prot_login = settings.PROT_TEST_LOGIN
        prot_passw = settings.PROT_TEST_PASSW
        prot_aoo = settings.PROT_TEST_AOO
        prot_agd = settings.PROT_AGD_DEFAULT
        prot_uo = settings.PROT_UO_DEFAULT
        prot_email = settings.PROT_EMAIL_DEFAULT
        # prot_id_uo = settings.PROT_UO_ID_DEFAULT
        prot_titolario = settings.PROT_TITOLARIO_DEFAULT
        prot_fascicolo_num = settings.PROT_FASCICOLO_DEFAULT
        prot_fascicolo_anno = settings.PROT_FASCICOLO_ANNO_DEFAULT
        prot_template = settings.PROTOCOL_XML
    # for production
    # elif not test and configuration:
    elif not test and valid_conf:
        prot_url = settings.PROT_URL
        prot_login = structure_configuration.protocollo_username
        prot_passw = structure_configuration.protocollo_password
        prot_aoo = structure_configuration.protocollo_aoo
        prot_agd = structure_configuration.protocollo_agd
        prot_uo = structure_configuration.protocollo_uo
        prot_email = structure_configuration.protocollo_email or settings.PROT_EMAIL_DEFAULT
        # prot_id_uo = configuration.protocollo_id_uo
        prot_titolario = configuration.protocollo_cod_titolario
        prot_fascicolo_num = configuration.protocollo_fascicolo_numero
        prot_fascicolo_anno = configuration.protocollo_fascicolo_anno
        prot_template = settings.PROTOCOL_XML
    # for production a custom configuration is necessary
    elif not test and not valid_conf:
        raise Exception(_('Missing XML configuration for production'))

    protocol_data = {
                     # 'wsdl_url' : prot_url,
                     # 'username' : prot_login,
                     # 'password' : prot_passw,
                     # 'template_xml_flusso': prot_template,

                      # Variabili
                     'oggetto':'{}'.format(subject),
                     # 'matricola_dipendente': user.matricola_dipendente,
                     'id_persona': user.taxpayer_id,
                     'nome_persona': user.first_name,
                     'cognome_persona': user.last_name,
                     # 'denominazione_persona': ' '.join((user.first_name,
                                                        # user.last_name,)),

                     # attributi creazione protocollo
                     'aoo': prot_aoo,
                     'agd': prot_agd,
                     'uo': prot_uo,
                     'email': prot_email,
                     # 'uo_id': prot_id_uo,
                     'id_titolario': prot_titolario,
                     'fascicolo_numero': prot_fascicolo_num,
                     'fascicolo_anno': prot_fascicolo_anno
                    }

    protclass = __import__(settings.CLASSE_PROTOCOLLO, globals(), locals(), ['*'])

    # wsclient = protclass.Protocollo(**protocol_data)
    wsclient = protclass.Protocollo(wsdl_url=prot_url,
                                    username=prot_login,
                                    password=prot_passw,
                                    template_xml_flusso=prot_template,
                                    strictly_required=True,
                                    **protocol_data)

    logger.info('Protocollazione richiesta {}'.format(subject))
    docPrinc = BytesIO()
    docPrinc.write(response)
    docPrinc.seek(0)

    wsclient.aggiungi_docPrinc(docPrinc,
                               nome_doc="{}.pdf".format(file_name),
                               tipo_doc='uniTicket request')

    # attachments
    if attachments_dict:
        for k,v in attachments_dict.items():
            file_path = '{}/{}/{}'.format(settings.MEDIA_ROOT,
                                          attachments_folder,
                                          v)
            mime = magic.Magic(mime=True)
            content_type = mime.from_file(file_path)
            f = open(file_path, 'rb')
            attachment_response = HttpResponse(f.read(), content_type=content_type)
            attachment_response['Content-Disposition'] = 'inline; filename=' + v
            f.close()
            allegato = BytesIO()
            allegato.write(attachment_response.content)
            allegato.seek(0)
            wsclient.aggiungi_allegato(nome=v,
                                       descrizione=subject,
                                       fopen=allegato)

    # print(wsclient.is_valid())
    logger.debug(wsclient.render_dataXML())
    # print(wsclient.render_dataXML())
    prot_resp = wsclient.protocolla()

    # logger.info('Avvenuta Protocollazione Richiesta {} numero: {}'.format(form.cleaned_data['subject'],
                                                                          # domanda_bando.numero_protocollo))
    # raise exception if wsclient hasn't a protocol number
    assert wsclient.numero
    return wsclient.numero
