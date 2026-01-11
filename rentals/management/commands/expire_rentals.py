# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from rentals.models import PropertyRental

# class Command(BaseCommand):
#     help = 'Expire rentals whose end_date has passed and mark them inactive.'

#     def handle(self, *args, **options):
#         today = timezone.now().date()
#         expired_qs = PropertyRental.objects.filter(is_active=True, end_date__lt=today)
#         count = expired_qs.count()
#         for rental in expired_qs:
#             rental.is_active = False
#             rental.save(update_fields=['is_active'])
#             # Optionally: send notification to tenant/owner here
#         self.stdout.write(self.style.SUCCESS(f'Marked {count} rentals expired.'))



from django.core.management.base import BaseCommand
from django.utils import timezone
from rentals.models import PropertyRental, Property

class Command(BaseCommand):
    help = 'Check and expire rentals that have passed their end date'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Get all active rentals
        active_rentals = PropertyRental.objects.filter(is_active=True)
        
        expired_count = 0
        properties_made_available = 0
        
        for rental in active_rentals:
            # Check if rental is expired
            if rental.end_date and rental.end_date < today:
                # Mark rental as inactive
                rental.is_active = False
                rental.save(update_fields=['is_active'])
                expired_count += 1
                
                self.stdout.write(
                    self.style.WARNING(
                        f'Expired rental: {rental.property.title} - Tenant: {rental.tenant.username}'
                    )
                )
        
        # Check all rental properties for expired rentals and update status
        rental_properties = Property.objects.filter(purpose='rent', status='sold')
        
        for property in rental_properties:
            if property.check_and_expire_rental():
                properties_made_available += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Property made available: {property.title}'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'- Expired rentals: {expired_count}\n'
                f'- Properties made available: {properties_made_available}'
            )
        )
