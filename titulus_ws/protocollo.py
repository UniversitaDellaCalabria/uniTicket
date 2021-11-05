import datetime
import io
import os
import xml.etree.ElementTree as ET

from django.conf import settings

from requests import Session
from requests.auth import HTTPBasicAuth

from zeep import Client, Settings, xsd
from zeep.transports import Transport


class WSTitulusClient(object):
    """
    """

    def __init__(self,
                 wsdl_url,
                 username,
                 password,
                 template_xml_flusso=open(settings.DOCUMENTO_ENTRATA_PATH).read(),
                 **kwargs):

        self.username = username
        self.password = password
        self.wsdl_url = wsdl_url

        self.template_xml_flusso = template_xml_flusso

        self.doc = self.template_xml_flusso.format(**kwargs)

        # zeep
        self.client = None
        self.service = None

        # numero viene popolato a seguito di una protocollazione
        if kwargs.get('numero') and kwargs.get('anno'):
            self.numero = kwargs.get('numero')
            self.anno   = kwargs.get('anno')
        else:
            self.numero = None
            self.anno = None

        # attachments
        self.allegati = []



    def connect(self):
        """
        """
        session=Session()
        settings = Settings(strict=False, xml_huge_tree=True)
        session.auth = HTTPBasicAuth(self.username,
                                     self.password)
        transport=Transport(session=session)
        self.client = Client(self.wsdl_url,
                             transport=transport,
                             settings=settings)
        self.service = self.client.bind('Titulus4Service', 'Titulus4')
        return self.client

    def is_connected(self):
        return True if self.client else False

    def assure_connection(self):
        if not self.is_connected():
            self.connect()

    def protocolla(self, test=False, force=False):
        self.assure_connection()

        namespaces = settings.NAMESPACES if not test else settings.NAMESPACES_DEBUG

        if not force:
            if self.numero or self.anno:
                raise Exception(('Stai tentando di protocollare '
                                 'una istanza che ha già un '
                                 'numero e un anno: {}/{}').format(self.numero,
                                                                   self.anno))
        ns0 = namespaces["ns0"]
        ns2 = namespaces["ns2"]

        attachmentBean_type = self.client.get_type(f'{ns0}AttachmentBean')
        attachmentBeans_type = self.client.get_type(f'{ns2}ArrayOf_tns1_AttachmentBean')
        saveParams = self.client.get_type(f'{ns0}SaveParams')()
        attachmentBeans = attachmentBeans_type(self.allegati)
        saveParams.pdfConversion = True
        saveParams.sendEMail = False
        saveDocumentResponse = None

        saveDocumentResponse = self.service.saveDocument(self.doc,
                                                         attachmentBeans,
                                                         saveParams)
        if saveDocumentResponse:
            root = ET.fromstring(saveDocumentResponse._value_1)
            self.numero = root[1][0].attrib['num_prot']
            return True

    def _get_allegato_dict(self):
        return {'content': None,
                'description': None,
                'filename': None}
                # force PDF
                # 'mimeType': "application/pdf"}

    def aggiungi_allegato(self,
                          fopen,
                          nome,
                          descrizione,
                          is_doc_princ=False,
                          test=False):

        namespaces = settings.NAMESPACES if not test else settings.NAMESPACES_DEBUG
        ns1 = namespaces["ns1"]

        ext = os.path.splitext(nome)[1]
        if not ext:
            raise Exception(("'nome' deve essere con l'estensione "
                             "esempio: .pdf altrimenti errore xml -201!"))
        self.assure_connection()
        content_type = self.client.get_type(f'{ns1}base64Binary')
        content = content_type(fopen.read())
        allegato_dict = self._get_allegato_dict()
        allegato_dict['content'] = content
        allegato_dict['description'] = descrizione
        allegato_dict['filename'] = nome
        # if it's principal document insert in first position
        if is_doc_princ:
            self.allegati.insert(0, allegato_dict)
        else: self.allegati.append(allegato_dict)
        return allegato_dict

    def aggiungi_docPrinc(self, fopen, nome_doc, tipo_doc):
        return self.aggiungi_allegato(fopen=fopen,
                                      nome=nome_doc,
                                      descrizione=tipo_doc,
                                      is_doc_princ=True)

    def fascicolaDocumento(self, fascicolo):
        self.assure_connection()
        response = self.service.addInFolder(fascicolo)
        if response:
            return True
            # root = ET.fromstring(response._value_1)

    def cercaDocumento(self, key, value):
        self.assure_connection()
        query = f'[{key}]={value}'
        return self.service.search(query,
                                   xsd.SkipValue,
                                   xsd.SkipValue)


class Protocollo(WSTitulusClient):
    pass
