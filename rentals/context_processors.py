# Create a context processor to show wallet balance everywhere
# In rentals/context_processors.py
from .models import Wallet

def wallet_context(request):
    context = {}
    if request.user.is_authenticated:
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0.00}
        )
        context['wallet_balance'] = wallet.balance
    return context

# context_processors.py
from .models import AdminMessage
from django.utils import timezone

def admin_messages_context(request):
    """Make active admin messages available in all templates"""
    if request.user.is_authenticated:
        # Get messages that should be shown to current user
        messages_to_show = []
        for message in AdminMessage.objects.filter(is_active=True):
            if message.should_show_to_user(request.user):
                # Check if message is currently active based on dates
                if message.is_current():
                    # Check if user has already dismissed this message
                    session_key = f'dismissed_message_{message.id}'
                    if not request.session.get(session_key):
                        messages_to_show.append(message)
        
        return {'admin_messages': messages_to_show}
    return {'admin_messages': []}