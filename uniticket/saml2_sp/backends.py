from djangosaml2.backends import Saml2Backend

from accounts.settings import EDITABLE_FIELDS
from saml2_sp.settings import SAML_ATTRIBUTE_MAPPING


class CustomSaml2Backend(Saml2Backend):
    """SAML2 backend that stores the login context and keeps the user's manual changes."""
    
    def authenticate(self, request, session_info=None, attribute_mapping=None, create_unknown_user=True, **kwargs):
        """
        Authenticates the user and stores the SAML authentication context.

        The first authn_info context class (e.g. the SPID level) is saved in
        last_login_context.

        Args:
            request: The current HttpRequest.
            session_info: The SAML session data of the assertion.

        Returns:
            The authenticated user, or None if authentication failed.
        """
        user = super().authenticate(
            request,
            session_info=session_info,
            attribute_mapping=attribute_mapping,
            create_unknown_user=create_unknown_user,
            **kwargs
        )

        if not user:
            return None

        auth_info = (session_info or {}).get('authn_info')
        if auth_info:
            user.last_login_context = auth_info[0][0]
        else:
            user.last_login_context = ""
        user.save(update_fields=['last_login_context'])
        return user

    def _update_user(self, user, attributes: dict, attribute_mapping: dict, force_save: bool = False):
        """
        Updates the user from the SAML attributes.

        Attributes mapped to EDITABLE_FIELDS are popped from attributes and
        set only if the field is empty or the user has never changed their
        data manually; the remaining ones are handled by the parent backend.

        Args:
            user: The user to update.
            attributes: The SAML attributes (not modified).
            attribute_mapping: Map from SAML attributes to user fields.
            force_save: Whether to save the user even if nothing changed.

        Returns:
            The value returned by the parent _update_user.
        """
        # copy: don't change the attributes dict of the caller
        attributes = dict(attributes)
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
            if not attr: continue
            # if attribute exists and user haven't done a manual update
            if not getattr(user, mapping[el], None) or not user.manual_user_update:
                # update field for user
                setattr(user, mapping[el], attr)
                force_save = True
        return super()._update_user(user, attributes, attribute_mapping, force_save)
