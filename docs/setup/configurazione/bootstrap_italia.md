# Bootstrap Italia

L'interfaccia utente di uniTicket è progettata nativamente per integrarsi con il design system della Pubblica Amministrazione. Di default, il sistema adotta il template Bootstrap Italia, garantendo accessibilità, usabilità e coerenza visiva secondo le linee guida AGID.

Il framework dei template è costruito su una logica di ereditarietà: ogni pagina del sistema estende un file di base comune. Qualora l'ente avesse la necessità di integrare un tema grafico differente o una personalizzazione strutturale del layout (ad esempio per inserire header o footer istituzionali specifici), è possibile agire sul parametro **DEFAULT_BASE_TEMPLATE** nel file *settingslocal.py*.

Specificando un file differente, tutte le viste del progetto erediteranno la nuova struttura definita, mantenendo però intatti i blocchi funzionali interni.

``` python
# default template to extend
# Default Bootstrap Italia template: 'bootstrap-italia-base.html'
# Example: Unical template: 'base-setup.html'
# DEFAULT_BASE_TEMPLATE = 'base-setup.html'
```