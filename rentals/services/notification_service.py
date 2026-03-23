from django.contrib.auth.models import User

class NotificationService:
    @classmethod
    def notify_user(cls, userid, type, message, **kwargs):
        user = User.objects.get(id=userid)
        if not user:
            return None
        
        n = cls.objects.create(
            user=user,
            type=type,
            message=message,
            related_id = kwargs.get("related_id")
        )
        
        n.save()
        return n