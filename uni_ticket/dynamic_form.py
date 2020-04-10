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

        self.initial_fields = {}
        self.final_fields = {}

        category_owner = custom_params.get('category_owner')
        show_conditions = custom_params.get('show_conditions')
        subject_initial = custom_params.get('subject_initial')
        description_initial = custom_params.get('description_initial')
        current_user = custom_params.get('current_user')

        conditions = category_owner.get_conditions()
        # If conditions to accept, generate checkbox field
        # and put it in initial fields
        if conditions and show_conditions:
            conditions_id = dynamic_fields.format_field_name(settings.TICKET_CONDITIONS_FIELD_ID)
            conditions_data = {'required' : True,
                               'label': settings.TICKET_CONDITIONS_TEXT}
            conditions_field = getattr(dynamic_fields,
                                       'CheckBoxField')(**conditions_data)
            self.initial_fields[conditions_id] = conditions_field

        # Generate SUBJECT TICKET field
        # and put it in initial fields
        subject_id = dynamic_fields.format_field_name(settings.TICKET_SUBJECT_ID)
        subject_data = {'required' : True,
                        'label': settings.TICKET_SUBJECT_LABEL,
                        'help_text': settings.TICKET_SUBJECT_HELP_TEXT,
                        'initial': subject_initial}
        subject_field = getattr(dynamic_fields,
                                'CustomCharField')(**subject_data)
        self.initial_fields[subject_id] = subject_field

        # Generate DESCRIZIONE TICKET field
        # and put it in initial fields
        description_id = dynamic_fields.format_field_name(settings.TICKET_DESCRIPTION_ID)
        description_data = {'required' : True,
                            'label': settings.TICKET_DESCRIPTION_LABEL,
                            'help_text': settings.TICKET_DESCRIPTION_HELP_TEXT,
                            'initial': description_initial}
        description_field = getattr(dynamic_fields,
                                    'TextAreaField')(**description_data)
        self.initial_fields[description_id] = description_field

        # if current_user is anonymous, generate CAPTCHA field
        # and put it in final_fields
        if current_user and not current_user.is_authenticated:
            captcha_data = {'label': settings.TICKET_CAPTCHA_LABEL,
                            'captcha_name': dynamic_fields.format_field_name(settings.TICKET_CAPTCHA_ID),
                            'captcha_hidden_name': dynamic_fields.format_field_name(settings.TICKET_CAPTCHA_HIDDEN_ID)}
            captcha_field = getattr(dynamic_fields,
                                    'CustomCaptchaComplexField')(**captcha_data)
            for single_field in captcha_field.get_fields():
                self.final_fields[single_field.name] = single_field

        super().__init__(initial_fields=self.initial_fields,
                         final_fields=self.final_fields,
                         constructor_dict=constructor_dict,
                         custom_params=custom_params,
                         *args, **kwargs)

    class Media:
        js = ('js/textarea-autosize.js', 'js/datepicker.js')
