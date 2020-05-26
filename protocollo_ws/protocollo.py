# © 2018 Giuseppe De Marco <giuseppe.demarco@unical.it>

# SPDX-License-Identifier: GPL-3.0

import datetime
import io
import os

from zeep import Client
from protocollo_ws.utils import clean_string
from protocollo_ws.settings import (PROT_TEMPLATE_FLUSSO_ENTRATA_DIPENDENTE_PATH,
                                    PROT_DOC_ENCODING,
                                    PROT_ALLEGATO_EXAMPLE_FILE,
                                    PROT_PARAMETRI_TMPL_ROW,
                                    PROT_PARAMETRI)

class WSArchiPROClient(object):
    _ALLEGATO_XML = """
                    <Documento nome="{nome}" id="{allegato_id}">
                          <DescrizioneDocumento>{descrizione}</DescrizioneDocumento>
                          <TipoDocumento>{tipo}</TipoDocumento>
                    </Documento>
                    """
    _FASCICOLO_XML = """
                     <Fascicolo>
                      <CodiceTitolario>{id_titolario}</CodiceTitolario>
                      <Oggetto>{oggetto}</Oggetto>
                      <Soggetto>{soggetto}</Soggetto>
                      <Note>{note}</Note>
                    <ApplicativoProtocollo nome="ArchiPRO">
                        {parametri_rows}
                    </ApplicativoProtocollo>
                    </Fascicolo>
                    """
    _ALLEGATO_SPLIT_STRING = "<!-- Allegati -->"
    REQUIRED_ATTRIBUTES = ['aoo',
                           'agd',
                           'uo',
                           'uo_id',
                           'fascicolo_numero',
                           'fascicolo_anno',
                           'id_titolario',

                           'oggetto',
                           'matricola_dipendente',
                           'denominazione_persona',
                           'nome_doc',
                           'tipo_doc']

    def __init__(self,
                 wsdl_url,
                 username,
                 password,
                 template_xml_flusso=open(PROT_TEMPLATE_FLUSSO_ENTRATA_DIPENDENTE_PATH).read(),
                 required_attributes=REQUIRED_ATTRIBUTES,
                 **kwargs):
        """
        il codice titolario in WSArchiPRO corrisponde alla PRIMARYKEY dello schema SQL
        """

        for attr in required_attributes:
            print(attr)
            setattr(self, attr, clean_string(kwargs.get(attr)))

        #self.doc_fopen = kwargs.get('fopen')
        #

        # numero viene popolato a seguito di una protocollazione
        if kwargs.get('numero') and kwargs.get('anno'):
            self.numero = kwargs.get('numero')
            self.anno   = kwargs.get('anno')
        else:
            self.numero = None
            self.anno = None

        if kwargs.get('aoo'):
            self.aoo = kwargs.get('aoo')

        # diventa vero solo se numero/anno sono stati opportunamente estratti e verificati dal server del protocollo
        self.protocollato = False

        self.docPrinc = None
        # lista di dizionari contenente la struttura di attributi + bytes stream per ogni allegato
        # es {  nome_file,
        #       descrizione,
        #       tipo,
        #       fopen }
        #
        self.allegati  = []
        self.template_xml_flusso = template_xml_flusso

        # to be filled by connect() method
        self.username = username
        self.password = password
        self.wsdl_url = wsdl_url
        self.client = None
        self.login  = None

    def connect(self):
        self.client = Client('{}'.format(self.wsdl_url))
        self.login = self.client.service.login(self.username,
                                               self.password)
        # TODO: non torna più OK bensì una stringa b64, da aggiornare qui
        assert self.login.DST
        return self.login.DST

    def is_connected(self):
        if self.client and self.login:
            return True

    def assure_connection(self):
        # chek if it is connected and authn
        if not self.is_connected():
            self.connect()

    def crea_fascicolo(self, template):
        """
        Crea un fascicolo usando il template self._FASCICOLO_XML
        """
        conf_fasciolo = {'id_titolario': self.id_titolario,
                         'oggetto': self.oggetto,
                         'soggetto': self.soggetto if hasattr(self, 'soggetto') \
                                     else self.oggetto,
                         'note': self.note if hasattr(self, 'note') else '',
                         'parametri_rows': ''.join([PROT_PARAMETRI_TMPL_ROW.format(**par) \
                                                    for par in PROT_PARAMETRI])}
        if isinstance(template, str):
            template = template.format(**conf_fasciolo)
        else:
            template = template.decode(PROT_DOC_ENCODING).format(**conf_fascicolo)
        print("Creating {}".format(template))
        template = template.encode(PROT_DOC_ENCODING)
        return self.client.service.creazioneFascicolo(self.login.DST, arg1=template)

    def get(self):
        """
        returns a dict like:
        {'contentType': None,
         'contenutoFile': b'%PDF-1.4\n.......[]....'
         'error_description': None,
         'error_number': 0,
         'nomeFile': 'mansioni_pubblico_impiego.pdf',
         'tipoFile': None}
        """
        # chek if it is connected and authn
        self.assure_connection()

        if not self.anno or \
           not self.numero:
               raise Exception(('anno e numero sono necessari.'
                                'Attualmente: anno={}, '
                                'numero={}.').format(self.anno,
                                                     self.numero))
        #rec = self.client.service.recuperoDocumento(DST=self.login.DST,
                                                    #lngAnnoPG=self.anno,
                                                    #lngNumPG=self.numero)
        rec = self.client.service.recuperoDocsProtocollo(DST=self.login.DST,
                                                         lngAnnoPG=self.anno,
                                                         lngNumPG=self.numero)
        self.oggetto = rec['oggetto']
        self.fascicolo_numero = rec['numFascicolo']
        self.fascicolo_anno = rec['annoFascicolo']

        # clean old ones
        self.allegati = []
        for f in rec['recuperoFileResult']:
            if f['tipoFile'] == 'P':
                self.nome_doc = f['nomeFile']
                self.tipo_doc = f['tipoFile']
                self.docPrinc = io.BytesIO()
                self.docPrinc.write(f['contenutoFile'])
                self.docPrinc.seek(0)
            else:
                allegato = io.BytesIO()
                allegato.write(f['contenutoFile'])
                allegato.seek(0)
                self.aggiungi_allegato(nome=f['nomeFile'],
                                       descrizione=f['nomeFile'],
                                       fopen=allegato,
                                       tipo=f['tipoFile'])
        return rec

    def dump_files(self, fpath="/tmp"):
        self.get()
        dir_path = os.path.sep.join((fpath,
                                     str(self.numero)))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        dprinc_path = os.path.sep.join((dir_path,
                                        self.nome_doc))
        with open(dprinc_path, 'wb') as f:
            f.write(self.docPrinc.read())
        for i in self.allegati:
            apath = os.path.sep.join((dir_path, i['nome']))
            with open(apath, 'wb') as f:
                f.write(i['ns0:attach'].fileContent)
        return fpath

    def verifica(self):
        return self.get()

    def is_valid(self):
        for i in self.REQUIRED_ATTRIBUTES:
            if not i:
                raise Exception('{} richiesto'.format(i))
        if not self.docPrinc:
            raise Exception('Manca il documento principale. Inseriscilo con .aggiungi_docPrinc(fopen)')
        return True

    def render_AllegatoXML(self, allegato_dict):
        return self._ALLEGATO_XML.format(**allegato_dict)

    def aggiungi_docPrinc(self, fopen,
                          nome_doc=None,
                          tipo_doc=None):
        if (nome_doc and not tipo_doc) or \
           (tipo_doc and not nome_doc):
               raise Exception('tipo_doc e nome_doc devono essere configurati insieme')

        if nome_doc and tipo_doc:
            self.nome_doc = clean_string(nome_doc)
            self.tipo_doc = clean_string(tipo_doc)
        # altrimenti utilizza quelle definite nel costruttore

        self.docPrinc = fopen
        self.docPrinc.seek(0)
        return True

    def render_dataXML(self):
        """
        renderizza il documento che descrive il flusso di protocollazione (dataXML)
        """
        if not isinstance(self.template_xml_flusso, str):
            self.template_xml_flusso = self.template_xml_flusso.decode(PROT_DOC_ENCODING)

        # renderizzo gli allegati, se presenti, nel flusso XML
        if self.allegati:
            allegati_xml = []
            for al in self.allegati:
                allegati_xml.append(self.render_AllegatoXML(al))
            xml_flusso_splitted = self.template_xml_flusso.split(self._ALLEGATO_SPLIT_STRING)
            con_allegati = ''.join((xml_flusso_splitted[0],
                                    ''.join(allegati_xml),
                                    xml_flusso_splitted[1]))
            return con_allegati.format(**self.__dict__)
        return self.template_xml_flusso.format(**self.__dict__)

    def _encode_filestream(self, fopen, enc=False):
        if enc:
            return fopen.read().encode(PROT_DOC_ENCODING)
        else:
            return fopen.read()

    def _get_allegato_dict(self):
        return {'allegato_id': None,
                'nome':        None,
                'descrizione': None,
                'tipo':        None,
                'file':        None}

    def aggiungi_allegato(self, nome,
                                descrizione,
                                fopen,
                                tipo='Allegato'):
        """
        nome: deve essere con l'estenzione esempio: .pdf altrimenti errore xml -201!
        il fopen popola la lista degli allegati.
        """
        if len(nome.split('.')) == 1:
            raise Exception(("'nome' deve essere con l'estensione "
                             "esempio: .pdf altrimenti errore xml -201!"))
        self.assure_connection()

        allegato_idsum = 2
        # recheck id seq
        for al in self.allegati:
            al['allegato_id'] = self.allegati.index(al) + allegato_idsum
        # +2 because it starts from 0 and id=1 is docPrinc

        allegato_dict = self._get_allegato_dict()
        allegato_dict['allegato_id'] = len(self.allegati) + allegato_idsum
        allegato_dict['nome']        = clean_string(nome)
        allegato_dict['descrizione'] = clean_string(descrizione)
        allegato_dict['tipo']        = clean_string(tipo)

        allegato = self.client.wsdl.types.get_type(qname='ns0:attach')()
        allegato.id = len(self.allegati) + allegato_idsum
        allegato.fileName = clean_string(nome)
        allegato.fileContent = self._encode_filestream(fopen)
        allegato_dict['ns0:attach']  = allegato



        self.allegati.append(allegato_dict)
        return self.render_AllegatoXML(allegato_dict)

    def protocolla(self, force=False):
        """
        Se "force" è disabilitato non sarà possibile protocollare un
        documento già protocollato.
        Se force è abilitato riprotocolla il documento e aggiorna il numero
        Torna un dizionario come segue:
        {'annoProt': 2018,
         'annoProtUff': 0,
         'dataProt': None,
         'error_description': None,
         'error_number': 0,
         'numProt': 183,
         'numProtUff': 0,
         'siglaUff': None}
        """
        # check if it is valid
        self.is_valid()

        # chek if it is connected and authn
        self.assure_connection()

        if not force:
            if self.numero or self.anno:
                raise Exception(('Stai tentando di protocollare '
                                 'una istanza che ha già un '
                                 'numero e un anno: {}/{}').format(self.numero,
                                                                   self.anno))

        kwargs = {'DST'      : self.login.DST,
                  'dataXML'  : self.render_dataXML().encode(PROT_DOC_ENCODING),
                  'docPrinc' : self._encode_filestream(self.docPrinc)}

        # print(kwargs['dataXML'])
        # raise Exception(kwargs['dataXML'])

        if self.allegati:
            allegati = [i['ns0:attach'] for i in self.allegati]
            kwargs['listaAllegati'] = allegati

        prot = self.client.service.protocollazioneDocumento(**kwargs)

        # error_number != 0 means that there was an error!
        if prot['error_number'] != 0:
            raise Exception('{}, codice {}'.format(prot['error_description'],
                                                   prot['error_number']))

        self.numero = prot['numProt']
        self.anno = prot['annoProt']
        return prot

    def __repr__(self):
        if self.numero and self.anno:
            return 'WSArchiPRO record: {}/{}'.format(self.numero, self.anno)
        return 'WSArchiPRO: {}'.format(id(self))


class Protocollo(WSArchiPROClient):
    pass


def test(allegati=True):
    """
    Procedura di esempio per esemplificare una sessione tipica di protocollo
    """
    allegati=1
    peo_dict = { 'aoo': settings.PROT_AOO,
                 'oggetto':'Partecipazione Bando PEO',

                 # Variabili
                 'matricola_dipendente':'XXXYYYY',
                 'denominazione_persona':'Giuseppe De Marco',
                 # Variabili
                 # Documento id è sempre 1
                 # 'documento_id':'1',

                 # attributi creazione protocollo
                 'id_titolario': settings.PROT_TITOLARIO_DEFAULT,
                 'fascicolo_numero': settings.PROT_FASCICOLO_DEFAULT,
                 'fascicolo_anno': datetime.date.today().year,
                  #

                 'nome_doc':'esempio.pdf',
                 'tipo_doc':'esempio.pdf',
                 'allegati': [] }

    wsclient = WSArchiPROClient(**peo_dict)
    # test attributi
    wsclient.render_dataXML()
    # print(wsclient.render_dataXML().decode(PROT_DOC_ENCODING))

    # aggiungi binario documento principale
    f = open('TODO', 'rb')
    wsclient.aggiungi_docPrinc(f)
    wsclient.is_valid()

    # aggiungi 3 allegati
    #
    if allegati:
        ad1 = wsclient.aggiungi_allegato('test1.pdf', 'documento di &% test1', open(PROT_ALLEGATO_EXAMPLE_FILE, 'rb'))
        ad2 = wsclient.aggiungi_allegato('test2.pdf', 'documento di -:;\\test2', open(PROT_ALLEGATO_EXAMPLE_FILE, 'rb'))
        ad3 = wsclient.aggiungi_allegato('test3.pdf', 'documento di test3', open(PROT_ALLEGATO_EXAMPLE_FILE, 'rb'))

    wsclient.is_valid()
    print(wsclient.render_dataXML()) #.decode(PROT_DOC_ENCODING))

    # protocollo quindi
    prot = wsclient.protocolla()

    print(prot)
    return wsclient


if __name__ == '__main__':
    test()
    # qui aggiungere argparse per fare protocollazioni command line
