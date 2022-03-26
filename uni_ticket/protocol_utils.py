import logging
import magic

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from io import BytesIO
from .models import UO_DICT

logger = logging.getLogger(__name__)


def ticket_protocol(
    user,
    subject,
    structure_configuration=None,
    configuration=None,
    file_name="",
    response=b"",
    attachments_folder=settings.MEDIA_ROOT,
    attachments_dict={},
    test=False,
):

    # protocol class and settings from settings file
    prot_class = __import__(settings.PROTOCOL_CLASS, globals(), locals(), ["*"])
    prot_utils = __import__(settings.PROTOCOL_UTILS, globals(), locals(), ["*"])

    valid_conf = structure_configuration and configuration

    # fix zeep key words issue
    subject = subject.upper()

    # Check only if protocol system works
    # if test and not configuration:
    if test:
        prot_url = settings.PROTOCOL_TEST_URL
        prot_login = settings.PROTOCOL_TEST_LOGIN
        prot_passw = settings.PROTOCOL_TEST_PASSW
        prot_aoo = settings.PROTOCOL_TEST_AOO
        prot_agd = settings.PROTOCOL_TEST_AGD
        prot_uo = settings.PROTOCOL_TEST_UO
        prot_uo_rpa = settings.PROTOCOL_TEST_UO_RPA
        prot_uo_rpa_username = ""
        prot_uo_rpa_matricola = ""
        prot_send_email = settings.PROTOCOL_SEND_MAIL_DEBUG
        prot_email = settings.PROTOCOL_EMAIL_DEFAULT
        prot_titolario = settings.PROTOCOL_TEST_TITOLARIO
        prot_fascicolo_num = settings.PROTOCOL_TEST_FASCICOLO
        prot_fascicolo_anno = settings.PROTOCOL_TEST_FASCICOLO_ANNO
        prot_template = settings.PROTOCOL_XML
        response = b"Test"
        file_name = "test name"
    # for production
    elif not test and valid_conf:
        prot_url = settings.PROTOCOL_URL
        prot_login = structure_configuration.protocollo_username
        prot_passw = structure_configuration.protocollo_password
        prot_aoo = structure_configuration.protocollo_aoo
        prot_agd = structure_configuration.protocollo_agd
        prot_uo = configuration.protocollo_uo
        prot_uo_rpa = configuration.protocollo_uo_rpa
        prot_uo_rpa_username = configuration.protocollo_uo_rpa_username
        prot_uo_rpa_matricola = configuration.protocollo_uo_rpa_matricola
        prot_send_email = configuration.protocollo_send_email
        prot_email = configuration.protocollo_email or settings.PROTOCOL_EMAIL_DEFAULT
        prot_titolario = configuration.protocollo_cod_titolario
        prot_fascicolo_num = configuration.protocollo_fascicolo_numero
        prot_fascicolo_anno = configuration.protocollo_fascicolo_anno
        prot_template = settings.PROTOCOL_XML
    # for production a custom configuration is necessary
    elif not test and not valid_conf:
        raise Exception(_("Missing XML configuration for production"))

    protocol_data = prot_utils.protocol_entrata_dict(
        oggetto=subject,
        autore="uniTicket (ticket.unical.it)",
        aoo=prot_aoo,
        agd=prot_agd,
        destinatario=prot_uo_rpa,
        destinatario_username=prot_uo_rpa_username,
        destinatario_code=prot_uo_rpa_matricola,
        send_email=prot_send_email,
        uo_nome=dict(UO_DICT)[prot_uo],
        uo=prot_uo,
        email_ufficio=prot_template,
        nome_mittente=user.first_name,
        cognome_mittente=user.last_name,
        cod_fis_mittente=user.taxpayer_id,
        cod_mittente=user.taxpayer_id,
        email_mittente=user.email,
        titolario="",
        cod_titolario=prot_titolario,
        num_allegati=1 + len(attachments_dict),
        fascicolo_num=prot_fascicolo_num,
        fascicolo_anno=prot_fascicolo_anno,
    )

    wsclient = prot_class.Protocollo(
        wsdl_url=prot_url,
        username=prot_login,
        password=prot_passw,
        template_xml_flusso=prot_template,
        **protocol_data,
    )

    logger.info(f"Protocollazione richiesta {subject}")
    docPrinc = BytesIO()
    docPrinc.write(response)
    docPrinc.seek(0)

    wsclient.aggiungi_docPrinc(
        fopen=docPrinc, nome_doc=f"{file_name}.pdf", tipo_doc=file_name
    )

    # attachments
    if attachments_dict:
        for k, v in attachments_dict.items():
            file_path = "{}/{}/{}".format(settings.MEDIA_ROOT, attachments_folder, v)
            mime = magic.Magic(mime=True)
            content_type = mime.from_file(file_path)
            f = open(file_path, "rb")
            attachment_response = HttpResponse(f.read(), content_type=content_type)
            attachment_response["Content-Disposition"] = "inline; filename=" + v
            f.close()
            allegato = BytesIO()
            allegato.write(attachment_response.content)
            allegato.seek(0)
            wsclient.aggiungi_allegato(
                nome=v, descrizione=subject, fopen=allegato, test=test
            )

    # print(wsclient.is_valid())
    # logger.debug(wsclient.render_dataXML())
    # print(wsclient.render_dataXML())

    wsclient.protocolla(test=test)
    assert wsclient.numero

    response = {"numero": wsclient.numero}

    if settings.FASCICOLAZIONE_SEPARATA and prot_fascicolo_num:
        try:
            fascicolo_physdoc = ""
            fascicolo_nrecord = ""
            fascicolo_numero = prot_fascicolo_num
            doc_physdoc = ""
            doc_nrecord = ""
            doc_num_prot = wsclient.numero
            doc_minuta = "no"  # si/no

            fasc = open(settings.FASCICOLO_PATH, "r").read()
            fasc = fasc.format(
                fascicolo_physdoc=fascicolo_physdoc,
                fascicolo_nrecord=fascicolo_nrecord,
                fascicolo_numero=fascicolo_numero,
                doc_physdoc=doc_physdoc,
                doc_nrecord=doc_nrecord,
                doc_num_prot=doc_num_prot,
                doc_minuta=doc_minuta,
            )
            wsclient.fascicolaDocumento(fasc)
            msg = "Fascicolazione avvenuta: {} in {}".format(
                fascicolo_numero, wsclient.numero
            )

        except Exception as e:
            msg = "Fascicolazione fallita: {} in {} - {}".format(
                fascicolo_numero, wsclient.numero, e
            )
        response["message"] = msg
        logger.info(msg)

    # raise exception if wsclient hasn't a protocol number
    return response
