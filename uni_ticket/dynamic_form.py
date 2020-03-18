from django.conf import settings
from django_form_builder.forms import BaseDynamicForm
from django_form_builder import dynamic_fields


class DynamicForm(BaseDynamicForm):
    """
    """
    def __init__(self,
                 constructor_dict={},
                 custom_params={},
                 *args,
                 **kwargs):

        self.fields = {}
        category_owner = custom_params.get('category_owner')
        show_conditions = custom_params.get('show_conditions')
        subject_initial = custom_params.get('subject_initial')
        description_initial = custom_params.get('description_initial')
        conditions = category_owner.get_conditions()
        # Inserimento manuale del checkbox per accettazione condizioni
        if conditions and show_conditions:
            conditions_id = dynamic_fields.format_field_name(settings.TICKET_CONDITIONS_FIELD_ID)
            conditions_data = {'required' : True,
                               'label': settings.TICKET_CONDITIONS_TEXT}
            conditions_field = getattr(dynamic_fields,
                                       'CheckBoxField')(**conditions_data)
            self.fields[conditions_id] = conditions_field

        # Inserimento manuale dei fields SUBJECT TICKET
        subject_id = dynamic_fields.format_field_name(settings.TICKET_SUBJECT_ID)
        subject_data = {'required' : True,
                        'label': settings.TICKET_SUBJECT_LABEL,
                        'help_text': settings.TICKET_SUBJECT_HELP_TEXT,
                        'initial': subject_initial}
        subject_field = getattr(dynamic_fields,
                                'CustomCharField')(**subject_data)
        self.fields[subject_id] = subject_field

        # Inserimento manuale dei fields DESCRIZIONE TICKET
        description_id = dynamic_fields.format_field_name(settings.TICKET_DESCRIPTION_ID)
        description_data = {'required' : True,
                            'label': settings.TICKET_DESCRIPTION_LABEL,
                            'help_text': settings.TICKET_DESCRIPTION_HELP_TEXT,
                            'initial': description_initial}
        description_field = getattr(dynamic_fields,
                                    'TextAreaField')(**description_data)
        self.fields[description_id] = description_field

        # kwargs['dyn_fields'] = self.fields

        super().__init__(initial_fields=self.fields,
                         constructor_dict=constructor_dict,
                         custom_params=custom_params,
                         *args, **kwargs)

    class Media:
        js = ('js/textarea-autosize.js', 'js/datepicker.js')
