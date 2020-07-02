[1mdiff --git a/docs/source/01_getting-started/getting_started.rst b/docs/source/01_getting-started/getting_started.rst[m
[1mindex 6fcd742..149087e 100644[m
[1m--- a/docs/source/01_getting-started/getting_started.rst[m
[1m+++ b/docs/source/01_getting-started/getting_started.rst[m
[36m@@ -168,7 +168,7 @@[m [mNel file di configurazione generale **uni_ticket_project/settingslocal.py** è p[m
     <Denominazione>UNICAL</Denominazione>[m
     <CodiceAmministrazione>UNICAL</CodiceAmministrazione>[m
     <IndirizzoTelematico tipo="smtp">amministrazione@pec.unical.it</IndirizzoTelematico>[m
[31m-    <UnitaOrganizzativa id="{uo_id}"/>[m
[32m+[m[32m    <UnitaOrganizzativa id=""/>[m
     </Amministrazione>[m
     </Destinatario>[m
     <Classifica>[m
[36m@@ -200,7 +200,7 @@[m [mNel file di configurazione generale **uni_ticket_project/settingslocal.py** è p[m
     PROT_FASCICOLO_ANNO_DEFAULT = 'default_year'[m
     PROT_AGD_DEFAULT = 'default_agd'[m
     PROT_UO_DEFAULT = 'default_uo'[m
[31m-    PROT_UO_ID_DEFAULT = 'default_uo_id'[m
[32m+[m[32m    # PROT_UO_ID_DEFAULT = 'default_uo_id'[m
     PROT_TITOLARIO_DEFAULT = 'default_titolario'[m
     PROT_TEST_URL = 'url_test'[m
     PROT_TEST_LOGIN = 'test_login'[m
[1mdiff --git a/protocollo_ws/protocollo.py b/protocollo_ws/protocollo.py[m
[1mindex c4a55a7..47f728a 100644[m
[1m--- a/protocollo_ws/protocollo.py[m
[1m+++ b/protocollo_ws/protocollo.py[m
[36m@@ -38,7 +38,7 @@[m [mclass WSArchiPROClient(object):[m
                            'agd',[m
                            'uo',[m
                            'email',[m
[31m-                           'uo_id',[m
[32m+[m[32m                           # 'uo_id',[m
                            'fascicolo_numero',[m
                            'fascicolo_anno',[m
                            'id_titolario',[m
[1mdiff --git a/protocollo_ws/settings.py b/protocollo_ws/settings.py[m
[1mindex 05545f0..7ed86aa 100644[m
[1m--- a/protocollo_ws/settings.py[m
[1m+++ b/protocollo_ws/settings.py[m
[36m@@ -1,3 +1,6 @@[m
[32m+[m[32mfrom django.utils.translation import gettext_lazy as _[m
[32m+[m
[32m+[m
 # win-chrk4d7tc85 must be resolved in /etc/hosts or DNS[m
 PROT_DOC_ENCODING = 'utf-8'[m
 PROT_MAX_LABEL_LENGTH = 99[m
[36m@@ -24,10 +27,10 @@[m [mPROT_EMAIL_DEFAULT = 'amministrazione@pec.unical.it'[m
 # vengono istruite le pratiche all'interno del sistema di protocollo di riferimento[m
 PROT_FASCICOLO_DEFAULT = '3'[m
 PROT_TITOLARIO_DEFAULT = '9095'[m
[31m-PROT_CODICI_TITOLARI = ([m
[31m-                           ('9095','7.1'),[m
[31m-                           ('9099', '7.5'),[m
[31m-                        )[m
[32m+[m[32m# PROT_CODICI_TITOLARI = ([m
[32m+[m[32m                           # ('9095','7.1'),[m
[32m+[m[32m                           # ('9099', '7.5'),[m
[32m+[m[32m                        # )[m
 [m
 PROT_AOO = 'AOO55' # test[m
 # PROT_AOO = 'AOO1' # produzione[m
[36m@@ -41,3 +44,131 @@[m [mPROT_PASSW = 'UT_PROTO_WS'[m
 PROT_URL = 'http://PROT_URL?wsdl'[m
 PROT_LOGIN = 'UT_PROTO_WS'[m
 PROT_PASSW = 'UT_PROTO_WS'[m
[32m+[m
[32m+[m[32mTITOLARIO_DICT = ([m
[32m+[m[32m    ("9002", _("Normativa e relativa attuazione")),[m
[32m+[m[32m    ("9003", _("Statuto")),[m
[32m+[m[32m    ("9004", _("Regolamenti")),[m
[32m+[m[32m    ("9005", _("Stemma, gonfalone e sigillo")),[m
[32m+[m[32m    ("9006", _("Sistema informativo, sicurezza dell'informazione e sistema informatico")),[m
[32m+[m[32m    ("9007", _("Protezione dei dati personali")),[m
[32m+[m[32m    ("9008", _("Archivio")),[m
[32m+[m[32m    ("9009", _("Trasparenza e relazioni con il pubblico")),[m
[32m+[m[32m    ("9010", _("Strategie per il personale, organigramma e funzionigramma")),[m
[32m+[m[32m    ("9011", _("Rapporti sindacali e contrattazione")),[m
[32m+[m[32m    ("9012", _("Controllo di gestione e sistema qualità")),[m
[32m+[m[32m    ("9013", _("Statistica e auditing")),[m
[32m+[m[32m    ("9014", _("Elezioni e designazioni")),[m
[32m+[m[32m    ("9015", _("Associazioni e attività culturali, sportive e ricreative")),[m
[32m+[m[32m    ("9016", _("Editoria e attività informativo-promozionale")),[m
[32m+[m[32m    ("9017", _("Onorificenze, cerimoniale e attività di rappresentanza")),[m
[32m+[m[32m    ("9018", _("Politiche e interventi per le pari opportunità")),[m
[32m+[m[32m    ("9019", _("Interventi di carattere politico, economico, sociale e umanitario")),[m
[32m+[m[32m    ("9021", _("Rettore")),[m
[32m+[m[32m    ("9022", _("Prorettore vicario e delegati")),[m
[32m+[m[32m    ("9023", _("Direttore generale")),[m
[32m+[m[32m    ("9024", _("Direttore")),[m
[32m+[m[32m    ("9025", _("Presidente")),[m
[32m+[m[32m    ("9026", _("Senato accademico")),[m
[32m+[m[32m    ("9027", _("Consiglio di amministrazione")),[m
[32m+[m[32m    ("9028", _("Consiglio")),[m
[32m+[m[32m    ("9029", _("Giunta")),[m
[32m+[m[32m    ("9030", _("Commissione didattica paritetica docenti-studenti")),[m
[32m+[m[32m    ("9031", _("Nucleo di valutazione")),[m
[32m+[m[32m    ("9032", _("Collegio dei revisori dei conti")),[m
[32m+[m[32m    ("9033", _("Collegio di disciplina (per i docenti)")),[m
[32m+[m[32m    ("9034", _("Senato degli studenti")),[m
[32m+[m[32m    ("9035", _("Comitato unico di garanzia e per le pari opportunità")),[m
[32m+[m[32m    ("9036", _("Comitato tecnico scientifico")),[m
[32m+[m[32m    ("9037", _("Conferenza dei rettori delle università italiane - CRUI")),[m
[32m+[m[32m    ("9038", _("Comitato regionale di coordinamento")),[m
[32m+[m[32m    ("9039", _("Comitato per lo sport universitario")),[m
[32m+[m[32m    ("9041", _("Ordinamento didattico")),[m
[32m+[m[32m    ("9042", _("Corsi di studio")),[m
[32m+[m[32m    ("9043", _("Corsi a ordinamento speciale")),[m
[32m+[m[32m    ("9044", _("Corsi di specializzazione")),[m
[32m+[m[32m    ("9045", _("Master")),[m
[32m+[m[32m    ("9046", _("Corsi di dottorato")),[m
[32m+[m[32m    ("9047", _("Corsi di perfezionamento e corsi di formazione permanente")),[m
[32m+[m[32m    ("9048", _("Programmazione didattica, orario delle lezioni, gestione delle aule e degli spazi")),[m
[32m+[m[32m    ("9049", _("Gestione di esami di profitto, di laurea e di prove di idoneità")),[m
[32m+[m[32m    ("9050", _("Programmazione e sviluppo, comprese aree, macroaree e settori scientifico-disciplinari")),[m
[32m+[m[32m    ("9051", _("Strategie e valutazione della didattica e della ricerca")),[m
[32m+[m[32m    ("9052", _("Premi e borse di studio finalizzati e vincolati")),[m
[32m+[m[32m    ("9053", _("Progetti e finanziamenti")),[m
[32m+[m[32m    ("9054", _("Accordi per la didattica e la ricerca")),[m
[32m+[m[32m    ("9055", _("Rapporti con enti e istituti di area socio-sanitaria")),[m
[32m+[m[32m    ("9056", _("Opere dell'ingegno, brevetti e imprenditoria della ricerca")),[m
[32m+[m[32m    ("9057", _("Piani di sviluppo dell'università")),[m
[32m+[m[32m    ("9058", _("Cooperazione con paesi in via di sviluppo")),[m
[32m+[m[32m    ("9059", _("Attività per conto terzi")),[m
[32m+[m[32m    ("9061", _("Contenzioso")),[m
[32m+[m[32m    ("9062", _("Atti di liberalità")),[m
[32m+[m[32m    ("9063", _("Violazioni amministrative e reati")),[m
[32m+[m[32m    ("9064", _("Responsabilità civile, penale e amministrativa del personale")),[m
[32m+[m[32m    ("9065", _("Pareri e consulenze")),[m
[32m+[m[32m    ("9067", _("Orientamento, informazione e tutorato")),[m
[32m+[m[32m    ("9068", _("Selezioni, immatricolazioni e ammissioni")),[m
[32m+[m[32m    ("9069", _("Trasferimenti e passaggi")),[m
[32m+[m[32m    ("9070", _("Cursus studiorum e provvedimenti disciplinari")),[m
[32m+[m[32m    ("9071", _("Diritto allo studio, assicurazioni, benefici economici, tasse e contributi")),[m
[32m+[m[32m    ("9072", _("Tirocinio, formazione e attività di ricerca")),[m
[32m+[m[32m    ("9073", _("Servizi di assistenza socio-sanitaria e a richiesta")),[m
[32m+[m[32m    ("9074", _("Conclusione e cessazione della carriera di studio")),[m
[32m+[m[32m    ("9075", _("Esami di stato e ordini professionali")),[m
[32m+[m[32m    ("9076", _("Associazionismo, goliardia e manifestazioni organizzate da studenti o ex studenti")),[m
[32m+[m[32m    ("9077", _("Benefici Legge 390/91 ")),[m
[32m+[m[32m    ("9078", _("Servizi abitativi e mensa per gli studenti")),[m
[32m+[m[32m    ("9079", _("Attività culturali e ricreative")),[m
[32m+[m[32m    ("9081", _("Poli")),[m
[32m+[m[32m    ("9082", _("Scuole e strutture di raccordo")),[m
[32m+[m[32m    ("9083", _("Dipartimenti")),[m
[32m+[m[32m    ("9084", _("Strutture a ordinamento speciale")),[m
[32m+[m[32m    ("9085", _("Scuole di specializzazione")),[m
[32m+[m[32m    ("9086", _("Scuole di dottorato")),[m
[32m+[m[32m    ("9087", _("Scuole interdipartimentali")),[m
[32m+[m[32m    ("9088", _("Centri")),[m
[32m+[m[32m    ("9089", _("Sistema bibliotecario")),[m
[32m+[m[32m    ("9090", _("Musei, pinacoteche e collezioni")),[m
[32m+[m[32m    ("9091", _("Consorzi ed enti a partecipazione universitaria")),[m
[32m+[m[32m    ("9092", _("Fondazioni")),[m
[32m+[m[32m    ("9093", _("Servizi di ristorazione, alloggi e foresterie")),[m
[32m+[m[32m    ("9095", _("Concorsi e selezioni")),[m
[32m+[m[32m    ("9096", _("Assunzioni e cessazioni")),[m
[32m+[m[32m    ("9097", _("Comandi e distacchi")),[m
[32m+[m[32m    ("9098", _("Mansioni e incarichi")),[m
[32m+[m[32m    ("9099", _("Carriera e inquadramenti")),[m
[32m+[m[32m    ("9100", _("Retribuzione e compensi")),[m
[32m+[m[32m    ("9101", _("Adempimenti fiscali, contributivi e assicurativi")),[m
[32m+[m[32m    ("9102", _("Pre-ruolo, trattamento di quiescenza, buonuscita")),[m
[32m+[m[32m    ("9103", _("Dichiarazioni di infermità ed equo indennizzo")),[m
[32m+[m[32m    ("9104", _("Servizi a domanda individuale")),[m
[32m+[m[32m    ("9105", _("Assenze")),[m
[32m+[m[32m    ("9106", _("Tutela della salute e sorveglianza sanitaria")),[m
[32m+[m[32m    ("9107", _("Valutazione, giudizi di merito e provvedimenti disciplinari")),[m
[32m+[m[32m    ("9108", _("Formazione e aggiornamento professionale")),[m
[32m+[m[32m    ("9109", _("Deontologia professionale ed etica del lavoro")),[m
[32m+[m[32m    ("9110", _("Personale non strutturato")),[m
[32m+[m[32m    ("9112", _("Ricavi ed entrate")),[m
[32m+[m[32m    ("9113", _("Costi e uscite")),[m
[32m+[m[32m    ("9114", _("Bilancio")),[m
[32m+[m[32m    ("9115", _("Tesoreria, cassa e istituti di credito")),[m
[32m+[m[32m    ("9116", _("Imposte, tasse, ritenute previdenziali e assistenziali")),[m
[32m+[m[32m    ("9118", _("Progettazione e costruzione di opere edilizie con relativi impianti")),[m
[32m+[m[32m    ("9119", _("Manutenzione ordinaria, straordinaria, ristrutturazione, restauro e destinazione d'uso")),[m
[32m+[m[32m    ("9120", _("Sicurezza e messa a norma degli ambienti di lavoro")),[m
[32m+[m[32m    ("9121", _("Telefonia e infrastruttura informatica")),[m
[32m+[m[32m    ("9122", _("Programmazione Territoriale")),[m
[32m+[m[32m    ("9124", _("Acquisizione e gestione di beni immobili e relativi servizi")),[m
[32m+[m[32m    ("9125", _("Locazione di beni immobili, di beni mobili e relativi servizi")),[m
[32m+[m[32m    ("9126", _("Alienazione di beni immobili e di beni mobili")),[m
[32m+[m[32m    ("9127", _("Acquisizione e fornitura di beni mobili, di materiali e attrezzature non tecniche e di servizi")),[m
[32m+[m[32m    ("9128", _("Manutenzione di beni mobili")),[m
[32m+[m[32m    ("9129", _("Materiali, attrezzature, impiantistica e adempimenti tecnico-normativi")),[m
[32m+[m[32m    ("9130", _("Partecipazioni e investimenti finanziari")),[m
[32m+[m[32m    ("9131", _("Inventario, rendiconto patrimoniale, beni in comodato")),[m
[32m+[m[32m    ("9132", _("Patrimonio culturale – Tutela e valorizzazione")),[m
[32m+[m[32m    ("9133", _("Gestione dei rifiuti")),[m
[32m+[m[32m    ("9134", _("Albo dei fornitori")),[m
[32m+[m[32m    ("9135", _("Oggetti diversi")),[m
[32m+[m[32m)[m
[1mdiff --git a/protocollo_ws/xml_templates/generalizzati/protocollo_entrata.tmpl.j2 b/protocollo_ws/xml_templates/generalizzati/protocollo_entrata.tmpl.j2[m
[1mindex 6d69e91..1fca971 100644[m
[1m--- a/protocollo_ws/xml_templates/generalizzati/protocollo_entrata.tmpl.j2[m
[1m+++ b/protocollo_ws/xml_templates/generalizzati/protocollo_entrata.tmpl.j2[m
[36m@@ -2,13 +2,13 @@[m
 <Segnatura xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">[m
     <Intestazione>[m
         <Oggetto>Autorizzazione Trasferta Dipendente</Oggetto>[m
[31m-        [m
[32m+[m[41m[m
         <Identificatore>[m
             <CodiceAmministrazione>{codice_amministrazione}</CodiceAmministrazione>[m
             <CodiceAOO>{codice_aoo}</CodiceAOO>[m
             <Flusso>{flusso}</Flusso>[m
         </Identificatore>[m
[31m-        [m
[32m+[m[41m[m
         <Mittente>[m
           <Dipendente id="{matricola_dipendente}">[m
            <Denominazione>{denominazione_persona}</Denominazione>[m
[36m@@ -20,7 +20,7 @@[m
                 <Denominazione>{denominazione_amministrazione}</Denominazione>[m
                 <CodiceAmministrazione>{codice_amministrazione}</CodiceAmministrazione>[m
                 <IndirizzoTelematico tipo="smtp">{email_amministrazione}</IndirizzoTelematico>[m
[31m-                <UnitaOrganizzativa id="{uo_id}" />[m
[32m+[m[32m                <UnitaOrganizzativa id="" />[m[41m[m
             </Amministrazione>[m
         </Destinatario>[m
 [m
[1mdiff --git a/protocollo_ws/xml_templates/generalizzati/protocollo_mittente_unical.tmpl.j2 b/protocollo_ws/xml_templates/generalizzati/protocollo_mittente_unical.tmpl.j2[m
[1mindex b41d74f..9cfd21f 100644[m
[1m--- a/protocollo_ws/xml_templates/generalizzati/protocollo_mittente_unical.tmpl.j2[m
[1m+++ b/protocollo_ws/xml_templates/generalizzati/protocollo_mittente_unical.tmpl.j2[m
[36m@@ -2,28 +2,28 @@[m
 <Segnatura xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">[m
 <Intestazione>[m
     <Oggetto>{oggetto}</Oggetto>[m
[31m-    [m
[32m+[m
     <Identificatore>[m
         <CodiceAmministrazione>{id_amm}</CodiceAmministrazione>[m
         <CodiceAOO>{cod_aoo}</CodiceAOO>[m
         <Flusso>{flusso}</Flusso>[m
     </Identificatore>[m
[31m-    [m
[32m+[m
     <Mittente>[m
         <Amministrazione>[m
             <Denominazione>{id_amm}</Denominazione>[m
             <CodiceAmministrazione>{cod_aoo}</CodiceAmministrazione>[m
             <IndirizzoTelematico tipo="smtp">{email}</IndirizzoTelematico>[m
[31m-            <UnitaOrganizzativa id="{uo_id}" />[m
[32m+[m[32m            <UnitaOrganizzativa id="" />[m
         </Amministrazione>[m
     </Mittente>[m
[31m-    [m
[32m+[m
     <Destinatario>[m
         <Persona id="{identificativo_persona}">[m
             <Denominazione>{denominazione_persona}</Denominazione>[m
         </Persona>[m
     </Destinatario>[m
[31m-    [m
[32m+[m
     <Classifica>[m
         <CodiceTitolario>{cod_titolario}</CodiceTitolario>[m
     </Classifica>[m
[1mdiff --git a/protocollo_ws/xml_templates/generalizzati/protocollo_uscita.tmpl.j2 b/protocollo_ws/xml_templates/generalizzati/protocollo_uscita.tmpl.j2[m
[1mindex 3bc1df5..2976eb9 100644[m
[1m--- a/protocollo_ws/xml_templates/generalizzati/protocollo_uscita.tmpl.j2[m
[1m+++ b/protocollo_ws/xml_templates/generalizzati/protocollo_uscita.tmpl.j2[m
[36m@@ -2,28 +2,28 @@[m
 <Segnatura xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">[m
 <Intestazione>[m
     <Oggetto>{oggetto}</Oggetto>[m
[31m-    [m
[32m+[m
     <Identificatore>[m
         <CodiceAmministrazione>{codice_amministrazione}</CodiceAmministrazione>[m
         <CodiceAOO>{codice_aoo}</CodiceAOO>[m
         <Flusso>{flusso}</Flusso>[m
     </Identificatore>[m
[31m-    [m
[32m+[m
     <Mittente>[m
         <Amministrazione>[m
             <Denominazione>{id_amm}</Denominazione>[m
             <CodiceAmministrazione>{cod_aoo}</CodiceAmministrazione>[m
             <IndirizzoTelematico tipo="smtp">{email}</IndirizzoTelematico>[m
[31m-            <UnitaOrganizzativa id="{uo_id}" />[m
[32m+[m[32m            <UnitaOrganizzativa id="" />[m
         </Amministrazione>[m
     </Mittente>[m
[31m-    [m
[32m+[m
     <Destinatario>[m
         <Persona id="{identificativo_persona}">[m
             <Denominazione>{denominazione_persona}</Denominazione>[m
         </Persona>[m
     </Destinatario>[m
[31m-    [m
[32m+[m
     <Classifica>[m
         <CodiceTitolario>{cod_titolario}</CodiceTitolario>[m
     </Classifica>[m
[1mdiff --git a/protocollo_ws/xml_templates/unical/flusso_entrata.xml_standard.j2 b/protocollo_ws/xml_templates/unical/flusso_entrata.xml_standard.j2[m
[1mindex 825f852..db288f5 100644[m
[1m--- a/protocollo_ws/xml_templates/unical/flusso_entrata.xml_standard.j2[m
[1m+++ b/protocollo_ws/xml_templates/unical/flusso_entrata.xml_standard.j2[m
[36m@@ -19,7 +19,7 @@[m
                 <Denominazione>UNICAL</Denominazione>[m
                 <CodiceAmministrazione>UNICAL</CodiceAmministrazione>[m
                 <IndirizzoTelematico tipo="smtp">amministrazione@pec.unical.it</IndirizzoTelematico>[m
[31m-                <UnitaOrganizzativa id="{uo_id}"/>[m
[32m+[m[32m                <UnitaOrganizzativa id=""/>[m
             </Amministrazione>[m
         </Destinatario>[m
 [m
[1mdiff --git a/uni_ticket/admin.py b/uni_ticket/admin.py[m
[1mindex 5217c85..410b13d 100644[m
[1m--- a/uni_ticket/admin.py[m
[1m+++ b/uni_ticket/admin.py[m
[36m@@ -93,7 +93,7 @@[m [mclass TaskAdmin(nested_admin.NestedModelAdmin):[m
 [m
 @admin.register(OrganizationalStructureWSArchiPro)[m
 class OrganizationalStructureWSArchiProAdmin(admin.ModelAdmin):[m
[31m-    list_display = ('organizational_structure',[m
[31m-                    'protocollo_cod_titolario',[m
[31m-                    'protocollo_fascicolo_numero',[m
[31m-                    'protocollo_template',)[m
[32m+[m[32m    list_display = ('organizational_structure',)[m
[32m+[m[32m                    # 'protocollo_cod_titolario',[m
[32m+[m[32m                    # 'protocollo_fascicolo_numero',[m
[32m+[m[32m                    # 'protocollo_template',)[m
[1mdiff --git a/uni_ticket/admin_nested_inlines.py b/uni_ticket/admin_nested_inlines.py[m
[1mindex 8bae932..fd622c6 100644[m
[1m--- a/uni_ticket/admin_nested_inlines.py[m
[1m+++ b/uni_ticket/admin_nested_inlines.py[m
[36m@@ -4,6 +4,7 @@[m [mfrom django import forms[m
 from django.contrib import admin[m
 from django.urls import reverse[m
 from django.utils.translation import gettext as _[m
[32m+[m[32mfrom bootstrap_italia_template.widgets import BootstrapItaliaSelectWidget[m
 [m
 from . models import *[m
 [m
[36m@@ -67,19 +68,21 @@[m [mclass TicketCategoryWSArchiProModelForm(forms.ModelForm):[m
     class Meta:[m
         model = TicketCategoryWSArchiPro[m
         fields = ('name',[m
[31m-                  'protocollo_aoo',[m
[31m-                  'protocollo_agd',[m
[31m-                  'protocollo_uo',[m
[31m-                  'protocollo_email',[m
[31m-                  'protocollo_id_uo',[m
[32m+[m[32m                  # 'protocollo_aoo',[m
[32m+[m[32m                  # 'protocollo_agd',[m
[32m+[m[32m                  # 'protocollo_uo',[m
[32m+[m[32m                  # 'protocollo_email',[m
[32m+[m[32m                  # 'protocollo_id_uo',[m
                   'protocollo_cod_titolario',[m
                   'protocollo_fascicolo_numero',[m
[31m-                  'protocollo_fascicolo_anno',[m
[31m-                  'protocollo_template')[m
[32m+[m[32m                  'protocollo_fascicolo_anno',)[m
[32m+[m[32m                  # 'protocollo_template')[m
         help_texts = {'protocollo_email': _('Se vuoto: {}').format(settings.PROT_EMAIL_DEFAULT)}[m
         labels = {'name': _('Denominazione'),[m
[31m-                  'protocollo_cod_titolario': _('Codice titolario')}[m
[31m-        widgets = {'protocollo_template': forms.Textarea(attrs={'rows':2})}[m
[32m+[m[32m                  'protocollo_cod_titolario': _('Titolario'),[m
[32m+[m[32m                  'protocollo_fascicolo_numero': _('Numero Fascicolo'),[m
[32m+[m[32m                  'protocollo_fascicolo_anno': _('Anno Fascicolo')}[m
[32m+[m[32m        widgets = {'protocollo_cod_titolario': BootstrapItaliaSelectWidget}[m
 [m
     class Media:[m
         js = ('js/textarea-autosize.js',)[m
[36m@@ -90,10 +93,10 @@[m [mclass TicketCategoryWSArchiProNestedInline(nested_admin.NestedTabularInline):[m
     #sortable_field_name = "name"[m
     extra = 0[m
     classes = ['collapse',][m
[31m-    readonly_fields = ('name',[m
[31m-                       'protocollo_cod_titolario',[m
[31m-                       'protocollo_fascicolo_numero',[m
[31m-                       'protocollo_template')[m
[32m+[m[32m    # readonly_fields = ('name',[m
[32m+[m[32m                       # 'protocollo_cod_titolario',[m
[32m+[m[32m                       # 'protocollo_fascicolo_numero',)[m
[32m+[m[32m                       # 'protocollo_template')[m
 [m
 [m
 # Ticket Category Task Form[m
[1mdiff --git a/uni_ticket/forms.py b/uni_ticket/forms.py[m
[1mindex 870e12d..9ce6906 100644[m
[1m--- a/uni_ticket/forms.py[m
[1m+++ b/uni_ticket/forms.py[m
[36m@@ -35,6 +35,7 @@[m [mclass CategoryForm(ModelForm):[m
                   'description': _('Descrizione'),[m
                   'allowed_users': _('Solo i seguenti utenti possono effettuare richieste')}[m
         widgets = {'description': forms.Textarea(attrs={'rows':2}),[m
[32m+[m[32m                   'confirm_message_text': forms.Textarea(attrs={'rows':2}),[m
                    'allowed_users': BootstrapItaliaSelectMultipleWidget,}[m
 [m
     class Media:[m
[36m@@ -399,18 +400,27 @@[m [mclass OrganizationalStructureWSArchiProModelForm(ModelForm):[m
     class Meta:[m
         model = OrganizationalStructureWSArchiPro[m
         fields = ['name',[m
[32m+[m[32m                  'protocollo_username',[m
[32m+[m[32m                  'protocollo_password',[m
                   'protocollo_aoo',[m
                   'protocollo_agd',[m
                   'protocollo_uo',[m
[31m-                  'protocollo_email',[m
[31m-                  'protocollo_id_uo',[m
[31m-                  'protocollo_cod_titolario',[m
[31m-                  'protocollo_fascicolo_numero',[m
[31m-                  'protocollo_fascicolo_anno',[m
[31m-                  'protocollo_template'][m
[31m-        help_texts = {'protocollo_email': _('Se vuoto: {}').format(settings.PROT_EMAIL_DEFAULT)}[m
[31m-        labels = {'protocollo_cod_titolario': _('Codice titolario')}[m
[31m-        widgets = {'protocollo_template': forms.Textarea(attrs={'rows':2})}[m
[32m+[m[32m                  'protocollo_email',][m
[32m+[m[32m                  # 'protocollo_id_uo',[m
[32m+[m[32m                  # 'protocollo_cod_titolario',[m
[32m+[m[32m                  # 'protocollo_fascicolo_numero',[m
[32m+[m[32m                  # 'protocollo_fascicolo_anno',[m
[32m+[m[32m                  # 'protocollo_template'][m
[32m+[m[32m        # help_texts = {'protocollo_email': _('Se vuoto: {}').format(settings.PROT_EMAIL_DEFAULT)}[m
[32m+[m[32m        # labels = {'protocollo_cod_titolario': _('Codice titolario')}[m
[32m+[m[32m        widgets = {'name': forms.TextInput(attrs={'disabled': True}),[m
[32m+[m[32m                   'protocollo_username': forms.TextInput(attrs={'disabled': True}),[m
[32m+[m[32m                   'protocollo_password': forms.TextInput(attrs={'disabled': True}),[m
[32m+[m[32m                   'protocollo_aoo': forms.TextInput(attrs={'disabled': True}),[m
[32m+[m[32m                   'protocollo_agd': forms.TextInput(attrs={'disabled': True}),[m
[32m+[m[32m                   'protocollo_uo': forms.TextInput(attrs={'disabled': True}),[m
[32m+[m[32m                   'protocollo_email': forms.TextInput(attrs={'disabled': True}),}[m
[32m+[m[32m                   # 'protocollo_template': forms.Textarea(attrs={'disabled': True})}[m
 [m
     class Media:[m
         js = ('js/textarea-autosize.js',)[m
[1mdiff --git a/uni_ticket/models.py b/uni_ticket/models.py[m
[1mindex 07bf1d2..43bfca2 100644[m
[1m--- a/uni_ticket/models.py[m
[1m+++ b/uni_ticket/models.py[m
[36m@@ -174,13 +174,22 @@[m [mclass TicketCategory(models.Model):[m
         if user_is_in_organization(user) and self.allow_user: return True[m
         return False[m
 [m
[32m+[m[32m    def get_active_structure_protocolo_configuration(self):[m
[32m+[m[32m        oswsap = OrganizationalStructureWSArchiPro[m
[32m+[m[32m        conf = oswsap.get_active_protocol_configuration(self.organizational_structure)[m
[32m+[m[32m        return conf if conf else False[m
[32m+[m
     def get_active_protocol_configuration(self):[m
[32m+[m[32m        if not self.get_active_structure_protocolo_configuration():[m
[32m+[m[32m            return False[m
[32m+[m
         tcwap = TicketCategoryWSArchiPro[m
         conf = tcwap.objects.filter(ticket_category=self,[m
                                     is_active=True).first()[m
[31m-        if not conf:[m
[31m-            oswsap = OrganizationalStructureWSArchiPro[m
[31m-            conf = oswsap.get_active_protocol_configuration(organizational_structure=self.organizational_structure)[m
[32m+[m[32m        # if not conf:[m
[32m+[m[32m            # oswsap = OrganizationalStructureWSArchiPro[m
[32m+[m[32m            # conf = oswsap.get_active_protocol_configuration(organizational_structure=self.organizational_structure)[m
[32m+[m
         return conf if conf else False[m
 [m
     def __str__(self):[m
[36m@@ -1165,40 +1174,61 @@[m [mclass TicketCategoryTask(AbstractTask):[m
         return '{} - {}'.format(self.subject, self.category)[m
 [m
 [m
[31m-class AbstractWSArchiPro(models.Model):[m
[31m-    """[m
[31m-    """[m
[32m+[m[32m# class AbstractWSArchiPro(models.Model):[m
[32m+[m[32m    # """[m
[32m+[m[32m    # """[m
[32m+[m[32m    # name = models.CharField(max_length=255)[m
[32m+[m[32m    # created = models.DateTimeField(auto_now=True)[m
[32m+[m[32m    # modified = models.DateTimeField(auto_now=True)[m
[32m+[m[32m    # is_active = models.BooleanField(default=False)[m
[32m+[m
[32m+[m[32m    # protocollo_aoo = models.CharField('AOO', max_length=12)[m
[32m+[m[32m    # protocollo_agd = models.CharField('AGD', max_length=12)[m
[32m+[m[32m    # protocollo_uo = models.CharField('UO', max_length=12,)[m
[32m+[m[32m    # protocollo_email = models.EmailField('E-mail',[m
[32m+[m[32m                                         # max_length=255,[m
[32m+[m[32m                                         # blank=True, null=True)[m
[32m+[m[32m    # protocollo_id_uo = models.CharField(_('ID Unità Organizzativa'),[m
[32m+[m[32m                                      # max_length=12)[m
[32m+[m[32m    # protocollo_cod_titolario = models.CharField(_('Codice titolario'),[m
[32m+[m[32m                                                # max_length=12,[m
[32m+[m[32m                                                # choices=settings.TITOLARIO_DICT)[m
[32m+[m[32m    # protocollo_fascicolo_numero = models.CharField(_('Fascicolo numero'),[m
[32m+[m[32m                                                   # max_length=12)[m
[32m+[m[32m                                                   # default=settings.PROTOCOLLO_FASCICOLO_DEFAULT)[m
[32m+[m[32m    # protocollo_fascicolo_anno = models.IntegerField(_('Fascicolo anno'))[m
[32m+[m[32m    # protocollo_template = models.TextField('XML template',[m
[32m+[m[32m                                           # help_text=_('Template XML che '[m
[32m+[m[32m                                                      # 'descrive il flusso'))[m
[32m+[m
[32m+[m[32m    # class Meta:[m
[32m+[m[32m        # abstract = True[m
[32m+[m
[32m+[m
[32m+[m[32mclass OrganizationalStructureWSArchiPro(models.Model):[m
[32m+[m[32m    organizational_structure = models.ForeignKey(OrganizationalStructure,[m
[32m+[m[32m                                                 on_delete=models.CASCADE)[m
     name = models.CharField(max_length=255)[m
     created = models.DateTimeField(auto_now=True)[m
     modified = models.DateTimeField(auto_now=True)[m
     is_active = models.BooleanField(default=False)[m
 [m
[32m+[m[32m    protocollo_username = models.CharField('Username', max_length=255)[m
[32m+[m[32m    protocollo_password = models.CharField('Password', max_length=255)[m
     protocollo_aoo = models.CharField('AOO', max_length=12)[m
     protocollo_agd = models.CharField('AGD', max_length=12)[m
     protocollo_uo = models.CharField('UO', max_length=12,)[m
     protocollo_email = models.EmailField('E-mail',[m
                                          max_length=255,[m
                                          blank=True, null=True)[m
[31m-    protocollo_id_uo = models.CharField(_('ID Unità Organizzativa'),[m
[31m-                                      max_length=12)[m
[31m-    protocollo_cod_titolario = models.CharField(_('Codice titolario'),[m
[31m-                                                max_length=12,)[m
[31m-                                                # choices=settings.PROTOCOLLO_CODICI_TITOLARI,[m
[31m-    protocollo_fascicolo_numero = models.CharField(_('Fascicolo numero'),[m
[31m-                                                   max_length=12)[m
[31m-                                                   # default=settings.PROTOCOLLO_FASCICOLO_DEFAULT)[m
[31m-    protocollo_fascicolo_anno = models.IntegerField(_('Fascicolo anno'))[m
[31m-    protocollo_template = models.TextField('XML template',[m
[31m-                                           help_text=_('Template XML che '[m
[31m-                                                      'descrive il flusso'))[m
[32m+[m[32m    # protocollo_template = models.TextField('XML template',[m
[32m+[m[32m                                           # help_text=_('Template XML che '[m
[32m+[m[32m                                                      # 'descrive il flusso'))[m
 [m
     class Meta:[m
[31m-        abstract = True[m
[31m-[m
[31m-[m
[31m-class OrganizationalStructureWSArchiPro(AbstractWSArchiPro):[m
[31m-    organizational_structure = models.ForeignKey(OrganizationalStructure,[m
[31m-                                                 on_delete=models.CASCADE)[m
[32m+[m[32m        ordering = ["-created"][m
[32m+[m[32m        verbose_name = _("Configurazione WSArchiPro Struttura")[m
[32m+[m[32m        verbose_name_plural = _("Configurazioni WSArchiPro Strutture")[m
 [m
     def disable_other_configurations(self):[m
         others = OrganizationalStructureWSArchiPro.objects.filter(organizational_structure=self.organizational_structure).exclude(pk=self.pk)[m
[36m@@ -1209,16 +1239,32 @@[m [mclass OrganizationalStructureWSArchiPro(AbstractWSArchiPro):[m
     @classmethod[m
     def get_active_protocol_configuration(cls, organizational_structure):[m
         conf = cls.objects.filter(organizational_structure=organizational_structure,[m
[31m-                                     is_active=True).first()[m
[32m+[m[32m                                  is_active=True).first()[m
         return conf if conf else False[m
 [m
     def __str__(self):[m
         return '{} - {}'.format(self.name, self.organizational_structure)[m
 [m
 [m
[31m-class TicketCategoryWSArchiPro(AbstractWSArchiPro):[m
[32m+[m[32mclass TicketCategoryWSArchiPro(models.Model):[m
     ticket_category = models.ForeignKey(TicketCategory,[m
                                         on_delete=models.CASCADE)[m
[32m+[m[32m    name = models.CharField(max_length=255)[m
[32m+[m[32m    created = models.DateTimeField(auto_now=True)[m
[32m+[m[32m    modified = models.DateTimeField(auto_now=True)[m
[32m+[m[32m    is_active = models.BooleanField(default=False)[m
[32m+[m[32m    protocollo_cod_titolario = models.CharField(_('Codice titolario'),[m
[32m+[m[32m                                                max_length=12,[m
[32m+[m[32m                                                choices=settings.TITOLARIO_DICT)[m
[32m+[m[32m    protocollo_fascicolo_numero = models.CharField(_('Fascicolo numero'),[m
[32m+[m[32m                                                   max_length=12)[m
[32m+[m[32m                                                   # default=settings.PROTOCOLLO_FASCICOLO_DEFAULT)[m
[32m+[m[32m    protocollo_fascicolo_anno = models.IntegerField(_('Fascicolo anno'))[m
[32m+[m
[32m+[m[32m    class Meta:[m
[32m+[m[32m        ordering = ["-created"][m
[32m+[m[32m        verbose_name = _("Configurazione WSArchiPro Categoria")[m
[32m+[m[32m        verbose_name_plural = _("Configurazioni WSArchiPro Categorie")[m
 [m
     def disable_other_configurations(self):[m
         others = TicketCategoryWSArchiPro.objects.filter(ticket_category=self.ticket_category).exclude(pk=self.pk)[m
[1mdiff --git a/uni_ticket/urls.py b/uni_ticket/urls.py[m
[1mindex 065bb12..34debe8 100644[m
[1m--- a/uni_ticket/urls.py[m
[1m+++ b/uni_ticket/urls.py[m
[36m@@ -212,11 +212,11 @@[m [murlpatterns += [[m
 [m
     # Structure Protocol configurations[m
     path('{}/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_detail, name='manager_structure_protocol_configuration_detail'),[m
[31m-    path('{}/new/'.format(structure_protocol_configurations), manager.structure_protocol_configuration_new, name='manager_structure_protocol_configuration_new'),[m
[31m-    path('{}/delete/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_delete, name='manager_structure_protocol_configuration_delete'),[m
[31m-    path('{}/disable/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_disable, name='manager_structure_protocol_configuration_disable'),[m
[31m-    path('{}/enable/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_enable, name='manager_structure_protocol_configuration_enable'),[m
[31m-    path('{}/test/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_test, name='manager_structure_protocol_configuration_test'),[m
[32m+[m[32m    # path('{}/new/'.format(structure_protocol_configurations), manager.structure_protocol_configuration_new, name='manager_structure_protocol_configuration_new'),[m
[32m+[m[32m    # path('{}/delete/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_delete, name='manager_structure_protocol_configuration_delete'),[m
[32m+[m[32m    # path('{}/disable/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_disable, name='manager_structure_protocol_configuration_disable'),[m
[32m+[m[32m    # path('{}/enable/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_enable, name='manager_structure_protocol_configuration_enable'),[m
[32m+[m[32m    # path('{}/test/'.format(structure_protocol_configuration), manager.structure_protocol_configuration_test, name='manager_structure_protocol_configuration_test'),[m
 [m
     # Category Protocol configurations[m
     path('{}/'.format(category_protocol_configuration), manager.category_protocol_configuration_detail, name='manager_category_protocol_configuration_detail'),[m
[36m@@ -224,7 +224,7 @@[m [murlpatterns += [[m
     path('{}/delete/'.format(category_protocol_configuration), manager.category_protocol_configuration_delete, name='manager_category_protocol_configuration_delete'),[m
     path('{}/disable/'.format(category_protocol_configuration), manager.category_protocol_configuration_disable, name='manager_category_protocol_configuration_disable'),[m
     path('{}/enable/'.format(category_protocol_configuration), manager.category_protocol_configuration_enable, name='manager_category_protocol_configuration_enable'),[m
[31m-    path('{}/test/'.format(category_protocol_configuration), manager.category_protocol_configuration_test, name='manager_category_protocol_configuration_test'),[m
[32m+[m[32m    # path('{}/test/'.format(category_protocol_configuration), manager.category_protocol_configuration_test, name='manager_category_protocol_configuration_test'),[m
 [m
     # Settings[m
     path('{}/settings/'.format(base), manager.manager_settings, name='manager_user_settings'),[m
[1mdiff --git a/uni_ticket/utils.py b/uni_ticket/utils.py[m
[1mindex 9dafa86..e131660 100644[m
[1m--- a/uni_ticket/utils.py[m
[1m+++ b/uni_ticket/utils.py[m
[36m@@ -403,8 +403,11 @@[m [mdef get_text_with_hrefs(text):[m
         new_text = new_text.replace(ele, a_value)[m
     return new_text[m
 [m
[31m-def ticket_protocol(user,[m
[32m+[m[32mdef ticket_protocol(prot_login,[m
[32m+[m[32m                    prot_passw,[m
[32m+[m[32m                    user,[m
                     subject,[m
[32m+[m[32m                    structure_configuration=None,[m
                     configuration=None,[m
                     file_name='test_name',[m
                     response=b'',[m
[36m@@ -412,8 +415,11 @@[m [mdef ticket_protocol(user,[m
                     attachments_dict={},[m
                     test=False):[m
 [m
[32m+[m[32m    valid_conf = structure_configuration and configuration[m
[32m+[m
     # Check only if protocol system works[m
[31m-    if test and not configuration:[m
[32m+[m[32m    # if test and not configuration:[m
[32m+[m[32m    if test:[m
         prot_url = settings.PROT_TEST_URL[m
         prot_login = settings.PROT_TEST_LOGIN[m
         prot_passw = settings.PROT_TEST_PASSW[m
[36m@@ -421,41 +427,43 @@[m [mdef ticket_protocol(user,[m
         prot_agd = settings.PROT_AGD_DEFAULT[m
         prot_uo = settings.PROT_UO_DEFAULT[m
         prot_email = settings.PROT_EMAIL_DEFAULT[m
[31m-        prot_id_uo = settings.PROT_UO_ID_DEFAULT[m
[32m+[m[32m        # prot_id_uo = settings.PROT_UO_ID_DEFAULT[m
         prot_titolario = settings.PROT_TITOLARIO_DEFAULT[m
         prot_fascicolo_num = settings.PROT_FASCICOLO_DEFAULT[m
         prot_fascicolo_anno = settings.PROT_FASCICOLO_ANNO_DEFAULT[m
         prot_template = settings.PROTOCOL_XML[m
     # check my configuration in test environment[m
[31m-    elif test and configuration:[m
[31m-        prot_url = settings.PROT_TEST_URL[m
[31m-        prot_login = settings.PROT_TEST_LOGIN[m
[31m-        prot_passw = settings.PROT_TEST_PASSW[m
[31m-        prot_aoo = configuration.protocollo_aoo[m
[31m-        prot_agd = configuration.protocollo_agd[m
[31m-        prot_uo = configuration.protocollo_uo[m
[31m-        prot_email = configuration.protocollo_email[m
[31m-        prot_id_uo = configuration.protocollo_id_uo[m
[31m-        prot_titolario = configuration.protocollo_cod_titolario[m
[31m-        prot_fascicolo_num = configuration.protocollo_fascicolo_numero[m
[31m-        prot_fascicolo_anno = configuration.protocollo_fascicolo_anno[m
[31m-        prot_template = configuration.protocollo_template[m
[32m+[m[32m    # elif test and configuration:[m
[32m+[m[32m        # prot_url = settings.PROT_TEST_URL[m
[32m+[m[32m        # prot_login = settings.PROT_TEST_LOGIN[m
[32m+[m[32m        # prot_passw = settings.PROT_TEST_PASSW[m
[32m+[m[32m        # prot_aoo = configuration.protocollo_aoo[m
[32m+[m[32m        # prot_agd = configuration.protocollo_agd[m
[32m+[m[32m        # prot_uo = configuration.protocollo_uo[m
[32m+[m[32m        # prot_email = configuration.protocollo_email[m
[32m+[m[32m        # prot_id_uo = configuration.protocollo_id_uo[m
[32m+[m[32m        # prot_titolario = configuration.protocollo_cod_titolario[m
[32m+[m[32m        # prot_fascicolo_num = configuration.protocollo_fascicolo_numero[m
[32m+[m[32m        # prot_fascicolo_anno = configuration.protocollo_fascicolo_anno[m
[32m+[m[32m        # prot_template = configuration.protocollo_template[m
     # for production[m
[31m-    elif not test and configuration:[m
[31m-        prot_url = settings.PROT_URL[m
[31m-        prot_login = settings.PROT_LOGIN[m
[31m-        prot_passw = settings.PROT_PASSW[m
[31m-        prot_aoo = configuration.protocollo_aoo[m
[31m-        prot_agd = configuration.protocollo_agd[m
[31m-        prot_uo = configuration.protocollo_uo[m
[31m-        prot_email = configuration.protocollo_email[m
[31m-        prot_id_uo = configuration.protocollo_id_uo[m
[32m+[m[32m    # elif not test and configuration:[m
[32m+[m[32m    elif not test and valid_conf:[m
[32m+[m[32m        print("PROTOCOLLAZIONE SIMULAZIONE REALE")[m
[32m+[m[32m        prot_url = settings.PROT_TEST_URL[m
[32m+[m[32m        prot_login = prot_login[m
[32m+[m[32m        prot_passw = prot_passw[m
[32m+[m[32m        prot_aoo = structure_configuration.protocollo_aoo[m
[32m+[m[32m        prot_agd = structure_configuration.protocollo_agd[m
[32m+[m[32m        prot_uo = structure_configuration.protocollo_uo[m
[32m+[m[32m        prot_email = structure_configuration.protocollo_email[m
[32m+[m[32m        # prot_id_uo = configuration.protocollo_id_uo[m
         prot_titolario = configuration.protocollo_cod_titolario[m
         prot_fascicolo_num = configuration.protocollo_fascicolo_numero[m
         prot_fascicolo_anno = configuration.protocollo_fascicolo_anno[m
[31m-        prot_template = configuration.protocollo_template[m
[32m+[m[32m        prot_template = settings.PROTOCOL_XML[m
     # for production a custom configuration is necessary[m
[31m-    elif not test and not configuration:[m
[32m+[m[32m    elif not test and not valid_conf:[m
         raise Exception(_('Missing XML configuration for production'))[m
 [m
     protocol_data = {[m
[36m@@ -478,7 +486,7 @@[m [mdef ticket_protocol(user,[m
                      'agd': prot_agd,[m
                      'uo': prot_uo,[m
                      'email': prot_email,[m
[31m-                     'uo_id': prot_id_uo,[m
[32m+[m[32m                     # 'uo_id': prot_id_uo,[m
                      'id_titolario': prot_titolario,[m
                      'fascicolo_numero': prot_fascicolo_num,[m
                      'fascicolo_anno': prot_fascicolo_anno[m
[1mdiff --git a/uni_ticket/views/manager.py b/uni_ticket/views/manager.py[m
[1mindex 3caf49f..fc90711 100644[m
[1m--- a/uni_ticket/views/manager.py[m
[1m+++ b/uni_ticket/views/manager.py[m
[36m@@ -790,11 +790,13 @@[m [mdef category_add_new(request, structure_slug, structure):[m
 [m
                 # check if protocol can be activated[m
                 protocol_required = form.cleaned_data['protocol_required'][m
[31m-                if protocol_required and not OrganizationalStructureWSArchiPro.get_active_protocol_configuration(organizational_structure=structure):[m
[32m+[m[32m                # if protocol_required and not OrganizationalStructureWSArchiPro.get_active_protocol_configuration(organizational_structure=structure):[m
[32m+[m[32m                if protocol_required:[m
                     protocol_required = False[m
                     messages.add_message(request, messages.INFO,[m
[31m-                                         _("Il protocollo non può essere attivato. "[m
[31m-                                           "Nessuna configurazione attiva"))[m
[32m+[m[32m                                         _("Prima di attivare il protocollo "[m
[32m+[m[32m                                           "obbligatorio è necessario "[m
[32m+[m[32m                                           "configurare i parametri"))[m
 [m
                 new_category.protocol_required = protocol_required[m
                 new_category.slug = slug[m
[36m@@ -857,7 +859,8 @@[m [mdef category_edit(request, structure_slug, category_slug, structure):[m
                 protocol_required = False[m
                 messages.add_message(request, messages.INFO,[m
                                      _("Il protocollo non può essere attivato. "[m
[31m-                                       "Nessuna configurazione attiva"))[m
[32m+[m[32m                                       "Controlla la configurazione dei parametri "[m
[32m+[m[32m                                       "della tipologia e della struttura"))[m
 [m
             slug = slugify(name)[m
             slug_name_exist = TicketCategory.objects.filter(Q(name=name) | Q(slug=slug),[m
[36m@@ -1507,21 +1510,21 @@[m [mdef category_input_module_preview(request, structure_slug,[m
         if form.is_valid():[m
 [m
             # Protocol TEST[m
[31m-            if category.protocol_required:[m
[31m-                protocol_configuration = category.get_active_protocol_configuration()[m
[31m-                try:[m
[31m-                    protocol_number = ticket_protocol(configuration=protocol_configuration,[m
[31m-                                                      user=request.user,[m
[31m-                                                      subject=form.cleaned_data['ticket_subject'],[m
[31m-                                                      test=True)[m
[31m-                    messages.add_message(request, messages.SUCCESS,[m
[31m-                                         _("Protocollo di test riuscito: "[m
[31m-                                           "n. <b>{}/{}</b>").format(protocol_number,[m
[31m-                                                                     timezone.now().year))[m
[31m-                except Exception as e:[m
[31m-                    logger.error("Errore Protocollazione: {} - {}".format(request.user, e))[m
[31m-                    messages.add_message(request, messages.ERROR,[m
[31m-                                         _("<b>Errore protocollo</b>: {}").format(e))[m
[32m+[m[32m            # if category.protocol_required:[m
[32m+[m[32m                # protocol_configuration = category.get_active_protocol_configuration()[m
[32m+[m[32m                # try:[m
[32m+[m[32m                    # protocol_number = ticket_protocol(configuration=protocol_configuration,[m
[32m+[m[32m                                                      # user=request.user,[m
[32m+[m[32m                                                      # subject=form.cleaned_data['ticket_subject'],[m
[32m+[m[32m                                                      # test=True)[m
[32m+[m[32m                    # messages.add_message(request, messages.SUCCESS,[m
[32m+[m[32m                                         # _("Protocollo di test riuscito: "[m
[32m+[m[32m                                           # "n. <b>{}/{}</b>").format(protocol_number,[m
[32m+[m[32m                                                                     # timezone.now().year))[m
[32m+[m[32m                # except Exception as e:[m
[32m+[m[32m                    # logger.error("Errore Protocollazione: {} - {}".format(request.user, e))[m
[32m+[m[32m                    # messages.add_message(request, messages.ERROR,[m
[32m+[m[32m                                         # _("<b>Errore protocollo</b>: {}").format(e))[m
             # end Protocol TEST[m
 [m
             messages.add_message(request, messages.SUCCESS,[m
[36m@@ -2467,31 +2470,34 @@[m [mdef structure_protocol_configuration_detail(request, structure_slug,[m
 [m
     :return: response[m
     """[m
[31m-    configuration = OrganizationalStructureWSArchiPro.objects.filter(organizational_structure=structure,[m
[31m-                                                                     pk=configuration_id).first()[m
[32m+[m[32m    configuration = get_object_or_404(OrganizationalStructureWSArchiPro,[m
[32m+[m[32m                                      organizational_structure=structure,[m
[32m+[m[32m                                      pk=configuration_id)[m
[32m+[m
     template = "manager/structure_protocol_configuration.html"[m
     title = _("Configurazione protocollo informatico")[m
 [m
     form = OrganizationalStructureWSArchiProModelForm(instance=configuration)[m
 [m
[31m-    if request.method == 'POST':[m
[31m-        form = OrganizationalStructureWSArchiProModelForm(instance=configuration,[m
[31m-                                                          data=request.POST)[m
[31m-        if form.is_valid():[m
[31m-            configuration = form.save(commit=False)[m
[31m-            if not configuration.protocollo_email:[m
[31m-                configuration.protocollo_email = settings.PROT_EMAIL_DEFAULT[m
[31m-            configuration.save()[m
[31m-[m
[31m-            messages.add_message(request, messages.SUCCESS,[m
[31m-                                 _("Configurazione protocollo informatico aggiornata"))[m
[31m-            return redirect('uni_ticket:manager_structure_protocol_configuration_detail',[m
[31m-                            structure_slug=structure_slug,[m
[31m-                            configuration_id=configuration.pk)[m
[31m-        else:[m
[31m-            for k,v in get_labeled_errors(form).items():[m
[31m-                messages.add_message(request, messages.ERROR,[m
[31m-                                     "<b>{}</b>: {}".format(k, strip_tags(v)))[m
[32m+[m[32m    # POST ACTION DISABLED[m
[32m+[m[32m    # if request.method == 'POST':[m
[32m+[m[32m        # form = OrganizationalStructureWSArchiProModelForm(instance=configuration,[m
[32m+[m[32m                                                          # data=request.POST)[m
[32m+[m[32m        # if form.is_valid():[m
[32m+[m[32m            # configuration = form.save(commit=False)[m
[32m+[m[32m            # if not configuration.protocollo_email:[m
[32m+[m[32m                # configuration.protocollo_email = settings.PROT_EMAIL_DEFAULT[m
[32m+[m[32m            # configuration.save()[m
[32m+[m
[32m+[m[32m            # messages.add_message(request, messages.SUCCESS,[m
[32m+[m[32m                                 # _("Configurazione protocollo informatico aggiornata"))[m
[32m+[m[32m            # return redirect('uni_ticket:manager_structure_protocol_configuration_detail',[m
[32m+[m[32m                            # structure_slug=structure_slug,[m
[32m+[m[32m                            # configuration_id=configuration.pk)[m
[32m+[m[32m        # else:[m
[32m+[m[32m            # for k,v in get_labeled_errors(form).items():[m
[32m+[m[32m                # messages.add_message(request, messages.ERROR,[m
[32m+[m[32m                                     # "<b>{}</b>: {}".format(k, strip_tags(v)))[m
     d = {'configuration': configuration,[m
          'form': form,[m
          'structure': structure,[m
[36m@@ -2694,39 +2700,39 @@[m [mdef structure_protocol_configuration_enable(request, structure_slug,[m
                     structure_slug=structure_slug)[m
 [m
 [m
[31m-@login_required[m
[31m-@is_manager[m
[31m-def structure_protocol_configuration_test(request, structure_slug,[m
[31m-                                          configuration_id, structure):[m
[31m-    """[m
[31m-    Structure protocol configuration test[m
[31m-[m
[31m-    :type structure_slug: String[m
[31m-    :type configuration_id: Integer[m
[31m-    :type structure: OrganizationalStructure (from @is_manager)[m
[31m-[m
[31m-    :param structure_slug: structure slug[m
[31m-    :param configuration_id: protocol configuration pk[m
[31m-    :param structure: structure object (from @is_manager/@is_operator)[m
[31m-[m
[31m-    :return: response[m
[31m-    """[m
[31m-    configuration = OrganizationalStructureWSArchiPro.objects.filter(organizational_structure=structure,[m
[31m-                                                                     pk=configuration_id).first()[m
[31m-    try:[m
[31m-        protocol_number = ticket_protocol(configuration=configuration,[m
[31m-                                          user=request.user,[m
[31m-                                          subject='test {}'.format(request.user),[m
[31m-                                          test=True)[m
[31m-        messages.add_message(request, messages.SUCCESS,[m
[31m-                             _("Complimenti! Configurazione valida."))[m
[31m-    except Exception as e:[m
[31m-        logger.error("Errore Protocollazione: {} - {}".format(request.user, e))[m
[31m-        messages.add_message(request, messages.ERROR,[m
[31m-                             _("<b>Errore protocollo</b>: {}").format(e))[m
[31m-    return redirect('uni_ticket:manager_structure_protocol_configuration_detail',[m
[31m-                    structure_slug=structure_slug,[m
[31m-                    configuration_id=configuration.pk)[m
[32m+[m[32m# @login_required[m
[32m+[m[32m# @is_manager[m
[32m+[m[32m# def structure_protocol_configuration_test(request, structure_slug,[m
[32m+[m[32m                                          # configuration_id, structure):[m
[32m+[m[32m    # """[m
[32m+[m[32m    # Structure protocol configuration test[m
[32m+[m
[32m+[m[32m    # :type structure_slug: String[m
[32m+[m[32m    # :type configuration_id: Integer[m
[32m+[m[32m    # :type structure: OrganizationalStructure (from @is_manager)[m
[32m+[m
[32m+[m[32m    # :param structure_slug: structure slug[m
[32m+[m[32m    # :param configuration_id: protocol configuration pk[m
[32m+[m[32m    # :param structure: structure object (from @is_manager/@is_operator)[m
[32m+[m
[32m+[m[32m    # :return: response[m
[32m+[m[32m    # """[m
[32m+[m[32m    # configuration = OrganizationalStructureWSArchiPro.objects.filter(organizational_structure=structure,[m
[32m+[m[32m                                                                     # pk=configuration_id).first()[m
[32m+[m[32m    # try:[m
[32m+[m[32m        # protocol_number = ticket_protocol(configuration=configuration,[m
[32m+[m[32m                                          # user=request.user,[m
[32m+[m[32m                                          # subject='test {}'.format(request.user),[m
[32m+[m[32m                                          # test=True)[m
[32m+[m[32m        # messages.add_message(request, messages.SUCCESS,[m
[32m+[m[32m                             # _("Complimenti! Configurazione valida."))[m
[32m+[m[32m    # except Exception as e:[m
[32m+[m[32m        # logger.error("Errore Protocollazione: {} - {}".format(request.user, e))[m
[32m+[m[32m        # messages.add_message(request, messages.ERROR,[m
[32m+[m[32m                             # _("<b>Errore protocollo</b>: {}").format(e))[m
[32m+[m[32m    # return redirect('uni_ticket:manager_structure_protocol_configuration_detail',[m
[32m+[m[32m                    # structure_slug=structure_slug,[m
[32m+[m[32m                    # configuration_id=configuration.pk)[m
 [m
 @login_required[m
 @is_manager[m
[36m@@ -2763,9 +2769,15 @@[m [mdef category_protocol_configuration_detail(request, structure_slug,[m
         form = TicketCategoryWSArchiProModelForm(instance=configuration,[m
                                                  data=request.POST)[m
         if form.is_valid():[m
[31m-            configuration = form.save(commit=False)[m
[31m-            if not configuration.protocollo_email:[m
[31m-                configuration.protocollo_email = settings.PROT_EMAIL_DEFAULT[m
[32m+[m[32m            configuration.name = form.cleaned_data['name'][m
[32m+[m[32m            configuration.protocollo_cod_titolario = form.cleaned_data['protocollo_cod_titolario'][m
[32m+[m[32m            configuration.protocollo_fascicolo_numero = form.cleaned_data['protocollo_fascicolo_numero'][m
[32m+[m[32m            configuration.protocollo_fascicolo_anno = form.cleaned_data['protocollo_fascicolo_anno'][m
[32m+[m[32m            configuration.save(update_fields=['name',[m
[32m+[m[32m                                              'modified',[m
[32m+[m[32m                                              'protocollo_cod_titolario',[m
[32m+[m[32m                                              'protocollo_fascicolo_numero',[m
[32m+[m[32m                                              'protocollo_fascicolo_anno'])[m
 [m
             messages.add_message(request, messages.SUCCESS,[m
                                  _("Configurazione protocollo informatico aggiornata"))[m
[36m@@ -2810,27 +2822,28 @@[m [mdef category_protocol_configuration_new(request, structure_slug,[m
     structure_protocol = OrganizationalStructureWSArchiPro.objects.filter(organizational_structure=structure,[m
                                                                           is_active=True).first()[m
 [m
[31m-    if structure_protocol:[m
[31m-        initial_data = {'protocollo_aoo': structure_protocol.protocollo_aoo,[m
[31m-                        'protocollo_agd': structure_protocol.protocollo_agd,[m
[31m-                        'protocollo_uo': structure_protocol.protocollo_uo,[m
[31m-                        'protocollo_email': structure_protocol.protocollo_email,[m
[31m-                        'protocollo_id_uo': structure_protocol.protocollo_id_uo,[m
[31m-                        'protocollo_cod_titolario': structure_protocol.protocollo_cod_titolario,[m
[31m-                        'protocollo_fascicolo_numero': structure_protocol.protocollo_fascicolo_numero,[m
[31m-                        'protocollo_fascicolo_anno': structure_protocol.protocollo_fascicolo_anno,[m
[31m-                        'protocollo_template': structure_protocol.protocollo_template}[m
[31m-    else:[m
[31m-        initial_data = {'protocollo_template': settings.PROTOCOL_XML}[m
[31m-[m
[31m-    form = TicketCategoryWSArchiProModelForm(initial_data)[m
[32m+[m[32m    # if structure_protocol:[m
[32m+[m[32m        # initial_data = {'protocollo_aoo': structure_protocol.protocollo_aoo,[m
[32m+[m[32m                        # 'protocollo_agd': structure_protocol.protocollo_agd,[m
[32m+[m[32m                        # 'protocollo_uo': structure_protocol.protocollo_uo,[m
[32m+[m[32m                        # 'protocollo_email': structure_protocol.protocollo_email,[m
[32m+[m[32m                        # 'protocollo_id_uo': structure_protocol.protocollo_id_uo,[m
[32m+[m[32m                        # 'protocollo_cod_titolario': structure_protocol.protocollo_cod_titolario,[m
[32m+[m[32m                        # 'protocollo_fascicolo_numero': structure_protocol.protocollo_fascicolo_numero,[m
[32m+[m[32m                        # 'protocollo_fascicolo_anno': structure_protocol.protocollo_fascicolo_anno,[m
[32m+[m[32m                        # 'protocollo_template': structure_protocol.protocollo_template}[m
[32m+[m[32m    # else:[m
[32m+[m[32m        # initial_data = {'protocollo_template': settings.PROTOCOL_XML}[m
[32m+[m
[32m+[m[32m    # form = TicketCategoryWSArchiProModelForm(initial_data)[m
[32m+[m[32m    form = TicketCategoryWSArchiProModelForm()[m
 [m
     if request.method == 'POST':[m
         form = TicketCategoryWSArchiProModelForm(data=request.POST)[m
         if form.is_valid():[m
             configuration = form.save(commit=False)[m
[31m-            if not configuration.protocollo_email:[m
[31m-                configuration.protocollo_email = settings.PROT_EMAIL_DEFAULT[m
[32m+[m[32m            # if not configuration.protocollo_email:[m
[32m+[m[32m                # configuration.protocollo_email = settings.PROT_EMAIL_DEFAULT[m
             configuration.ticket_category=category[m
             configuration.save()[m
 [m
[36m@@ -2996,11 +3009,13 @@[m [mdef category_protocol_configuration_enable(request, structure_slug,[m
                                  slug=category_slug)[m
     configuration = TicketCategoryWSArchiPro.objects.filter(ticket_category=category,[m
                                                             pk=configuration_id).first()[m
[32m+[m
     if configuration.is_active:[m
         messages.add_message(request,[m
                              messages.ERROR,[m
                              _("Configurazione {} già attivata"[m
                                "").format(configuration))[m
[32m+[m
     else:[m
         configuration.is_active = True[m
         configuration.save(update_fields = ['is_active', 'modified'])[m
[36m@@ -3025,46 +3040,46 @@[m [mdef category_protocol_configuration_enable(request, structure_slug,[m
                     structure_slug=structure_slug,[m
                     category_slug=category_slug)[m
 [m
[31m-@login_required[m
[31m-@is_manager[m
[31m-def category_protocol_configuration_test(request, structure_slug,[m
[31m-                                         category_slug,[m
[31m-                                         configuration_id, structure):[m
[31m-    """[m
[31m-    Test a category protocol configuration[m
[31m-[m
[31m-    :type structure_slug: String[m
[31m-    :type category_slug: String[m
[31m-    :type configuration_id: Integer[m
[31m-    :type structure: OrganizationalStructure (from @is_manager)[m
[31m-[m
[31m-    :param structure_slug: structure slug[m
[31m-    :param category_slug: category slug[m
[31m-    :param configuration_id: protocol configuration pk[m
[31m-    :param structure: structure object (from @is_manager/@is_operator)[m
[31m-[m
[31m-    :return: redirect[m
[31m-    """[m
[31m-    category = get_object_or_404(TicketCategory,[m
[31m-                                 organizational_structure=structure,[m
[31m-                                 slug=category_slug)[m
[31m-    configuration = TicketCategoryWSArchiPro.objects.filter(ticket_category=category,[m
[31m-                                                            pk=configuration_id).first()[m
[31m-    try:[m
[31m-        protocol_number = ticket_protocol(configuration=configuration,[m
[31m-                                          user=request.user,[m
[31m-                                          subject='test {}'.format(request.user),[m
[31m-                                          test=True)[m
[31m-        messages.add_message(request, messages.SUCCESS,[m
[31m-                             _("Complimenti! Configurazione valida."))[m
[31m-    except Exception as e:[m
[31m-        logger.error("Errore Protocollazione: {} - {}".format(request.user, e))[m
[31m-        messages.add_message(request, messages.ERROR,[m
[31m-                             _("<b>Errore protocollo</b>: {}").format(e))[m
[31m-    return redirect('uni_ticket:manager_category_protocol_configuration_detail',[m
[31m-                    structure_slug=structure_slug,[m
[31m-                    category_slug=category_slug,[m
[31m-                    configuration_id=configuration.pk)[m
[32m+[m[32m# @login_required[m
[32m+[m[32m# @is_manager[m
[32m+[m[32m# def category_protocol_configuration_test(request, structure_slug,[m
[32m+[m[32m                                         # category_slug,[m
[32m+[m[32m                                         # configuration_id, structure):[m
[32m+[m[32m    # """[m
[32m+[m[32m    # Test a category protocol configuration[m
[32m+[m
[32m+[m[32m    # :type structure_slug: String[m
[32m+[m[32m    # :type category_slug: String[m
[32m+[m[32m    # :type configuration_id: Integer[m
[32m+[m[32m    # :type structure: OrganizationalStructure (from @is_manager)[m
[32m+[m
[32m+[m[32m    # :param structure_slug: structure slug[m
[32m+[m[32m    # :param category_slug: category slug[m
[32m+[m[32m    # :param configuration_id: protocol configuration pk[m
[32m+[m[32m    # :param structure: structure object (from @is_manager/@is_operator)[m
[32m+[m
[32m+[m[32m    # :return: redirect[m
[32m+[m[32m    # """[m
[32m+[m[32m    # category = get_object_or_404(TicketCategory,[m
[32m+[m[32m                                 # organizational_structure=structure,[m
[32m+[m[32m                                 # slug=category_slug)[m
[32m+[m[32m    # configuration = TicketCategoryWSArchiPro.objects.filter(ticket_category=category,[m
[32m+[m[32m                                                            # pk=configuration_id).first()[m
[32m+[m[32m    # try:[m
[32m+[m[32m        # protocol_number = ticket_protocol(configuration=configuration,[m
[32m+[m[32m                                          # user=request.user,[m
[32m+[m[32m                                          # subject='test {}'.format(request.user),[m
[32m+[m[32m                                          # test=True)[m
[32m+[m[32m        # messages.add_message(request, messages.SUCCESS,[m
[32m+[m[32m                             # _("Complimenti! Configurazione valida."))[m
[32m+[m[32m    # except Exception as e:[m
[32m+[m[32m        # logger.error("Errore Protocollazione: {} - {}".format(request.user, e))[m
[32m+[m[32m        # messages.add_message(request, messages.ERROR,[m
[32m+[m[32m                             # _("<b>Errore protocollo</b>: {}").format(e))[m
[32m+[m[32m    # return redirect('uni_ticket:manager_category_protocol_configuration_detail',[m
[32m+[m[32m                    # structure_slug=structure_slug,[m
[32m+[m[32m                    # category_slug=category_slug,[m
[32m+[m[32m                    # configuration_id=configuration.pk)[m
 [m
 @login_required[m
 @is_manager[m
[1mdiff --git a/uni_ticket/views/user.py b/uni_ticket/views/user.py[m
[1mindex 296428a..ad568d3 100644[m
[1m--- a/uni_ticket/views/user.py[m
[1m+++ b/uni_ticket/views/user.py[m
[36m@@ -490,12 +490,16 @@[m [mdef ticket_add_new(request, structure_slug, category_slug):[m
                 # Protocol[m
                 if category.protocol_required:[m
                     try:[m
[32m+[m[32m                        protocol_struct_configuration = category.get_active_structure_protocolo_configuration()[m
                         protocol_configuration = category.get_active_protocol_configuration()[m
 [m
                         response = download_ticket_pdf(request=request,[m
                                                        ticket_id=ticket.code).content[m
 [m
[31m-                        protocol_number = ticket_protocol(configuration=protocol_configuration,[m
[32m+[m[32m                        protocol_number = ticket_protocol(prot_login=protocol_struct_configuration.protocollo_username,[m
[32m+[m[32m                                                          prot_passw=protocol_struct_configuration.protocollo_password,[m
[32m+[m[32m                                                          structure_configuration=protocol_struct_configuration,[m
[32m+[m[32m                                                          configuration=protocol_configuration,[m
                                                           user=current_user,[m
                                                           subject=ticket.subject,[m
                                                           file_name=ticket.code,[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/category_detail.html b/uni_ticket_bootstrap_italia_template/templates/manager/category_detail.html[m
[1mindex db39c06..9edacf0 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/category_detail.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/category_detail.html[m
[36m@@ -304,7 +304,9 @@[m
                             {% endfor %}[m
                         </ul>[m
                     {% else %}[m
[31m-                    -[m
[32m+[m[32m                    <svg class="icon icon-sm icon-secondary">[m
[32m+[m[32m                        <use xlink:href="{% static 'svg/sprite.svg' %}#it-minus"></use>[m
[32m+[m[32m                    </svg>[m
                     {% endif %}[m
                 </td>[m
             </tr>[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/category_input_module_preview.html b/uni_ticket_bootstrap_italia_template/templates/manager/category_input_module_preview.html[m
[1mindex 47f812a..7f87402 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/category_input_module_preview.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/category_input_module_preview.html[m
[36m@@ -14,11 +14,7 @@[m
         <svg class="icon icon-xs icon-white">[m
             <use xlink:href="{% static 'svg/sprite.svg' %}#it-check"></use>[m
         </svg>[m
[31m-        {% if categoria.protocol_required %}[m
[31m-            {% trans "Simula invio e protocollo della richiesta" %}[m
[31m-        {% else %}[m
[31m-            {% trans "Simula invio richiesta" %}[m
[31m-        {% endif %}[m
[32m+[m[32m        {% trans "Simula invio richiesta" %}[m
     </button>[m
 </div>[m
 {% endblock %}[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_detail.html b/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_detail.html[m
[1mindex 254e1b4..183c5f9 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_detail.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_detail.html[m
[36m@@ -21,12 +21,14 @@[m
     </svg> {% trans "Torna alla tipologia di richiesta" %}[m
 </a>[m
 [m
[32m+[m[32m{% comment %}[m
 <a role="button" class="btn btn-outline-success"[m
    href="{% url 'uni_ticket:manager_category_protocol_configuration_test' structure_slug=structure.slug category_slug=category.slug configuration_id=configuration.pk %}">[m
     <svg class="icon icon-xs icon-success">[m
         <use xlink:href="{% static 'svg/sprite.svg' %}#it-check-circle"></use>[m
     </svg> {% trans "Verifica" %}[m
 </a>[m
[32m+[m[32m{% endcomment %}[m
 [m
 {% if configuration.is_active %}[m
 <button type="button"[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_new.html b/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_new.html[m
[1mindex 4e452c7..a8cbe59 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_new.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configuration_new.html[m
[36m@@ -31,11 +31,10 @@[m
             {% trans "Eventuali <b>parametri errati</b> comporteranno un <b>errore in fase di protocollazione</b>" %}[m
             {% trans " e la conseguente interruzione del processo di generazione della richiesta." %}[m
             <br>[m
[31m-            {% trans "Di default, i dati vengono ereditati dalla " %}[m
[32m+[m[32m            {% trans "La configurazione del protocollo della struttura, se presente, è disponibile " %}[m
             <a href="{% url 'uni_ticket:manager_user_settings' structure_slug=structure.slug %}">[m
[31m-                <b>{% trans "configurazione del protcollo della struttura," %}</b>[m
[32m+[m[32m                <b>{% trans "qui" %}</b>.[m
             </a>[m
[31m-            {% trans " se presente, o dalla configurazione globale del sistema." %}[m
         </div>[m
         <div class="card-space card-wrapper">[m
             <div class="card card-bg no-after">[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configurations.html b/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configurations.html[m
[1mindex 2c6b570..59d1acc 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configurations.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/category_protocol_configurations.html[m
[36m@@ -138,9 +138,6 @@[m
         {% endfor %}[m
     </ul>[m
     {% else %}[m
[31m-    {% trans "Nessuna configurazione attiva. Sarà usata, se presente, " %}[m
[31m-    <a href="{% url 'uni_ticket:manager_user_settings' structure_slug=structure.slug %}">[m
[31m-        <b>{% trans "quella della struttura" %}</b>[m
[31m-    </a>[m
[32m+[m[32m    {% trans "Nessuna configurazione attiva." %}[m
     {% endif %}[m
 </div>[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/structure_protocol_configuration.html b/uni_ticket_bootstrap_italia_template/templates/manager/structure_protocol_configuration.html[m
[1mindex 7211b14..6fbcdcd 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/structure_protocol_configuration.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/structure_protocol_configuration.html[m
[36m@@ -21,6 +21,8 @@[m
     </svg> {% trans "Torna alla gestione parametri" %}[m
 </a>[m
 [m
[32m+[m[32m{% comment %}[m
[32m+[m[32mUSER ACTIONS DISABLED![m
 <a role="button" class="btn btn-outline-success"[m
    href="{% url 'uni_ticket:manager_structure_protocol_configuration_test' structure_slug=structure.slug configuration_id=configuration.pk %}">[m
     <svg class="icon icon-xs icon-success">[m
[36m@@ -55,8 +57,10 @@[m
             <use xlink:href="{% static 'svg/sprite.svg' %}#it-close-circle"></use>[m
         </svg> {% trans "Elimina" %}[m
 </button>[m
[32m+[m[32m{% endcomment %}[m
 {% endblock top_buttons %}[m
 [m
[32m+[m[32m{% comment %}[m
 {% block clean_content %}[m
 <div class="row">[m
     <div class="col">[m
[36m@@ -202,3 +206,4 @@[m
     </div>[m
 </div>[m
 {% endblock clean_content %}[m
[32m+[m[32m{% endcomment %}[m
[1mdiff --git a/uni_ticket_bootstrap_italia_template/templates/manager/user_settings.html b/uni_ticket_bootstrap_italia_template/templates/manager/user_settings.html[m
[1mindex b814701..eaf56a6 100644[m
[1m--- a/uni_ticket_bootstrap_italia_template/templates/manager/user_settings.html[m
[1m+++ b/uni_ticket_bootstrap_italia_template/templates/manager/user_settings.html[m
[36m@@ -43,9 +43,11 @@[m
                     <div class="card-wrapper card-space pb-3">[m
                         <div class="card card-bg no-after">[m
                             <div class="card-body">[m
[31m-                                {% trans "Qui puoi definire <b>flussi personalizzati</b> di protocollo per le pratiche della struttura." %}[m
[32m+[m[32m                                {% trans "Qui sono definiti i <b>parametri di configurazione</b> di protocollo della struttura." %}[m
[32m+[m[32m                                {% comment %}[m
                                 <br>[m
                                 {% trans "La configurazione attiva sarà ereditata da ogni tipologia di richiesta." %}[m
[32m+[m[32m                                {% endcomment %}[m
                                 <hr>[m
                                 {% trans "E' anche possibile eseguire un <b>test</b> per verificare che il <b>sistema di protocollo</b> funzioni correttamente." %}[m
                                 <br>[m
[36m@@ -62,158 +64,164 @@[m
                     </div>[m
                 </div>[m
             </div>[m
[32m+[m[32m            {% if protocol_configurations %}[m
             <div class="row">[m
                 <div class="col">[m
                     <div class="card-space card-wrapper">[m
                         <div class="card card-bg no-after">[m
                             <div class="card-body">[m
[31m-                                {% if protocol_configurations %}[m
[31m-                                    <div class="table-responsive">[m
[31m-                                        <table class="table table-striped table-hover">[m
[31m-                                            <thead>[m
[31m-                                                <tr role="row">[m
[31m-                                                    <th>{% trans "Denominazione" %}</th>[m
[31m-                                                    <th>{% trans "Creata il" %}</th>[m
[31m-                                                    <th>{% trans "Modificata il" %}</th>[m
[31m-                                                    <th>{% trans "Stato" %}</th>[m
[31m-                                                    <th></th>[m
[31m-                                                </tr>[m
[31m-                                            </thead>[m
[31m-                                            <tbody>[m
[31m-                                                {% for conf in protocol_configurations %}[m
[31m-                                                <tr>[m
[31m-                                                    <td>[m
[31m-                                                        <a href="{% url 'uni_ticket:manager_structure_protocol_configuration_detail' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[31m-                                                            {{ conf.name }}[m
[31m-                                                        </a>[m
[31m-                                                    </td>[m
[31m-                                                    <td>{{ conf.created }}</td>[m
[31m-                                                    <td>{{ conf.modified }}</td>[m
[31m-                                                    <td>[m
[31m-                                                        {% if conf.is_active %}[m
[31m-                                                        <span class="badge badge-success mb-2">[m
[31m-                                                            {% trans "Attiva" %}[m
[31m-                                                        </span>[m
[31m-                                                        {% else %}[m
[31m-                                                        <span class="badge badge-danger mb-2">[m
[31m-                                                            {% trans "Non attiva" %}[m
[31m-                                                        </span>[m
[31m-                                                        {% endif %}[m
[31m-                                                    </td>[m
[31m-                                                    <td>[m
[31m-                                                        <button type="button"[m
[31m-                                                                class="mx-1 btn btn-outline-danger btn-xs float-right"[m
[31m-                                                                data-toggle="modal"[m
[31m-                                                                data-target="#deleteConfiguration{{ forloop.counter0 }}">[m
[31m-                                                            {% trans "Elimina" %}[m
[31m-                                                        </button>[m
[31m-[m
[31m-                                                        {% if conf.is_active %}[m
[31m-                                                        <button type="button"[m
[31m-                                                            class="mx-1 btn btn-outline-secondary btn-xs float-right"[m
[31m-                                                            data-toggle="modal"[m
[31m-                                                            data-target="#disableConfiguration{{ forloop.counter0 }}">[m
[31m-                                                            {% trans "Disattiva" %}[m
[31m-                                                        </button>[m
[31m-                                                        {% else %}[m
[31m-                                                        <button type="button"[m
[31m-                                                            class="mx-1 btn btn-outline-success btn-xs float-right"[m
[32m+[m[32m                                <div class="table-responsive">[m
[32m+[m[32m                                    <table class="table table-striped table-hover">[m
[32m+[m[32m                                        <thead>[m
[32m+[m[32m                                            <tr role="row">[m
[32m+[m[32m                                                <th>{% trans "Denominazione" %}</th>[m
[32m+[m[32m                                                <th>{% trans "Creata il" %}</th>[m
[32m+[m[32m                                                <th>{% trans "Modificata il" %}</th>[m
[32m+[m[32m                                                <th>{% trans "Stato" %}</th>[m
[32m+[m[32m                                                {% comment %}[m
[32m+[m[32m                                                <th></th>[m
[32m+[m[32m                                                {% endcomment %}[m
[32m+[m[32m                                            </tr>[m
[32m+[m[32m                                        </thead>[m
[32m+[m[32m                                        <tbody>[m
[32m+[m[32m                                            {% for conf in protocol_configurations %}[m
[32m+[m[32m                                            <tr>[m
[32m+[m[32m                                                <td>[m
[32m+[m[32m                                                    <a href="{% url 'uni_ticket:manager_structure_protocol_configuration_detail' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[32m+[m[32m                                                        {{ conf.name }}[m
[32m+[m[32m                                                    </a>[m
[32m+[m[32m                                                </td>[m
[32m+[m[32m                                                <td>{{ conf.created }}</td>[m
[32m+[m[32m                                                <td>{{ conf.modified }}</td>[m
[32m+[m[32m                                                <td>[m
[32m+[m[32m                                                    {% if conf.is_active %}[m
[32m+[m[32m                                                    <span class="badge badge-success mb-2">[m
[32m+[m[32m                                                        {% trans "Attiva" %}[m
[32m+[m[32m                                                    </span>[m
[32m+[m[32m                                                    {% else %}[m
[32m+[m[32m                                                    <span class="badge badge-danger mb-2">[m
[32m+[m[32m                                                        {% trans "Non attiva" %}[m
[32m+[m[32m                                                    </span>[m
[32m+[m[32m                                                    {% endif %}[m
[32m+[m[32m                                                </td>[m
[32m+[m[32m                                                {% comment %}[m
[32m+[m[32m                                                <td>[m
[32m+[m[32m                                                    <button type="button"[m
[32m+[m[32m                                                            class="mx-1 btn btn-outline-danger btn-xs float-right"[m
                                                             data-toggle="modal"[m
[31m-                                                            data-target="#enableConfiguration{{ forloop.counter0 }}">[m
[31m-                                                            {% trans "Attiva" %}[m
[31m-                                                        </button>[m
[31m-                                                        {% endif %}[m
[31m-                                                    </td>[m
[31m-                                                </tr>[m
[31m-                                                <div class="modal fade" tabindex="-1" role="dialog" id="enableConfiguration{{ forloop.counter0 }}">[m
[31m-                                                    <div class="modal-dialog modal-dialog-centered" role="document">[m
[31m-                                                        <div class="modal-content">[m
[31m-                                                            <div class="modal-header">[m
[31m-                                                                <h5 class="modal-title">[m
[31m-                                                                    {% trans "Attivazione configurazione" %}[m
[31m-                                                                </h5>[m
[31m-                                                                <button class="close" type="button"[m
[31m-                                                                        data-dismiss="modal" aria-label="Close">[m
[31m-                                                                   <svg class="icon">[m
[31m-                                                                      <use xlink:href="{% static 'svg/sprite.svg' %}#it-close"></use>[m
[31m-                                                                   </svg>[m
[31m-                                                                </button>[m
[31m-                                                            </div>[m
[31m-                                                            <div class="modal-body">[m
[31m-                                                                <p>{% trans "Vuoi davvero attivare la configurazione " %}[m
[31m-                                                                   <b>{{ conf }}</b> ?[m
[31m-                                                                </p>[m
[31m-                                                            </div>[m
[31m-                                                            <div class="modal-footer">[m
[31m-                                                                <a role="button" class="btn btn-success"[m
[31m-                                                                   href="{% url 'uni_ticket:manager_structure_protocol_configuration_enable' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[31m-                                                                    {% trans "Si, attiva la configurazione" %}[m
[31m-                                                                </a>[m
[31m-                                                            </div>[m
[32m+[m[32m                                                            data-target="#deleteConfiguration{{ forloop.counter0 }}">[m
[32m+[m[32m                                                        {% trans "Elimina" %}[m
[32m+[m[32m                                                    </button>[m
[32m+[m
[32m+[m[32m                                                    {% if conf.is_active %}[m
[32m+[m[32m                                                    <button type="button"[m
[32m+[m[32m                                                        class="mx-1 btn btn-outline-secondary btn-xs float-right"[m
[32m+[m[32m                                                        data-toggle="modal"[m
[32m+[m[32m                                                        data-target="#disableConfiguration{{ forloop.counter0 }}">[m
[32m+[m[32m                                                        {% trans "Disattiva" %}[m
[32m+[m[32m                                                    </button>[m
[32m+[m[32m                                                    {% else %}[m
[32m+[m[32m                                                    <button type="button"[m
[32m+[m[32m                                                        class="mx-1 btn btn-outline-success btn-xs float-right"[m
[32m+[m[32m                                                        data-toggle="modal"[m
[32m+[m[32m                                                        data-target="#enableConfiguration{{ forloop.counter0 }}">[m
[32m+[m[32m                                                        {% trans "Attiva" %}[m
[32m+[m[32m                                                    </button>[m
[32m+[m[32m                                                    {% endif %}[m
[32m+[m[32m                                                </td>[m
[32m+[m[32m                                                {% endcomment %}[m
[32m+[m[32m                                            </tr>[m
[32m+[m[32m                                            {% comment %}[m
[32m+[m[32m                                            <div class="modal fade" tabindex="-1" role="dialog" id="enableConfiguration{{ forloop.counter0 }}">[m
[32m+[m[32m                                                <div class="modal-dialog modal-dialog-centered" role="document">[m
[32m+[m[32m                                                    <div class="modal-content">[m
[32m+[m[32m                                                        <div class="modal-header">[m
[32m+[m[32m                                                            <h5 class="modal-title">[m
[32m+[m[32m                                                                {% trans "Attivazione configurazione" %}[m
[32m+[m[32m                                                            </h5>[m
[32m+[m[32m                                                            <button class="close" type="button"[m
[32m+[m[32m                                                                    data-dismiss="modal" aria-label="Close">[m
[32m+[m[32m                                                               <svg class="icon">[m
[32m+[m[32m                                                                  <use xlink:href="{% static 'svg/sprite.svg' %}#it-close"></use>[m
[32m+[m[32m                                                               </svg>[m
[32m+[m[32m                                                            </button>[m
[32m+[m[32m                                                        </div>[m
[32m+[m[32m                                                        <div class="modal-body">[m
[32m+[m[32m                                                            <p>{% trans "Vuoi davvero attivare la configurazione " %}[m
[32m+[m[32m                                                               <b>{{ conf }}</b> ?[m
[32m+[m[32m                                                            </p>[m
[32m+[m[32m                                                        </div>[m
[32m+[m[32m                                                        <div class="modal-footer">[m
[32m+[m[32m                                                            <a role="button" class="btn btn-success"[m
[32m+[m[32m                                                               href="{% url 'uni_ticket:manager_structure_protocol_configuration_enable' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[32m+[m[32m                                                                {% trans "Si, attiva la configurazione" %}[m
[32m+[m[32m                                                            </a>[m
                                                         </div>[m
                                                     </div>[m
                                                 </div>[m
[31m-                                                <div class="modal fade" tabindex="-1" role="dialog" id="disableConfiguration{{ forloop.counter0 }}">[m
[31m-                                                    <div class="modal-dialog modal-dialog-centered" role="document">[m
[31m-                                                        <div class="modal-content">[m
[31m-                                                            <div class="modal-header">[m
[31m-                                                                <h5 class="modal-title">[m
[31m-                                                                    {% trans "Disattivazione configurazione" %}[m
[31m-                                                                </h5>[m
[31m-                                                                <button class="close" type="button"[m
[31m-                                                                        data-dismiss="modal" aria-label="Close">[m
[31m-                                                                   <svg class="icon">[m
[31m-                                                                      <use xlink:href="{% static 'svg/sprite.svg' %}#it-close"></use>[m
[31m-                                                                   </svg>[m
[31m-                                                                </button>[m
[31m-                                                            </div>[m
[31m-                                                            <div class="modal-body">[m
[31m-                                                                <p>{% trans "Vuoi davvero disattivare la configurazione " %}[m
[31m-                                                                   <b>{{ conf }}</b> ?[m
[31m-                                                                </p>[m
[31m-                                                            </div>[m
[31m-                                                            <div class="modal-footer">[m
[31m-                                                                <a role="button" class="btn btn-danger"[m
[31m-                                                                   href="{% url 'uni_ticket:manager_structure_protocol_configuration_disable' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[31m-                                                                    {% trans "Si, disattiva la configurazione" %}[m
[31m-                                                                </a>[m
[31m-                                                            </div>[m
[32m+[m[32m                                            </div>[m
[32m+[m[32m                                            <div class="modal fade" tabindex="-1" role="dialog" id="disableConfiguration{{ forloop.counter0 }}">[m
[32m+[m[32m                                                <div class="modal-dialog modal-dialog-centered" role="document">[m
[32m+[m[32m                                                    <div class="modal-content">[m
[32m+[m[32m                                                        <div class="modal-header">[m
[32m+[m[32m                                                            <h5 class="modal-title">[m
[32m+[m[32m                                                                {% trans "Disattivazione configurazione" %}[m
[32m+[m[32m                                                            </h5>[m
[32m+[m[32m                                                            <button class="close" type="button"[m
[32m+[m[32m                                                                    data-dismiss="modal" aria-label="Close">[m
[32m+[m[32m                                                               <svg class="icon">[m
[32m+[m[32m                                                                  <use xlink:href="{% static 'svg/sprite.svg' %}#it-close"></use>[m
[32m+[m[32m                                                               </svg>[m
[32m+[m[32m                                                            </button>[m
[32m+[m[32m                                                        </div>[m
[32m+[m[32m                                                        <div class="modal-body">[m
[32m+[m[32m                                                            <p>{% trans "Vuoi davvero disattivare la configurazione " %}[m
[32m+[m[32m                                                               <b>{{ conf }}</b> ?[m
[32m+[m[32m                                                            </p>[m
[32m+[m[32m                                                        </div>[m
[32m+[m[32m                                                        <div class="modal-footer">[m
[32m+[m[32m                                                            <a role="button" class="btn btn-danger"[m
[32m+[m[32m                                                               href="{% url 'uni_ticket:manager_structure_protocol_configuration_disable' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[32m+[m[32m                                                                {% trans "Si, disattiva la configurazione" %}[m
[32m+[m[32m                                                            </a>[m
                                                         </div>[m
                                                     </div>[m
                                                 </div>[m
[31m-                                                <div class="modal fade" tabindex="-1" role="dialog" id="deleteConfiguration{{ forloop.counter0 }}">[m
[31m-                                                    <div class="modal-dialog modal-dialog-centered" role="document">[m
[31m-                                                        <div class="modal-content">[m
[31m-                                                            <div class="modal-header">[m
[31m-                                                                <h5 class="modal-title">[m
[31m-                                                                    {% trans "Eliminazione configurazione" %}[m
[31m-                                                                </h5>[m
[31m-                                                                <button class="close" type="button"[m
[31m-                                                                        data-dismiss="modal" aria-label="Close">[m
[31m-                                                                   <svg class="icon">[m
[31m-                                                                      <use xlink:href="{% static 'svg/sprite.svg' %}#it-close"></use>[m
[31m-                                                                   </svg>[m
[31m-                                                                </button>[m
[31m-                                                            </div>[m
[31m-                                                            <div class="modal-body">[m
[31m-                                                                <p>{% trans "Vuoi davvero eliminare la configurazione " %}[m
[31m-                                                                   <b>{{ conf }}</b> ?[m
[31m-                                                                </p>[m
[31m-                                                            </div>[m
[31m-                                                            <div class="modal-footer">[m
[31m-                                                                <a role="button" class="btn btn-danger"[m
[31m-                                                                   href="{% url 'uni_ticket:manager_structure_protocol_configuration_delete' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[31m-                                                                    {% trans "Si, elimina la configurazione" %}[m
[31m-                                                                </a>[m
[31m-                                                            </div>[m
[32m+[m[32m                                            </div>[m
[32m+[m[32m                                            <div class="modal fade" tabindex="-1" role="dialog" id="deleteConfiguration{{ forloop.counter0 }}">[m
[32m+[m[32m                                                <div class="modal-dialog modal-dialog-centered" role="document">[m
[32m+[m[32m                                                    <div class="modal-content">[m
[32m+[m[32m                                                        <div class="modal-header">[m
[32m+[m[32m                                                            <h5 class="modal-title">[m
[32m+[m[32m                                                                {% trans "Eliminazione configurazione" %}[m
[32m+[m[32m                                                            </h5>[m
[32m+[m[32m                                                            <button class="close" type="button"[m
[32m+[m[32m                                                                    data-dismiss="modal" aria-label="Close">[m
[32m+[m[32m                                                               <svg class="icon">[m
[32m+[m[32m                                                                  <use xlink:href="{% static 'svg/sprite.svg' %}#it-close"></use>[m
[32m+[m[32m                                                               </svg>[m
[32m+[m[32m                                                            </button>[m
[32m+[m[32m                                                        </div>[m
[32m+[m[32m                                                        <div class="modal-body">[m
[32m+[m[32m                                                            <p>{% trans "Vuoi davvero eliminare la configurazione " %}[m
[32m+[m[32m                                                               <b>{{ conf }}</b> ?[m
[32m+[m[32m                                                            </p>[m
[32m+[m[32m                                                        </div>[m
[32m+[m[32m                                                        <div class="modal-footer">[m
[32m+[m[32m                                                            <a role="button" class="btn btn-danger"[m
[32m+[m[32m                                                               href="{% url 'uni_ticket:manager_structure_protocol_configuration_delete' structure_slug=structure.slug configuration_id=conf.pk %}">[m
[32m+[m[32m                                                                {% trans "Si, elimina la configurazione" %}[m
[32m+[m[32m                                                            </a>[m
                                                         </div>[m
                                                     </div>[m
                                                 </div>[m
[31m-                                                {% endfor %}[m
[31m-                                            </tbody>[m
[31m-                                        </table>[m
[31m-                                    </div>[m
[31m-                                {% endif %}[m
[32m+[m[32m                                            </div>[m
[32m+[m[32m                                            {% endcomment %}[m
[32m+[m[32m                                            {% endfor %}[m
[32m+[m[32m                                        </tbody>[m
[32m+[m[32m                                    </table>[m
[32m+[m[32m                                </div>[m
[32m+[m[32m                                {% comment %}[m
                                 <div>[m
                                     <a class="btn btn-outline-success btn-block mt-4"[m
                                        href="{% url 'uni_ticket:manager_structure_protocol_configuration_new' structure_slug=structure.slug %}">[m
[36m@@ -222,11 +230,13 @@[m
                                         </svg> Aggiungi nuova configurazione[m
                                     </a>[m
                                 </div>[m
[32m+[m[32m                                {% endcomment %}[m
                             </div>[m
                         </div>[m
                     </div>[m
                 </div>[m
             </div>[m
[32m+[m[32m            {% endif %}[m
         </div>[m
     </div>[m
 </div>[m
[1mdiff --git a/uni_ticket_project/settingslocal.py.example b/uni_ticket_project/settingslocal.py.example[m
[1mindex 1542c9d..62776bb 100644[m
[1m--- a/uni_ticket_project/settingslocal.py.example[m
[1m+++ b/uni_ticket_project/settingslocal.py.example[m
[36m@@ -308,7 +308,7 @@[m [mPROTOCOL_XML = """<Segnatura xmlns:xsi="http://www.w3.org/2001/XMLSchema-instanc[m
 <Denominazione>UNICAL</Denominazione>[m
 <CodiceAmministrazione>UNICAL</CodiceAmministrazione>[m
 <IndirizzoTelematico tipo="smtp">amministrazione@pec.unical.it</IndirizzoTelematico>[m
[31m-<UnitaOrganizzativa id="{uo_id}"/>[m
[32m+[m[32m<UnitaOrganizzativa id=""/>[m
 </Amministrazione>[m
 </Destinatario>[m
 <Classifica>[m
[36m@@ -340,7 +340,7 @@[m [mPROT_FASCICOLO_DEFAULT = 'default_fascicolo'[m
 PROT_FASCICOLO_ANNO_DEFAULT = 'default_year'[m
 PROT_AGD_DEFAULT = 'default_agd'[m
 PROT_UO_DEFAULT = 'default_uo'[m
[31m-PROT_UO_ID_DEFAULT = 'default_uo_id'[m
[32m+[m[32m# PROT_UO_ID_DEFAULT = 'default_uo_id'[m
 PROT_TITOLARIO_DEFAULT = 'default_titolario'[m
 PROT_TEST_URL = 'url_test'[m
 PROT_TEST_LOGIN = 'test_login'[m
