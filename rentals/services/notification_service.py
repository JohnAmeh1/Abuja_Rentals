from ..models import User, Notification

def notify_user(userid, type, message, mode):
    user = User.objects.get(id=userid)
    if not user:
        return None
    
    n = Notification.objects.create(
        user=user,
        message_type=type,
        message=message,
    )
    
    if mode:
        n.mode = mode
    
    n.save()
    return n