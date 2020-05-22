# win-chrk4d7tc85 must be resolved in /etc/hosts or DNS
PROT_DOC_ENCODING = 'utf-8'
PROT_MAX_LABEL_LENGHT = 99
# most common oracle wildcard chars
PROT_UNALLOWED_CHARS = ['&', '(', ')', ',', '?', '!', '{', '}', '\\', '[', ']',
                        ':', '~', '|', '$', '<', '>', '*', '%',
                        ';', '"', "'"]

PROT_TEMPLATE_PATH = 'protocollo_ws/xml_templates'
PROT_CREAZIONE_FASCICOLO_XML_PATH = '{}/generalizzati/creazione_fascicolo_standard.xml'.format(PROT_TEMPLATE_PATH)
PROT_TEMPLATE_FLUSSO_ENTRATA_DIPENDENTE_PATH='{}/unical/flusso_entrata.xml_standard.j2'.format(PROT_TEMPLATE_PATH)
PROT_ALLEGATO_EXAMPLE_FILE='{}/esempi/sample.pdf'.format(PROT_TEMPLATE_PATH)

# Flusso entrata per dipendenti
# mittente persona fisica come dipendente, destinatario Unical
PROT_PARAMETRI_TMPL_ROW = '<Parametro nome="{nome}" valore="{valore}" />'
PROT_PARAMETRI = [{'nome': 'agd', 'valore': '483'},
                  {'nome': 'uo', 'valore': '1231'}]

# PROTOCOLLO, questi valori possono variare sulla base di come
# vengono istruite le pratiche all'interno del sistema di protocollo di riferimento
PROT_FASCICOLO_DEFAULT = '3'
PROT_TITOLARIO_DEFAULT = '9095'
PROT_CODICI_TITOLARI = (
                           ('9095','7.1'),
                           ('9099', '7.5'),
                        )

PROT_AOO = 'AOO55' # test
# PROTOCOLLO_AOO = 'AOO1' # produzione

# PRODUCTION USE
PROT_URL = 'http://PROT_URL?wsdl'
PROT_LOGIN = 'UT_PROTO_WS'
PROT_PASSW = 'UT_PROTO_WS'

# TEST USE
PROT_URL = 'http://PROT_URL?wsdl'
PROT_LOGIN = 'UT_PROTO_WS'
PROT_PASSW = 'UT_PROTO_WS'
