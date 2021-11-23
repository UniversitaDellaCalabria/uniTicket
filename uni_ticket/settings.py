from django.conf import settings
from django.utils.translation import gettext_lazy as _

# system attachments folders
LOGOS_FOLDER = getattr(settings, "LOGOS_FOLDER", "logos")
STRUCTURES_FOLDER = getattr(settings, "STRUCTURES_FOLDER", "structures")
TICKET_ATTACHMENT_FOLDER = getattr(
    settings, "TICKET_ATTACHMENT_FOLDER", "ticket")
TICKET_CATEGORIES_FOLDER = getattr(
    settings, "TICKET_CATEGORIES_FOLDER", "categories")
TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = getattr(
    settings, "TICKET_MESSAGES_ATTACHMENT_SUBFOLDER", "messages"
)
TICKET_TASK_ATTACHMENT_SUBFOLDER = getattr(
    settings, "TICKET_TASK_ATTACHMENT_SUBFOLDER", "task"
)
CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER = getattr(
    settings, "CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER", "conditions"
)

UNITICKET_JWE_RSA_KEY_PATH = getattr(
    settings, "UNITICKET_JWE_RSA_KEY_PATH", "saml2_sp/saml2_config/certificates/key.pem"
)
UNITICKET_JWE_ALG = getattr(settings, "UNITICKET_JWE_ALG", "RSA-OAEP")
UNITICKET_JWE_ENC = getattr(settings, "UNITICKET_JWE_ENC", "A128CBC-HS256")

# superusers view all
SUPER_USER_VIEW_ALL = getattr(settings, "SUPER_USER_VIEW_ALL", True)

# show ticket priority to simple userse
SIMPLE_USER_SHOW_PRIORITY = getattr(
    settings, "SIMPLE_USER_SHOW_PRIORITY", False)

# category conditions form field
TICKET_CONDITIONS_FIELD_ID = getattr(
    settings, "TICKET_CONDITIONS_FIELD_ID", "condizioni_field_id"
)
TICKET_CONDITIONS_TEXT = getattr(
    settings,
    "TICKET_CONDITIONS_TEXT",
    _(
        "Dichiara di aver letto "
        "e compreso quanto scritto sopra "
        "e di assumersi ogni responsabilità "
        "su quanto di seguito dichiarato"
    ),
)

# new ticket heading text (user informations)
SHOW_HEADING_TEXT = getattr(settings, "SHOW_HEADING_TEXT", True)
TICKET_HEADING_TEXT = getattr(
    settings,
    "TICKET_HEADING_TEXT",
    _(
        "Soggetto richiedente: <b>{user}</b>"
        '<br><span class="x-small">[{taxpayer}]</span>'
    ),
)

TICKET_COMPILED_HEADING_TEXT = getattr(
    settings,
    "TICKET_COMPILED_HEADING_TEXT",
    _("Compilato da: <b>{user}</b>" '<br><span class="x-small">[{taxpayer}]</span>'),
)

# form fields names
# ticket subject
TICKET_SUBJECT_ID = getattr(settings, "TICKET_SUBJECT_ID", "ticket_subject")

TICKET_SUBJECT_LABEL = getattr(
    settings, "TICKET_SUBJECT_LABEL", _("Oggetto della Richiesta")
)
TICKET_SUBJECT_HELP_TEXT = getattr(
    settings,
    "TICKET_SUBJECT_HELP_TEXT",
    _(
        "Il campo Oggetto è impostato con "
        "la denominazione della richiesta. "
        "E' possibile modificarlo o integrarlo "
        "per fornire indicazioni specifiche"
    ),
)

# ticket description
TICKET_DESCRIPTION_ID = getattr(
    settings, "TICKET_DESCRIPTION_ID", "ticket_description")
TICKET_DESCRIPTION_LABEL = getattr(
    settings, "TICKET_DESCRIPTION_LABEL", _("Descrizione")
)
TICKET_DESCRIPTION_HELP_TEXT = getattr(
    settings,
    "TICKET_DESCRIPTION_HELP_TEXT",
    _(
        "Il campo Descrizione è impostato con "
        "la descrizione generica della richiesta. "
        "E' possibile modificarlo o integrarlo "
        "per fornire indicazioni specifiche"
    ),
)

# captcha
TICKET_CAPTCHA_ID = getattr(settings, "TICKET_CAPTCHA_ID", "ticket_captcha")
TICKET_CAPTCHA_HIDDEN_ID = getattr(settings, "", "ticket_captcha_hidden")
TICKET_CAPTCHA_LABEL = getattr(
    settings, "TICKET_CAPTCHA_HIDDEN_ID", _("Codice di verifica")
)

# new ticket submit buttons (create / generate import URL)
TICKET_CREATE_BUTTON_NAME = getattr(
    settings, "TICKET_CREATE_BUTTON_NAME", "confirm_submit"
)
TICKET_GENERATE_URL_BUTTON_NAME = getattr(
    settings, "TICKET_GENERATE_URL_BUTTON_NAME", "generate_url_submit"
)
TICKET_COMPILED_BY_USER_NAME = getattr(
    settings, "TICKET_COMPILED_BY_USER_NAME", "compiled_by_user"
)
TICKET_COMPILED_CREATION_DATE = getattr(
    settings, "TICKET_COMPILED_CREATION_DATE", "compiled_date"
)
TICKET_INPUT_MODULE_NAME = getattr(
    settings, "TICKET_INPUT_MODULE_NAME", "ticket_input_module"
)

# priority levels
PRIORITY_LEVELS = getattr(
    settings,
    "PRIORITY_LEVELS",
    (
        (-2, _("Molto alta")),
        (-1, _("Alta")),
        (0, _("Normale")),
        (1, _("Bassa")),
        (2, _("Molto bassa")),
    ),
)

# closing levels
CLOSING_LEVELS = getattr(
    settings,
    "CLOSING_LEVELS",
    (
        (-1, _("Rifiutata")),
        (0, _("Non risolta")),
        (1, _("Risolta con successo")),
        (2, _("Non definita")),
    ),
)

# If 0 = Unlimited
MAX_DAILY_TICKET_PER_USER = getattr(settings, "MAX_DAILY_TICKET_PER_USER", 10)

# user contexts
CONTEXT_SIMPLE_USER = getattr(settings, "CONTEXT_SIMPLE_USER", _("Utente"))

# To change the URLs prefix for every user type
MANAGER_PREFIX = getattr(settings, "MANAGER_PREFIX", "Manager")
OPERATOR_PREFIX = getattr(settings, "OPERATOR_PREFIX", "Operatore")
USER_PREFIX = getattr(settings, "USER_PREFIX", "user")

# Do not edit! - START
MANAGEMENT_URL_PREFIX = {
    "manager": MANAGER_PREFIX,
    "operator": OPERATOR_PREFIX,
    "user": USER_PREFIX,
}
# Do not edit! - END

# ticket competence abandoned
NO_MORE_COMPETENCE_OVER_TICKET = getattr(
    settings, "NO_MORE_COMPETENCE_OVER_TICKET", _(
        "Nessuna competenza sulla richiesta")
)
# ticket readonly access
READONLY_COMPETENCE_OVER_TICKET = getattr(
    settings,
    "READONLY_COMPETENCE_OVER_TICKET",
    _("Hai accesso alla richiesta in sola lettura"),
)

# min ticket content length (digits) to compress
TICKET_MIN_DIGITS_TO_COMPRESS = getattr(
    settings, "TICKET_MIN_DIGITS_TO_COMPRESS", 90)

# Access level to categories
# Override for your own context

# This parameters define the roles of users to open ticket
# If True, an employee is a user that has this parameter filled (in user model)
# If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
EMPLOYEE_ATTRIBUTE_NAME = getattr(
    settings, "EMPLOYEE_ATTRIBUTE_NAME", "matricola_dipendente"
)
EMPLOYEE_ATTRIBUTE_LABEL = getattr(
    settings, "EMPLOYEE_ATTRIBUTE_LABEL", "Matricola dipendente"
)

# Label
ORGANIZATION_EMPLOYEE_LABEL = getattr(
    settings, "ORGANIZATION_EMPLOYEE_LABEL", "Dipendenti"
)
# If True, an internal user (not guest) is a user that has this filled (in user model)
# If False, an internal user is a user that is mapped as OrganizationalStructureOfficeEmployee
USER_ATTRIBUTE_NAME = getattr(
    settings, "USER_ATTRIBUTE_NAME", "matricola_studente")
USER_ATTRIBUTE_LABEL = getattr(
    settings, "USER_ATTRIBUTE_LABEL", "Matricola studente")

# Ticket categories CSV export
# additional user fields to export
ADDITIONAL_USER_FIELDS = getattr(
    settings, "ADDITIONAL_USER_FIELDS", [
        EMPLOYEE_ATTRIBUTE_NAME, USER_ATTRIBUTE_NAME]
)

# REQUIRED
UO_DICT = getattr(
    settings,
    "UO_DICT",
    (
        ("2015.1","AMMINISTRAZIONE CTC"),
        ("2013.1","AMMINISTRAZIONE DEMACS"),
        ("2025.1","AMMINISTRAZIONE DESF"),
        ("2020.1","AMMINISTRAZIONE DIAM"),
        ("2014.1","AMMINISTRAZIONE DIBEST"),
        ("2022.1","AMMINISTRAZIONE DICES"),
        ("2019.1","AMMINISTRAZIONE DIMEG"),
        ("2017.1","AMMINISTRAZIONE DIMES"),
        ("2018.1","AMMINISTRAZIONE DINCI"),
        ("2024.1","AMMINISTRAZIONE DISCAG"),
        ("0","UNIVERSITA' DELLA CALABRIA")
    )
)

TITOLARIO_DICT = (
    ("Amministrazione",
        (
            ("1/1","Normativa e relativa attuazione"),
            ("1/2","Statuto"),
            ("1/3","Regolamenti"),
            ("1/4","Stemma, gonfalone e sigillo"),
            ("1/5","Sistema informativo, sicurezza dell'informazione e sistema informatico"),
            ("1/6","Protezione dei dati personali"),
            ("1/7","Archivio"),
            ("1/8","Trasparenza e relazioni con il pubblico"),
            ("1/9","Strategie per il personale, organigramma e funzionigramma"),
            ("1/10","Rapporti sindacali e contrattazione"),
            ("1/11","Controllo di gestione e sistema qualità"),
            ("1/12","Statistica e auditing"),
            ("1/13","Elezioni e designazioni"),
            ("1/14","Associazioni e attività culturali, sportive e ricreative"),
            ("1/15","Editoria e attività informativo-promozionale"),
            ("1/16","Onorificenze, cerimoniale e attività di rappresentanza"),
            ("1/17","Politiche e interventi per le pari opportunità"),
            ("1/18","Interventi di carattere politico, economico, sociale e umanitario")
        )
    ),
    ("Organi di governo, gestione, controllo, consulenza e garanzia",
        (
            ("2/1","Rettore"),
            ("2/2","Prorettore vicario e delegati"),
            ("2/3","Direttore generale"),
            ("2/4","Direttore"),
            ("2/5","Presidente"),
            ("2/6","Senato accademico"),
            ("2/7","Consiglio di amministrazione"),
            ("2/8","Consiglio"),
            ("2/9","Giunta"),
            ("2/10","Commissione didattica paritetica docenti-studenti"),
            ("2/11","Nucleo di valutazione"),
            ("2/12","Collegio dei revisori dei conti"),
            ("2/13","Collegio di disciplina (per i docenti)"),
            ("2/14","Senato degli studenti"),
            ("2/15","Comitato unico di garanzia e per le pari opportunità"),
            ("2/16","Comitato tecnico scientifico"),
            ("2/17","Conferenza dei rettori delle università italiane - CRUI"),
            ("2/18","Comitato regionale di coordinamento"),
            ("2/19","Comitato per lo sport universitario")
        )
    ),
    ("Didattica, ricerca, programmazione e sviluppo",
        (
            ("3/1","Ordinamento didattico"),
            ("3/2","Corsi di studio"),
            ("3/3","Corsi a ordinamento speciale"),
            ("3/4","Corsi di specializzazione"),
            ("3/5","Master"),
            ("3/6","Corsi di dottorato"),
            ("3/7","Corsi di perfezionamento e corsi di formazione permanente"),
            ("3/8","Programmazione didattica, orario delle lezioni, gestione delle aule e degli spazi"),
            ("3/9","Gestione di esami di profitto, di laurea e di prove di idoneità"),
            ("3/10","Programmazione e sviluppo, comprese aree, macroaree e settori scientifico-disciplinari"),
            ("3/11","Strategie e valutazione della didattica e della ricerca"),
            ("3/12","Premi e borse di studio finalizzati e vincolati"),
            ("3/13","Progetti e finanziamenti"),
            ("3/14","Accordi per la didattica e la ricerca"),
            ("3/15","Rapporti con enti e istituti di area socio-sanitaria"),
            ("3/16","Opere dell'ingegno, brevetti e imprenditoria della ricerca"),
            ("3/17","Piani di sviluppo dell'università"),
            ("3/18","Cooperazione con paesi in via di sviluppo"),
            ("3/19","Attività per conto terzi")
        )
    ),
    ("Attività giuridico-legale",
        (
            ("4/1","Contenzioso"),
            ("4/2","Atti di liberalità"),
            ("4/3","Violazioni amministrative e reati"),
            ("4/4","Responsabilità civile, penale e amministrativa del personale"),
            ("4/5","Pareri e consulenze")
        )
    ),
    ("Studenti e laureati",
        (
            ("5/1","Orientamento, informazione e tutorato"),
            ("5/2","Selezioni, immatricolazioni e ammissioni"),
            ("5/3","Trasferimenti e passaggi"),
            ("5/4","Cursus studiorum e provvedimenti disciplinari"),
            ("5/5","Diritto allo studio, assicurazioni, benefici economici, tasse e contributi"),
            ("5/6","Tirocinio, formazione e attività di ricerca"),
            ("5/7","Servizi di assistenza socio-sanitaria e a richiesta"),
            ("5/8","Conclusione e cessazione della carriera di studio"),
            ("5/9","Esami di stato e ordini professionali"),
            ("5/10","Associazionismo, goliardia e manifestazioni organizzate da studenti o ex studenti"),
            ("5/11","Benefici Legge 390/91"),
            ("5/12","Servizi abitativi e mensa per gli studenti"),
            ("5/13","Attività culturali e ricreative")
        )
    ),
    ("Strutture didattiche, di ricerca e di servizio",
        (
            ("6/1","Poli"),
            ("6/2","Scuole e strutture di raccordo"),
            ("6/3","Dipartimenti"),
            ("6/4","Strutture a ordinamento speciale"),
            ("6/5","Scuole di specializzazione"),
            ("6/6","Scuole di dottorato"),
            ("6/7","Scuole interdipartimentali"),
            ("6/8","Centri"),
            ("6/9","Sistema bibliotecario"),
            ("6/10","Musei, pinacoteche e collezioni"),
            ("6/11","Consorzi ed enti a partecipazione universitaria"),
            ("6/12","Fondazioni"),
            ("6/13","Servizi di ristorazione, alloggi e foresterie")
        )
    ),
    ("Personale",
        (
            ("7/1","Concorsi e selezioni"),
            ("7/2","Assunzioni e cessazioni"),
            ("7/3","Comandi e distacchi"),
            ("7/4","Mansioni e incarichi"),
            ("7/5","Carriera e inquadramenti"),
            ("7/6","Retribuzione e compensi"),
            ("7/7","Adempimenti fiscali, contributivi e assicurativi"),
            ("7/8","Pre-ruolo, trattamento di quiescenza, buonuscita"),
            ("7/9","Dichiarazioni di infermità ed equo indennizzo"),
            ("7/10","Servizi a domanda individuale"),
            ("7/11","Assenze"),
            ("7/12","Tutela della salute e sorveglianza sanitaria"),
            ("7/13","Valutazione, giudizi di merito e provvedimenti disciplinari"),
            ("7/14","Formazione e aggiornamento professionale"),
            ("7/15","Deontologia professionale ed etica del lavoro"),
            ("7/16","Personale non strutturato")
        )
    ),
    ("Finanza, contabilità e bilancio",
        (
            ("8/1","Ricavi ed entrate"),
            ("8/2","Costi e uscite"),
            ("8/3","Bilancio"),
            ("8/4","Tesoreria, cassa e istituti di credito"),
            ("8/5","Imposte, tasse, ritenute previdenziali e assistenziali")
        )
    ),
    ("Edilizia e territorio",
        (
            ("9/1","Progettazione e costruzione di opere edilizie con relativi impianti"),
            ("9/2","Manutenzione ordinaria, straordinaria, ristrutturazione, restauro e destinazione d'uso"),
            ("9/3","Sicurezza e messa a norma degli ambienti di lavoro"),
            ("9/4","Telefonia e infrastruttura informatica"),
            ("9/5","Programmazione Territoriale")
        )
    ),
    ("Patrimonio, economato e provveditorato",
        (
            ("10/1","Acquisizione e gestione di beni immobili e relativi servizi"),
            ("10/2","Locazione di beni immobili, di beni mobili e relativi servizi"),
            ("10/3","Alienazione di beni immobili e di beni mobili"),
            ("10/4","Acquisizione e fornitura di beni mobili, di materiali e attrezzature non tecniche e di servizi"),
            ("10/5","Manutenzione di beni mobili"),
            ("10/6","Materiali, attrezzature, impiantistica e adempimenti tecnico-normativi"),
            ("10/7","Partecipazioni e investimenti finanziari"),
            ("10/8","Inventario, rendiconto patrimoniale, beni in comodato"),
            ("10/9","Patrimonio culturale – Tutela e valorizzazione"),
            ("10/10","Gestione dei rifiuti"),
            ("10/11","Albo dei fornitori")
        )
    ),
    # ("Oggetti diversi")
)

# END REQUIRED

# Label
ORGANIZATION_USER_LABEL = getattr(
    settings, "ORGANIZATION_USER_LABEL", "Studenti")

# error message for user that has compiled a request but it's not the owner
TICKET_SHARING_USER_ERROR_MESSAGE = getattr(
    settings,
    "TICKET_SHARING_USER_ERROR_MESSAGE",
    _(
        "Impossibile effettuare l'operazione."
        "<br>"
        "Nonostante tu abbia precompilato la richiesta, "
        "è l'utente <b>{}</b> che l'ha sottomessa"
    ),
)

# E-mail messages
MSG_HEADER = getattr(
    settings,
    "MSG_HEADER",
    _(
        """Gentile utente,
questo messaggio è stato inviato da {hostname}.
Per favore non rispondere a questa email.

-------------------

"""
    ),
)

MSG_FOOTER = getattr(
    settings,
    "MSG_FOOTER",
    _(
        """

-------------------

Per problemi tecnici contatta il nostro staff.
Cordiali saluti.
"""
    ),
)

UNAVAILABLE_TICKET_CATEGORY = getattr(
    settings,
    "UNAVAILABLE_TICKET_CATEGORY",
    _("""La tipologia di richiesta non è attiva"""),
)

NEW_TICKET_CREATED_ALERT = getattr(
    settings, "NEW_TICKET_CREATED_ALERT", _(
        """Richiesta "{}" creata con successo""")
)

NEW_TICKET_CREATED = getattr(
    settings,
    "NEW_TICKET_CREATED",
    _(
        """{added_text}

L'identificativo univoco di questa transazione è {ticket}.

Clicca qui {url} per prenderne visione."""
    ),
)

TICKET_UPDATED = getattr(
    settings,
    "TICKET_UPDATED",
    _(
        """La richiesta "{ticket}" è stata aggiornata con il seguente messaggio:

{message}"""
    ),
)

USER_TICKET_MESSAGE = getattr(
    settings,
    "USER_TICKET_MESSAGE",
    _(
        """Hai {status} un nuovo messaggio per la richiesta \"{ticket}\"

Oggetto: {message_subject}

Testo: {message_text}

Clicca qui {url} per aprire il pannello dei messaggi."""
    ),
)

TICKET_DELETED = getattr(
    settings,
    "TICKET_DELETED",
    _("""La richiesta "{ticket}" è stata eliminata correttamente."""),
)

SUMMARY_USER_EMAIL = getattr(
    settings,
    "SUMMARY_USER_EMAIL",
    _(
        """La seguente richiesta {event msg}:

{ticket}"""
    ),
)

SUMMARY_EMPLOYEE_EMAIL = getattr(
    settings,
    "SUMMARY_EMPLOYEE_EMAIL",
    _(
        """Ci sono {opened_ticket_number} richieste da gestire.

{tickets_per_office}"""
    ),
)

NEW_TICKET_CREATED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_TICKET_CREATED_EMPLOYEE_BODY",
    _(
        """E' stata effettuata una nuova richiesta all'ufficio {destination_office}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)

NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY",
    _(
        """Hai ricevuto un nuovo messaggio per la richiesta \"{ticket}\"

Oggetto: {message_subject}

Testo: {message_text}

Clicca qui {url} per aprire il pannello dei messaggi."""
    ),
)

NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY = getattr(
    settings,
    "NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY",
    _(
        """Ti è stata assegnata una nuova richiesta da {manager}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)

# Old english version
NEW_TICKET_UPDATE_OLD_EN = getattr(
    settings,
    "NEW_TICKET_UPDATE_OLD_EN",
    _(
        "Dear user,"
        "you have successfully {status} the ticket:"
        ""
        "{ticket}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

USER_TICKET_MESSAGE_OLD_EN = getattr(
    settings,
    "USER_TICKET_MESSAGE_OLD_EN",
    _(
        "Dear {user},"
        "you have successfully {status} a message for ticket:"
        ""
        "{ticket}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

TICKET_UPDATED_OLD_EN = getattr(
    settings,
    "TICKET_UPDATED_OLD_EN",
    _(
        "Dear {user},"
        "the ticket:"
        ""
        "{ticket}"
        ""
        "has been updated with the message:"
        ""
        "{message}."
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

SUMMARY_USER_EMAIL_OLD_EN = getattr(
    settings,
    "SUMMARY_USER_EMAIL_OLD_EN",
    _(
        "Dear {user},"
        "the following ticket {event_msg}:"
        ""
        "{ticket}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

SUMMARY_EMPLOYEE_EMAIL_OLD_EN = getattr(
    settings,
    "SUMMARY_EMPLOYEE_EMAIL_OLD_EN",
    _(
        "Dear {user},"
        "You have {open_ticket_number} tickets to manage."
        ""
        "{tickets_per_office}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)
