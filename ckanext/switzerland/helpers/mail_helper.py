# encoding: utf-8

import logging
from ckan.common import config
from ckan.lib.base import render_jinja2
import ckan.lib.mailer as mailer

SITE_TITLE = config.get('ckan.site_title')
SITE_URL = config.get('ckan.site_url')
SHOWCASE_ADMIN_EMAIL = config.get(
    'ckanext.switzerland.showcase_admin_email'
)
SHOWCASE_ADMIN_NAME = config.get(
    'ckanext.switzerland.showcase_admin_name'
)

log = logging.getLogger(__name__)


def get_registration_body(user):
    """set up text for user registration email"""
    extra_vars = {
        'site_title': SITE_TITLE,
        'site_url': SITE_URL,
        'user_name': user.get('name'),
        'display_name': user.get('display_name', user['name'])
        }
    # NOTE: This template is translated
    return render_jinja2('emails/registration.txt', extra_vars)


def send_registration_email(user):
    """send new users an email at the time of registartion"""
    body = get_registration_body(user)
    extra_vars = {
        'site_title': SITE_TITLE
    }
    subject = render_jinja2('emails/registration_subject.txt', extra_vars)

    # Make sure we only use the first line
    subject = subject.split('\n')[0]

    recipient_name = user.get('display_name', user['name'])
    recipient_email = user.get('email')
    mailer.mail_recipient(recipient_name, recipient_email, subject, body)


def send_showcase_email(showcase):
    """send an email when a showcase is created"""
    extra_vars = {
        'showcase_url': SITE_URL + '/showcase/' + showcase.get('name'),
    }
    mailer.mail_recipient(
        SHOWCASE_ADMIN_NAME,
        SHOWCASE_ADMIN_EMAIL,
        render_jinja2('emails/showcase_subject.txt', extra_vars),
        render_jinja2('emails/showcase.txt', extra_vars),
    )
