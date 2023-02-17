from django import forms
from django_form_builder.forms import BaseDynamicForm
from django_form_builder import dynamic_fields
from uni_ticket.settings import (
    TICKET_CAPTCHA_HIDDEN_ID,
    TICKET_CAPTCHA_ID,
    TICKET_CAPTCHA_LABEL,
    TICKET_CONDITIONS_FIELD_ID,
    TICKET_CONDITIONS_TEXT,
    TICKET_DESCRIPTION_HELP_TEXT,
    TICKET_DESCRIPTION_ID,
    TICKET_DESCRIPTION_LABEL,
    TICKET_SUBJECT_HELP_TEXT,
    TICKET_SUBJECT_ID,
    TICKET_SUBJECT_LABEL,
)


class DynamicForm(BaseDynamicForm):
    """ """

    def __init__(self, constructor_dict={}, custom_params={}, *args, **kwargs):

        self.initial_fields = {}
        self.final_fields = {}

        category_owner = custom_params.get("category_owner")
        show_conditions = custom_params.get("show_conditions")
        subject_initial = custom_params.get("subject_initial")
        description_initial = custom_params.get("description_initial")
        current_user = custom_params.get("current_user")

        conditions = category_owner.get_conditions()
        # If conditions to accept, generate checkbox field
        # and put it in initial fields
        if conditions and show_conditions:
            conditions_id = dynamic_fields.format_field_name(
                TICKET_CONDITIONS_FIELD_ID)
            conditions_data = {
                "required": True,
                "label": TICKET_CONDITIONS_TEXT,
            }
            conditions_field = getattr(dynamic_fields, "CheckBoxField")(
                **conditions_data
            )
            self.initial_fields[conditions_id] = conditions_field

        # Generate SUBJECT TICKET field
        # and put it in initial fields
        subject_id = dynamic_fields.format_field_name(TICKET_SUBJECT_ID)
        subject_data = {
            "required": True,
            "label": TICKET_SUBJECT_LABEL,
            "help_text": TICKET_SUBJECT_HELP_TEXT,
            "initial": subject_initial,
        }
        subject_field = getattr(
            dynamic_fields, "CustomCharField")(**subject_data)
        self.initial_fields[subject_id] = subject_field

        # Generate DESCRIZIONE TICKET field
        # and put it in initial fields
        description_id = dynamic_fields.format_field_name(
            TICKET_DESCRIPTION_ID)
        description_data = {
            "required": True,
            "label": TICKET_DESCRIPTION_LABEL,
            "help_text": TICKET_DESCRIPTION_HELP_TEXT,
            "initial": description_initial,
        }
        description_field = getattr(
            dynamic_fields, "TextAreaField")(**description_data)
        self.initial_fields[description_id] = description_field
        self.initial_fields[description_id].widget = forms.Textarea(attrs={
                                                                    "rows": 2})

        # if current_user is anonymous, generate CAPTCHA field
        # and put it in final_fields
        if current_user and not current_user.is_authenticated:
            captcha_data = {
                "label": TICKET_CAPTCHA_LABEL,
                "captcha_name": dynamic_fields.format_field_name(TICKET_CAPTCHA_ID),
                "captcha_hidden_name": dynamic_fields.format_field_name(
                    TICKET_CAPTCHA_HIDDEN_ID
                ),
            }
            captcha_field = getattr(dynamic_fields, "CustomCaptchaComplexField")(
                **captcha_data
            )
            captcha_field.define_value(custom_value="", **custom_params)
            for single_field in captcha_field.get_fields():
                self.final_fields[single_field.name] = single_field
        super().__init__(
            initial_fields=self.initial_fields,
            final_fields=self.final_fields,
            constructor_dict=constructor_dict,
            custom_params=custom_params,
            *args,
            **kwargs
        )

    class Media:
        js = ("js/textarea-autosize.js",)


def _get_choices(choices):
    elements = []
    for choice in choices:
        if (type(choice[1]) == tuple):
            elements.extend(_get_choices(choice[1]))
        else:
            elements.append(
                {"text": choice[1],
                 "value": choice[0]}
            )
    return elements


def serialize_form(form, api_source = 'api_source'):

    form_fields = []

    for field_name in form.fields:
        field = form.fields[field_name]
        field_type = getattr(field.widget.__class__,
                             'input_type',
                             'textarea')

        field_dict = {}
        field_dict['id'] = field_name
        field_dict['label'] = field.label
        field_dict['initial'] = field.initial
        field_dict['disabled'] = field.disabled
        field_dict['required'] = True if field.required else False
        field_dict['error_messages'] = field.error_messages
        field_dict['help_text'] = field.help_text
        field_dict['api_source'] = getattr(field, api_source, '')
        field_dict['options'] = []
        field_dict['multiple'] = 0
        field_dict['html'] = field.widget.render(field_name, field.initial)

        class_name = field.widget.__class__.__name__

        if class_name == 'DateInput':
            field_dict['type'] = 'date'
        elif class_name == 'DateTimeInput':
            field_dict['type'] = 'datetime'
        elif class_name in ('Select', 'SelectMultiple', 'CheckboxSelectMultiple'):
            field_dict['type'] = 'select'
            if field.widget.__class__.__dict__.get('allow_multiple_selected'):
                field_dict['multiple'] = 1

            if hasattr(field, '_queryset') and not getattr(field, api_source, ''):
                for item in field._queryset:
                    field_dict['options'].append({"text": item.__str__(),
                                                  "value": item.pk})
            elif hasattr(field, '_choices'):
                field_dict['options'].extend(_get_choices(field._choices))
        else:
            field_dict['type'] = field_type
        form_fields.append(field_dict)
    return form_fields
