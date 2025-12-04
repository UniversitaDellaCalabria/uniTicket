from djangosaml2.backends import Saml2Backend

from accounts.settings import EDITABLE_FIELDS
from saml2_sp.settings import SAML_ATTRIBUTE_MAPPING


class CustomSaml2Backend(Saml2Backend):
    
    def authenticate(self, request, session_info=None, attribute_mapping=None, create_unknown_user=True, **kwargs):
        user = super().authenticate(
            request,
            session_info=session_info,
            attribute_mapping=attribute_mapping,
            create_unknown_user=create_unknown_user,
            **kwargs
        )

        auth_info = session_info.get('authn_info')
        if auth_info:
            user.last_login_context = auth_info[0][0]
        else:
            user.last_login_context = ""
        user.save(update_fields=['last_login_context'])
        return user

    def _update_user(self, user, attributes: dict, attribute_mapping: dict, force_save: bool = False):
        mapping = {}
        # get editable fields from accounts app
        for ef in EDITABLE_FIELDS:
            # get mapping from saml2_sp settings
            for key in SAML_ATTRIBUTE_MAPPING:
                # for every editable fields get saml attributes
                if ef in SAML_ATTRIBUTE_MAPPING[key]:
                    mapping[key] = ef
        # for every editable field
        for el in mapping:
            # get saml2 value from attributes
            # pop to avoid the saml2 default update
            saml_attr = attributes.pop(el, [])
            attr = saml_attr[0] if saml_attr else None
            # if attribute exists and user haven't done a manual update
            if attr and not user.manual_user_update:
                # update field for user
                setattr(user, mapping[el], attr)
                force_save = True
        return super()._update_user(user, attributes, attribute_mapping, force_save)
