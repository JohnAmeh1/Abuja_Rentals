import logging
import threading

from django.db.models.signals import post_save
from django.dispatch           import receiver
from .services.send_mail import _send_notification_email_thread

from .models import Notification

logger = logging.getLogger(__name__)



@receiver(post_save, sender=Notification)
def on_notification_created(sender, instance, created, **kwargs):
    if not created:
        return 

    if not instance.user.email:
        return 
    
    if instance.type in ["email_verification", "login_otp", "forgot_password"]:
        return

    # try:
    #     if not instance.user.userprofile.email_notifications:
    #         return
    # except Exception:
    #     pass 

    threading.Thread(
        target=_send_notification_email_thread,
        args=(instance.id,),
        daemon=True,
    ).start()


