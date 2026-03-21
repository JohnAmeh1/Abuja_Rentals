from django.contrib.auth.models import User

class NotificationService:
    @classmethod
    def notify_user(cls, userid, type, message, mode):
        user = User.objects.get(id=userid)
        if not user:
            return None
        
        n = cls.objects.create(
            user=user,
            message_type=type,
            message=message,
        )
        
        if mode:
            n.mode = mode
        
        n.save()
        return n