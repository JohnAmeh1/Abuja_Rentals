from django.utils import timezone


def save(self, *args, **kwargs):        
    if self.purpose == 'rent' and not self.rent_duration_months:
        self.rent_duration_months = 12
    
    if self.status == 'available' and not self.published_at:
        self.published_at = timezone.now()
    
    self.save(*args, **kwargs)

