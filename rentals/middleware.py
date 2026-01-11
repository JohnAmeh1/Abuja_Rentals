# Save this file as: yourapp/middleware.py

from django.utils import timezone
from django.core.cache import cache
from .models import PropertyRental

class RentalExpiryMiddleware:
    """
    Middleware to check and expire rentals periodically.
    Uses caching to avoid checking on every request.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check rentals only once every 10 minutes using cache
        cache_key = 'rental_expiry_last_check'
        last_check = cache.get(cache_key)
        
        if last_check is None:
            # First time or cache expired, check rentals
            self.check_expired_rentals()
            # Set cache for 10 minutes (600 seconds)
            cache.set(cache_key, timezone.now(), 600)
        
        response = self.get_response(request)
        return response
    
    def check_expired_rentals(self):
        """Check and update expired rentals and their property statuses."""
        today = timezone.now().date()
        
        # Get all active rentals
        active_rentals = PropertyRental.objects.filter(is_active=True).select_related('property')
        
        for rental in active_rentals:
            # This will update rental status and property status if needed
            try:
                rental.check_and_update_status()
            except Exception as e:
                # Log error but don't break the request
                print(f"Error checking rental {rental.id}: {str(e)}")
                continue


# Add this to your settings.py MIDDLEWARE list:
# MIDDLEWARE = [
#     ...
#     'yourapp.middleware.RentalExpiryMiddleware',  # Add this line
#     ...
# ]