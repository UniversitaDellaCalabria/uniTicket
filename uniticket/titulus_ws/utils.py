

def protocol_entrata_dict(**kwargs):

    protocol_data = {
                     # Variabili
                     'oggetto': '{:<20}'.format(kwargs.get('oggetto')),
                     'autore': kwargs.get('autore'),

                     'cod_amm_aoo': kwargs.get('aoo'),

                     # riferimento interno
                     'nome_persona_rif_interno': kwargs.get('destinatario'),

                     'destinatario_username': kwargs.get('destinatario_username'),
                     'destinatario_code': kwargs.get('destinatario_code'),

                     'nome_uff_rif_interno': kwargs.get('uo_nome'),
                     'cod_uff_rif_interno': kwargs.get('uo'),

                     'send_email': kwargs.get('send_email'),

                     # riferimento esterno
                     'nome_rif_esterno': f'{kwargs.get("nome_mittente")} {kwargs.get("cognome_mittente")}',
                     'codice_fiscale_rif_esterno': kwargs.get('cod_fis_mittente'),
                     'cod_nome_rif_esterno': kwargs.get('cod_fis_mittente'),
                     'email_rif_esterno': kwargs.get('email_mittente'),
                     'fax_rif_esterno': '',
                     'tel_rif_esterno': '',
                     'indirizzo': '',

                     'classif': kwargs.get('titolario'),
                     'cod_classif': kwargs.get('cod_titolario'),

                     'allegato': kwargs.get('num_allegati'),
                    }
    return protocol_data
