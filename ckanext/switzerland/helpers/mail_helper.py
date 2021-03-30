# encoding: utf-8

import logging
from ckan.common import config
from ckan.lib.base import render_jinja2
import ckan.lib.mailer as mailer

log = logging.getLogger(__name__)


def get_registration_body(user):
    """set up text for user registration email"""
    extra_vars = {
        'site_title': config.get('ckan.site_title'),
        'site_url': config.get('ckan.site_url'),
        'user_name': user.get('name'),
        'display_name': user.get('display_name', user['name'])
        }
    # NOTE: This template is translated
    return render_jinja2('emails/registration.txt', extra_vars)


def send_registration_email(user):
    """send new users an email at the time of registartion"""
    body = get_registration_body(user)
    extra_vars = {
        'site_title': config.get('ckan.site_title')
    }
    subject = render_jinja2('emails/registration_subject.txt', extra_vars)

    # Make sure we only use the first line
    subject = subject.split('\n')[0]

    recipient_name = user.get('display_name', user['name'])
    recipient_email = user.get('email')
    mailer.mail_recipient(recipient_name, recipient_email, subject, body)
