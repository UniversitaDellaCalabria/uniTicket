import re
from protocollo_ws.settings import (PROT_MAX_LABEL_LENGHT,
                                    PROT_UNALLOWED_CHARS)

def clean_string(word):
    # ignore bytes and int and all the other type different from str
    if not isinstance(word, str): return word
    # non sono giunte specifiche chiare sulla lunghezza massima...
    word = word[:PROT_MAX_LABEL_LENGHT]
    # su WSArchiPRO non si capisce come fare funzionare l'escape...
    for c in PROT_UNALLOWED_CHARS:
        # word = word.replace(c, '\{}'.format(c))
        word = word.replace(c, '')
    # oppure, ancora meglio sarebbe
    # word = re.escape(word)
    return word
