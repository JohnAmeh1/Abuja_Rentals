from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rentals.models import Wallet

class Command(BaseCommand):
    help = 'Create wallets for existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            wallet, created = Wallet.objects.get_or_create(user=user)
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created wallets for {created_count} users'))