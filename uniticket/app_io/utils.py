import json
import logging
import requests

from . models import IOLog, IOServiceTicketCategory
from . settings import *


logger = logging.getLogger(__name__)


def _callIOApi(method='get',
               endpoint='',
               key='',
               data={}):
    url = f'{APP_IO_API_BASE_URL}/{endpoint}'
    headers = {APP_IO_API_HEADER_KEY: key}
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(data),
            timeout=5
        )
    except requests.exceptions.Timeout:
        return {
            'data': {},
            'status': 503
        }
    return {
        'data': response.json(),
        'status': response.status_code
    }


def check_user_profile(fiscal_code, service_id, service_key):
    # check if Io can notify user (/profiles API)
    data = {"fiscal_code": fiscal_code}
    logger.info(f'Getting App IO {fiscal_code} profile for service {service_id}')
    response = _callIOApi(
        method='post',
        key=service_key,
        endpoint=APP_IO_API_PROFILES_ENDPOINT,
        data=data
    )

    if response['status'] != 200:
        error = response['data'].get('detail', response['status'])
        logger.info(f'Error App IO {fiscal_code} profile for service {service_id}: {error}')
        return (False, error)
    if not response['data'].get('sender_allowed', 0):
        error = 'Sender not allowed by user'
        logger.info(f'Error App IO {fiscal_code} profile for service {service_id}: {error}')
        return (False, error)
    return (True, None)
    # END check if Io can notify user (/profiles API)


def send_message(ticket, subject, body, log=None):
    io_service = IOServiceTicketCategory.objects.filter(category=ticket.input_module.ticket_category,
                                                        service__is_active=True,
                                                        is_active=True).select_related('service').first()
    if not io_service: return False

    user = ticket.created_by.taxpayer_id
    service_id = io_service.service.service_id
    service_key = io_service.service.api_key

    # check App IO user profile for service
    check = check_user_profile(user, service_id, service_key)
    if not check[0]:
        result = {
            'message_id': None,
            'error': check[1]
        }
    else:
        logger.info(f'Sending App IO message {ticket.code} to {user}')
        msg_data = {
            "fiscal_code": user,
            "content": {
                "subject": subject,
                "markdown": body
            }
        }
        # call generic callIOApi
        response = _callIOApi(
            method='post',
            endpoint=APP_IO_API_MESSAGES_ENDPOINT,
            key=service_key,
            data=msg_data
        )
        # success
        if response['status'] == 201:
            message_id = response['data']['id']
            error_detail = None
            logger.info(f'App IO message sent: {ticket.code} to {user}')
        # error
        else:
            message_id = None
            error_detail = response['data'].get('detail', response['status'])
            logger.info("Appi IO error: " + error_detail)

        result = {
            'message_id': message_id,
            'error': error_detail
        }

    if log:
        IOLog.objects.create(
            log=log,
            response=result
        )

    return result
