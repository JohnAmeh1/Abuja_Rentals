from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
import random
import string
import bcrypt
from django.conf import settings



class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    
    
    def __str__(self):
        return f"OTP for {self.user.email}"
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    
    @classmethod
    def create_otp(cls, user):
        """Create or update OTP for a user"""
        otp_code = cls.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=10)  
        otp, created = cls.objects.update_or_create(
            user=user,
            defaults={
                'code': bcrypt.hashpw(otp_code,  bcrypt.gensalt()),
                'expires_at': expires_at,
            }
        )
        return otp_code, created
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return timezone.now() < self.expires_at and not self.is_verified
    
    def verify(self, code):
        """Verify the OTP code"""
        if self.is_valid() and bcrypt.checkpw(code, self.code):
            self.delete()
            return True
        return False


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('tenant', 'Tenant/Looking to Rent'),
        ('agent', 'Real Estate Agent'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, blank=True, default='tenant')
    phone_number = models.CharField(max_length=15, blank=True)
    whatsapp_link = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def __str__(self):
        return f"{self.user.username}'s Profile"


class School(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200)
    logo = models.URLField(blank=True, null=True)
    description = models.TextField()
    next_resumption = models.DateField(blank=True)
    other_names = models.JSONField(default=list, blank=True)    
    
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, default='Abuja')
    state = models.CharField(max_length=100, default='FCT')
    zip_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    class Meta:
        indexes= [
            models.Index(fields=["next_resumption"]),
            models.Index(fields=["short_name"]),
            models.Index(fields=["name"]),
        ]

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('penthouse', 'Penthouse'),
        ('shop', 'Shop'),
        ('office', 'Office Space'),
        ('warehouse', 'Warehouse'),
        ('land', 'Land'),
        ('studio', 'Studio'),
        ('commercial', 'Commercial Building'),
    ]
    
    AMENITY_CHOICES = [
        ('swimming_pool', 'Swimming Pool'),
        ('gym', 'Gym/Fitness Center'),
        ('parking', 'Parking Space'),
        ('security', '24/7 Security'),
        ('garden', 'Garden'),
        ('balcony', 'Balcony/Terrace'),
        ('elevator', 'Elevator'),
        ('ac', 'Air Conditioning'),
        ('heating', 'Heating System'),
        ('laundry', 'Laundry Room'),
        ('storage', 'Storage Space'),
        ('concierge', 'Concierge Service'),
        ('pet_friendly', 'Pet Friendly'),
        ('furnished', 'Furnished'),
        ('wifi', 'High-Speed Internet'),
        ('cctv', 'CCTV Surveillance'),
    ]
    
    PURPOSE_CHOICES = [
        ('rent', 'For Rent'),
        ('sale', 'For Sale'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('draft', 'Draft'),
    ]
    
    CITIES = [
        ('gwarinpa', 'Gwarinpa'),
        ('jahi', 'Jahi'),
        ('wuse', 'Wuse'),
        ('wuye', 'Wuye'),
        ('apo', 'Apo'),
        ('dutse', 'Dutse'),
        ('kubwa', 'Kubwa'),
        ('bwari', 'Bwari'),
        ('gwagwalada', 'Gwagwalada'),
        ('lugbe', 'Lugbe'),
        ('kuje', 'Kuje'),
        ('kwali', 'Kwali'),
        ('abaji', 'Abaji'),
        ('maitama', 'Maitama'),
        ('asokoro', 'Asokoro'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name="properties", null=True, blank=True)
    
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, default='Abuja')
    state = models.CharField(max_length=100, default='FCT')
    zip_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    bedrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    bathrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    price = models.DecimalField(max_digits=12, decimal_places=2)
        
    rent_duration_months = models.PositiveIntegerField(default=12, blank=True, null=True)
    
    amenities = models.JSONField(default=list,blank=True)
    
    main_image = models.URLField(blank=True, null=True)
    images = models.JSONField(default=list, blank=True)

    furnished = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    serviced = models.BooleanField(default=False)
    
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['purpose', 'city', 'status']),
            models.Index(fields=['purpose', 'status']),
            models.Index(fields=['property_type']),
            models.Index(fields=['price']),
            models.Index(fields=['bedrooms']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['views']),
            models.Index(fields=['created_at']),
            models.Index(fields=['created_at', "-id"]),
            models.Index(fields=['status']),
            models.Index(fields=['school']),
            # models.Index(fields=['available']),
        ]

    
    def save(self, *args, **kwargs):        
        if self.purpose == 'rent' and not self.rent_duration_months:
            self.rent_duration_months = 12
        
        if self.status == 'available' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.get_property_type_display()} ({self.get_purpose_display()})"


@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        # Use get_or_create but don't overwrite existing profile
        profile, created_profile = UserProfile.objects.get_or_create(
            user=instance,
            defaults={'user_type': 'tenant'}  # Default only if creating new
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()



class PropertyVisit(models.Model):
    """Model to track scheduled property visits"""
    VISIT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('declined', 'Declined'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    visitor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_visits')
    visit_date = models.DateField()
    visit_time = models.TimeField()
    status = models.CharField(max_length=20, choices=VISIT_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    owner_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-visit_date', '-visit_time']
        verbose_name_plural = 'Property Visits'
    
    def __str__(self):
        return f"{self.visitor.username} - {self.property.title} on {self.visit_date}"


class Inquiry(models.Model):

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquires', null=True, blank=True)
    full_name   = models.CharField(max_length=150)
    phone       = models.CharField(max_length=30)
    email       = models.EmailField(blank=True)

    property_type = models.CharField(max_length=20, choices=Property.PROPERTY_TYPE_CHOICES, blank=True)
    purpose       = models.CharField(max_length=10, choices=Property.PURPOSE_CHOICES, blank=True)

    city = models.CharField(max_length=100, blank=True)

    budget_min = models.PositiveIntegerField(null=True, blank=True)
    budget_max = models.PositiveIntegerField(null=True, blank=True)

    bedrooms_min = models.PositiveSmallIntegerField(null=True, blank=True)
    bedrooms_max = models.PositiveSmallIntegerField(null=True, blank=True)

    bathrooms_min = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms_max = models.PositiveSmallIntegerField(null=True, blank=True)

    amenities = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)


    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inquiry'
        verbose_name_plural = 'Inquiries'
        indexes = [
            models.Index(fields=['created_at']),
        ]


    def __str__(self):
        return f"{self.full_name} — {self.property_type or 'any'} ({self.created_at:%d %b %Y})"

    def amenities_list(self):
        """Return amenities as a Python list."""
        return [a.strip() for a in self.amenities.split(',') if a.strip()]



class InquiryResponse(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inquires_responses")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="inquires_responses")
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="inquires_responses")
    created_at = models.DateTimeField(auto_now=True)
    opened = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['inquiry']),
            models.Index(fields=['agent']),
        ]


class SavedProperty(models.Model):
    """Model to track properties saved by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'property']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"

class AdminMessage(models.Model):
    """Model for admin messages to all users"""
    MESSAGE_TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('alert', 'Alert'),
        ('maintenance', 'Maintenance'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='info')
    is_active = models.BooleanField(default=True)
    show_to_all = models.BooleanField(default=True, help_text="Show to all non-admin users")
    show_to_owners = models.BooleanField(default=True)
    show_to_tenants = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True, help_text="Optional: Message will expire after this date")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Admin Messages'
    
    def __str__(self):
        return f"{self.title} ({self.get_message_type_display()})"
    
    def is_current(self):
        """Check if message is currently active"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def should_show_to_user(self, user):
        """Check if message should be shown to specific user"""
        if not self.is_current():
            return False
        
        # Don't show to message creator
        if user == self.created_by:
            return False
        
        # Don't show to admins unless explicitly allowed
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin':
            return False
        
        # Check user type permissions
        if hasattr(user, 'userprofile'):
            user_type = user.userprofile.user_type
            if user_type == 'agent' and not self.show_to_owners:
                return False
            if user_type == 'tenant' and not self.show_to_tenants:
                return False
        
        return True


class Report(models.Model):
    REASON_CHOICES = [
        ('fake_listing', 'Fake / Misleading Listing'),
        ('harassment', 'Harassment / Abusive Behavior'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    admin_action = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} by {self.reporter.username} - {self.get_reason_display()}"
