from django.core.mail          import EmailMultiAlternatives
from django.template.loader    import render_to_string
from django.conf               import settings
from django.db                 import connection
import logging
logger = logging.getLogger(__name__)

from ..models import Notification

NOTIFICATION_CONFIG = {
    'new_inquiry':            ('New property request in your area',           'emails/new_inquiry.html'),
    'inquiry_response':       ('An agent responded to your request',          'emails/inquiry_response.html'),
    'property_approved':      ('Your listing has been approved',              'emails/property_approved.html'),
    'property_rejected':      ('Update on your listing',                      'emails/property_rejected.html'),
    'agent_verified':         ('Your agent account has been verified',        'emails/agent_verified.html'),
    'new_visit_request':      ('New visit request for your property',         'emails/visit_request.html'),
    'visit_confirmed':        ('Your visit has been confirmed',               'emails/visit_confirmed.html'),
    'verification_request':   ('Agent verification request',                  'emails/verification_request.html'),

    'email_verification':     ('Verify your email address',                   'emails/email_verification.html'),
    'login_otp':              ('Your login verification code',                'emails/login_otp.html'),
    'forgot_password':        ('Reset your password',                         'emails/forgot_password.html'),

    'welcome':                ('Welcome to AbujaRentals',                     'emails/welcome.html'),
    'password_changed':       ('Your password was changed',                   'emails/password_changed.html'),
    'visit_cancelled':        ('A visit has been cancelled',                  'emails/visit_cancelled.html'),
    'property_expired':       ('Your listing has expired',                    'emails/property_expired.html'),
    'inquiry_closed':         ('Your inquiry has been closed',                'emails/inquiry_closed.html'),
}

FALLBACK_SUBJECT  = 'You have a new notification — Abuja Rentals'
FALLBACK_TEMPLATE = 'emails/generic_notification.html'

def _build_email(notification):
    subject, template = NOTIFICATION_CONFIG.get(
        notification.type,
        (FALLBACK_SUBJECT, FALLBACK_TEMPLATE)
    )

    context = {
        'notification': notification,
        'user':         notification.user,
        'site_name':    'Abuja Rentals',
        'site_url':     settings.SITE_URL,
    }
    
    if notification.type in ["email_verification", "login_otp", "forgot_password"]:
        context["otp_code"] = notification.message

    try:
        body_html = render_to_string(template, context)
    except Exception:
        body_html = None

    body_text = notification.message  

    return subject, body_text, body_html

def _send_notification_email(notification_id):
    try:
        notification = (
            Notification.objects
            .select_related('user', 'user__userprofile')
            .get(id=notification_id)
        )

        subject, body_text, body_html = _build_email(notification)

        msg = EmailMultiAlternatives(
            subject    = subject,
            body       = body_text,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [notification.user.email],
        )
        if body_html:
            msg.attach_alternative(body_html, 'text/html')

        msg.send(fail_silently=False)

        notification.sent = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found for email")
        return False
    except Exception as e:
        logger.error(f"Failed to email notification {notification_id}: {e}", exc_info=True)
        return False



def _send_notification_email_thread(notification_id):
    try:
        notification = (
            Notification.objects
            .select_related('user', 'user__userprofile')
            .get(id=notification_id)
        )

        subject, body_text, body_html = _build_email(notification)

        msg = EmailMultiAlternatives(
            subject    = subject,
            body       = body_text,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [notification.user.email],
        )
        if body_html:
            msg.attach_alternative(body_html, 'text/html')

        msg.send(fail_silently=False)

        Notification.objects.filter(id=notification_id).update(sent=True)
    except Notification.DoesNotExist:
        logger.warning(f"Notification {notification_id} not found for email")
    except Exception as e:
        logger.error(f"Failed to email notification {notification_id}: {e}", exc_info=True)
    finally:
        connection.close()