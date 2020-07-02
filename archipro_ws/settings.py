from django.utils.translation import gettext_lazy as _


# win-chrk4d7tc85 must be resolved in /etc/hosts or DNS
PROT_DOC_ENCODING = 'utf-8'
PROT_MAX_LABEL_LENGTH = 99
# most common oracle wildcard chars
PROT_UNALLOWED_CHARS = ['&', '(', ')', ',', '?', '!', '{', '}', '\\', '[', ']',
                        ':', '~', '|', '$', '<', '>', '*', '%',
                        ';', '"', "'"]

PROT_TEMPLATE_PATH = 'archipro_ws/xml_templates'
PROT_CREAZIONE_FASCICOLO_XML_PATH = '{}/generalizzati/creazione_fascicolo_standard.xml'.format(PROT_TEMPLATE_PATH)
PROT_TEMPLATE_FLUSSO_ENTRATA_DIPENDENTE_PATH='{}/unical/flusso_entrata.xml_standard.j2'.format(PROT_TEMPLATE_PATH)
PROT_ALLEGATO_EXAMPLE_FILE='{}/esempi/sample.pdf'.format(PROT_TEMPLATE_PATH)

# Flusso entrata per dipendenti
# mittente persona fisica come dipendente, destinatario Unical
PROT_PARAMETRI_TMPL_ROW = '<Parametro nome="{nome}" valore="{valore}" />'
PROT_PARAMETRI = [{'nome': 'agd', 'valore': '483'},
                  {'nome': 'uo', 'valore': '1231'}]

# DEFAULT EMAIL
PROT_EMAIL_DEFAULT = 'amministrazione@pec.unical.it'

# PROTOCOLLO, questi valori possono variare sulla base di come
# vengono istruite le pratiche all'interno del sistema di protocollo di riferimento
PROT_FASCICOLO_DEFAULT = '3'
PROT_TITOLARIO_DEFAULT = '9095'
# PROT_CODICI_TITOLARI = (
                           # ('9095','7.1'),
                           # ('9099', '7.5'),
                        # )

PROT_AOO = 'AOO55' # test
# PROT_AOO = 'AOO1' # produzione

# PRODUCTION USE
PROT_URL = 'http://PROT_URL?wsdl'
PROT_LOGIN = 'UT_PROTO_WS'
PROT_PASSW = 'UT_PROTO_WS'

# TEST USE
PROT_URL = 'http://PROT_URL?wsdl'
PROT_LOGIN = 'UT_PROTO_WS'
PROT_PASSW = 'UT_PROTO_WS'

TITOLARIO_DICT = (
    ("9002", _("Normativa e relativa attuazione")),
    ("9003", _("Statuto")),
    ("9004", _("Regolamenti")),
    ("9005", _("Stemma, gonfalone e sigillo")),
    ("9006", _("Sistema informativo, sicurezza dell'informazione e sistema informatico")),
    ("9007", _("Protezione dei dati personali")),
    ("9008", _("Archivio")),
    ("9009", _("Trasparenza e relazioni con il pubblico")),
    ("9010", _("Strategie per il personale, organigramma e funzionigramma")),
    ("9011", _("Rapporti sindacali e contrattazione")),
    ("9012", _("Controllo di gestione e sistema qualità")),
    ("9013", _("Statistica e auditing")),
    ("9014", _("Elezioni e designazioni")),
    ("9015", _("Associazioni e attività culturali, sportive e ricreative")),
    ("9016", _("Editoria e attività informativo-promozionale")),
    ("9017", _("Onorificenze, cerimoniale e attività di rappresentanza")),
    ("9018", _("Politiche e interventi per le pari opportunità")),
    ("9019", _("Interventi di carattere politico, economico, sociale e umanitario")),
    ("9021", _("Rettore")),
    ("9022", _("Prorettore vicario e delegati")),
    ("9023", _("Direttore generale")),
    ("9024", _("Direttore")),
    ("9025", _("Presidente")),
    ("9026", _("Senato accademico")),
    ("9027", _("Consiglio di amministrazione")),
    ("9028", _("Consiglio")),
    ("9029", _("Giunta")),
    ("9030", _("Commissione didattica paritetica docenti-studenti")),
    ("9031", _("Nucleo di valutazione")),
    ("9032", _("Collegio dei revisori dei conti")),
    ("9033", _("Collegio di disciplina (per i docenti)")),
    ("9034", _("Senato degli studenti")),
    ("9035", _("Comitato unico di garanzia e per le pari opportunità")),
    ("9036", _("Comitato tecnico scientifico")),
    ("9037", _("Conferenza dei rettori delle università italiane - CRUI")),
    ("9038", _("Comitato regionale di coordinamento")),
    ("9039", _("Comitato per lo sport universitario")),
    ("9041", _("Ordinamento didattico")),
    ("9042", _("Corsi di studio")),
    ("9043", _("Corsi a ordinamento speciale")),
    ("9044", _("Corsi di specializzazione")),
    ("9045", _("Master")),
    ("9046", _("Corsi di dottorato")),
    ("9047", _("Corsi di perfezionamento e corsi di formazione permanente")),
    ("9048", _("Programmazione didattica, orario delle lezioni, gestione delle aule e degli spazi")),
    ("9049", _("Gestione di esami di profitto, di laurea e di prove di idoneità")),
    ("9050", _("Programmazione e sviluppo, comprese aree, macroaree e settori scientifico-disciplinari")),
    ("9051", _("Strategie e valutazione della didattica e della ricerca")),
    ("9052", _("Premi e borse di studio finalizzati e vincolati")),
    ("9053", _("Progetti e finanziamenti")),
    ("9054", _("Accordi per la didattica e la ricerca")),
    ("9055", _("Rapporti con enti e istituti di area socio-sanitaria")),
    ("9056", _("Opere dell'ingegno, brevetti e imprenditoria della ricerca")),
    ("9057", _("Piani di sviluppo dell'università")),
    ("9058", _("Cooperazione con paesi in via di sviluppo")),
    ("9059", _("Attività per conto terzi")),
    ("9061", _("Contenzioso")),
    ("9062", _("Atti di liberalità")),
    ("9063", _("Violazioni amministrative e reati")),
    ("9064", _("Responsabilità civile, penale e amministrativa del personale")),
    ("9065", _("Pareri e consulenze")),
    ("9067", _("Orientamento, informazione e tutorato")),
    ("9068", _("Selezioni, immatricolazioni e ammissioni")),
    ("9069", _("Trasferimenti e passaggi")),
    ("9070", _("Cursus studiorum e provvedimenti disciplinari")),
    ("9071", _("Diritto allo studio, assicurazioni, benefici economici, tasse e contributi")),
    ("9072", _("Tirocinio, formazione e attività di ricerca")),
    ("9073", _("Servizi di assistenza socio-sanitaria e a richiesta")),
    ("9074", _("Conclusione e cessazione della carriera di studio")),
    ("9075", _("Esami di stato e ordini professionali")),
    ("9076", _("Associazionismo, goliardia e manifestazioni organizzate da studenti o ex studenti")),
    ("9077", _("Benefici Legge 390/91 ")),
    ("9078", _("Servizi abitativi e mensa per gli studenti")),
    ("9079", _("Attività culturali e ricreative")),
    ("9081", _("Poli")),
    ("9082", _("Scuole e strutture di raccordo")),
    ("9083", _("Dipartimenti")),
    ("9084", _("Strutture a ordinamento speciale")),
    ("9085", _("Scuole di specializzazione")),
    ("9086", _("Scuole di dottorato")),
    ("9087", _("Scuole interdipartimentali")),
    ("9088", _("Centri")),
    ("9089", _("Sistema bibliotecario")),
    ("9090", _("Musei, pinacoteche e collezioni")),
    ("9091", _("Consorzi ed enti a partecipazione universitaria")),
    ("9092", _("Fondazioni")),
    ("9093", _("Servizi di ristorazione, alloggi e foresterie")),
    ("9095", _("Concorsi e selezioni")),
    ("9096", _("Assunzioni e cessazioni")),
    ("9097", _("Comandi e distacchi")),
    ("9098", _("Mansioni e incarichi")),
    ("9099", _("Carriera e inquadramenti")),
    ("9100", _("Retribuzione e compensi")),
    ("9101", _("Adempimenti fiscali, contributivi e assicurativi")),
    ("9102", _("Pre-ruolo, trattamento di quiescenza, buonuscita")),
    ("9103", _("Dichiarazioni di infermità ed equo indennizzo")),
    ("9104", _("Servizi a domanda individuale")),
    ("9105", _("Assenze")),
    ("9106", _("Tutela della salute e sorveglianza sanitaria")),
    ("9107", _("Valutazione, giudizi di merito e provvedimenti disciplinari")),
    ("9108", _("Formazione e aggiornamento professionale")),
    ("9109", _("Deontologia professionale ed etica del lavoro")),
    ("9110", _("Personale non strutturato")),
    ("9112", _("Ricavi ed entrate")),
    ("9113", _("Costi e uscite")),
    ("9114", _("Bilancio")),
    ("9115", _("Tesoreria, cassa e istituti di credito")),
    ("9116", _("Imposte, tasse, ritenute previdenziali e assistenziali")),
    ("9118", _("Progettazione e costruzione di opere edilizie con relativi impianti")),
    ("9119", _("Manutenzione ordinaria, straordinaria, ristrutturazione, restauro e destinazione d'uso")),
    ("9120", _("Sicurezza e messa a norma degli ambienti di lavoro")),
    ("9121", _("Telefonia e infrastruttura informatica")),
    ("9122", _("Programmazione Territoriale")),
    ("9124", _("Acquisizione e gestione di beni immobili e relativi servizi")),
    ("9125", _("Locazione di beni immobili, di beni mobili e relativi servizi")),
    ("9126", _("Alienazione di beni immobili e di beni mobili")),
    ("9127", _("Acquisizione e fornitura di beni mobili, di materiali e attrezzature non tecniche e di servizi")),
    ("9128", _("Manutenzione di beni mobili")),
    ("9129", _("Materiali, attrezzature, impiantistica e adempimenti tecnico-normativi")),
    ("9130", _("Partecipazioni e investimenti finanziari")),
    ("9131", _("Inventario, rendiconto patrimoniale, beni in comodato")),
    ("9132", _("Patrimonio culturale – Tutela e valorizzazione")),
    ("9133", _("Gestione dei rifiuti")),
    ("9134", _("Albo dei fornitori")),
    ("9135", _("Oggetti diversi")),
)
