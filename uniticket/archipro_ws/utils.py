from archipro_ws.settings import (PROT_MAX_LABEL_LENGTH,
                                  PROT_UNALLOWED_CHARS)


def clean_string(word, save_extension=False):
    # ignore bytes and int and all the other type different from str
    if not isinstance(word, str): return word
    # non sono giunte specifiche chiare sulla lunghezza massima...
    # 50 caratteri
    if save_extension:
        fpart = word.rpartition('.')
        limit = PROT_MAX_LABEL_LENGTH - len(fpart[-1]) - 1
        word = '.'.join((fpart[0][:limit], fpart[-1]))
    else:
        word = word[:PROT_MAX_LABEL_LENGTH]
    # su WSArchiPRO non si capisce come fare funzionare l'escape...
    for c in PROT_UNALLOWED_CHARS:
        # word = word.replace(c, '\{}'.format(c))
        word = word.replace(c, '')
    # oppure, ancora meglio sarebbe
    # word = re.escape(word)
    return word


def protocol_entrata_dict(**kwargs):

    protocol_data = {
        # Variabili
        'oggetto': kwargs.get('oggetto'),
        # 'identificativo_dipendente': user.identificativo_dipendente,
        'id_persona': kwargs.get('cod_fis_mittente'),
        'nome_persona': kwargs.get('nome_mittente'),
        'cognome_persona': kwargs.get('cognome_mittente'),
        # 'denominazione_persona': ' '.join((user.first_name,
        # user.last_name,)),

        # attributi creazione protocollo
        'aoo': kwargs.get('aoo'),
        'agd': kwargs.get('agd'),
        'uo': kwargs.get('uo'),
        'email': kwargs.get('email_ufficio'),
        'id_titolario': kwargs.get('titolario'),
        'fascicolo_numero': kwargs.get('fascicolo_num'),
        'fascicolo_anno': kwargs.get('fascicolo_anno')
    }
    return protocol_data
