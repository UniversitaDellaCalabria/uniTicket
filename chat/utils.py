import random
import re

from django.apps import apps

from organizational_area.models import OrganizationalStructure
from uni_ticket.utils import user_is_in_default_office


def chat_operator(user, structure_slug):
    if not structure_slug: return False
    if not user: return False
    structure = OrganizationalStructure.objects.filter(slug=structure_slug,
                                                       is_active=True).first()
    if not structure: return False
    return user_is_in_default_office(user, structure)

def chat_operator_online(user, structure_slug):
    structure = OrganizationalStructure.objects.filter(slug=structure_slug,
                                                       is_active=True).first()
    if not structure: return False
    # if I'm an operator, I can enter in every moment in chat :)
    if user_is_in_default_office(user, structure):
        return True
    user_channel = apps.get_model('chat', 'UserChannel')
    users_in_room = user_channel.objects.filter(room=structure_slug).exclude(user=user)
    for room_user in users_in_room:
        if user_is_in_default_office(room_user.user, structure):
            return True
    return False

def get_text_with_hrefs(text):
    """Transforms a text with url in text with <a href=></a> tags
       text = ("Allora considerando quanto scritto quì "
               "https://ingoalla.it/sdfsd/.well-known/ini.php?sdf=3244&df23=FDS3_ "
               "dovresti piuttosto - se vuoi - andare qui "
               "http://rt4t.ty/546-546-56546 oppure "
               "https://mdq.auth.unical.it:8000/entities/https%3A%2F%2Fidp.unical.it%2Fidp%2Fshibboleth")
    get_text_with_hrefs(text)
    """
    new_text = ''.join([ch for ch in text])
    href_tmpl = '<a target="{}" href="{}">{}</a>'
    regexp = re.compile('https?://[\.A-Za-z0-9\-\_\:\/\?\&\=\+\%]*', re.I)
    for ele in re.findall(regexp, text):
        target = str(random.random())[2:]
        a_value = href_tmpl.format(target, ele, ele)
        new_text = new_text.replace(ele, a_value)
    return new_text
