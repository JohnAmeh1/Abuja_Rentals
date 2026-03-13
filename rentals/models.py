from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# from django.contrib.gis.db import models as gis_models

from .services.helper import (PURPOSE_CHOICES, PROPERTY_STATUS_CHOICES, USER_TYPE_CHOICES, REASON_CHOICES, REPORT_STATUS_CHOICES, VISIT_STATUS_CHOICES, MESSAGE_TYPE_CHOICES, AGENT_APP_STATUS_CHOICES)



class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp')
    code = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    

class UserProfile(models.Model):
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

class State(models.Model):
    name = models.CharField(max_length=100)

class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

class Area(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

class Location(models.Model):
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name="locations")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    # point = gis_models.PointField()
    
    def __str__(self):
        if self.city:
            return f"{self.address}, {self.city.name}"
        return self.address

class School(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200)
    next_resumption_start = models.DateField(blank=True, null=True)
    next_resumption_end = models.DateField(blank=True, null=True)
    semester_end = models.DateField(blank=True, null=True)
    
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="schools", null=True)
    
    class Meta:
        indexes= [
            models.Index(fields=["short_name"]),
            models.Index(fields=["name"]),
        ]
        
class SchoolAlias(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class PropertyType(models.Model):
    name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=50)

class Property(models.Model):    
    title = models.CharField(max_length=200)
    description = models.TextField()
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    status = models.CharField(max_length=10, choices=PROPERTY_STATUS_CHOICES, default='draft')
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name="properties", null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="properties", null=True)
    
    bedrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    bathrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    price = models.DecimalField(max_digits=12, decimal_places=2)
    rent_duration_months = models.PositiveIntegerField(default=12, blank=True, null=True)

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
            # models.Index(fields=['purpose', 'location__area', 'status']),
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

    
    def __str__(self):
        ptype = self.property_type.display_name if self.property_type else "Unknown"
        return f"{self.title} - {ptype} ({self.get_purpose_display()})"


@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        profile, created_profile = UserProfile.objects.get_or_create(
            user=instance,
            defaults={'user_type': 'tenant'}
        )



class PropertyVisit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    visitor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_visits')
    visit_date = models.DateField(blank=True, null=True)
    visit_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=VISIT_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    owner_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-visit_date']
        verbose_name_plural = 'Property Visits'
    
    def __str__(self):
        return f"{self.visitor.username} - {self.property.title} on {self.visit_date}"

class Inquiry(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquires')
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, blank=True, null=True)
    cities = models.JSONField(default=list, max_length=100, blank=True)

    budget_min = models.PositiveIntegerField(null=True, blank=True)
    budget_max = models.PositiveIntegerField(null=True, blank=True)
    bedrooms_min = models.PositiveSmallIntegerField(null=True, blank=True)
    bedrooms_max = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms_min = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms_max = models.PositiveSmallIntegerField(null=True, blank=True)

    amenities = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    furnished = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    serviced = models.BooleanField(default=False)
    
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='inquires', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    closed = models.BooleanField(default=False)


    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inquiry'
        verbose_name_plural = 'Inquiries'
        indexes = [
            models.Index(fields=['created_at']),
        ]

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'property']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["user"]),
        ]
    
    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"

class AdminMessage(models.Model):
    """Model for admin messages to all users"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='info')
    is_active = models.BooleanField(default=True)
    show_to_all = models.BooleanField(default=True, help_text="Show to all non-admin users")
    show_to_agents = models.BooleanField(default=True)
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

class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    admin_action = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} by {self.reporter.username} - {self.get_reason_display()}"

class Amenity(models.Model):
    name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=30)

class PropertyAmenities(models.Model):
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="property_amenities")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="property_amenities", null=True)
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="inquiry_amenities", null=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['amenity', 'property'],
                name='unique_property_amenity'
            ),
            models.UniqueConstraint(
                fields=['amenity', 'inquiry'],
                name='unique_inquiry_amenity'
            ),
        ]

class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    verified = models.BooleanField(default=False)

    assigned_cities  = models.JSONField(default=list, blank=True, null=True)
    assigned_schools = models.ManyToManyField('School', blank=True,  related_name='agents')

    preferred_types   = models.JSONField(default=list, blank=True, null=True)
    preferred_purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, blank=True, null=True)

    bio     = models.TextField(blank=True)
    phone   = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Agent: {self.user.get_full_name() or self.user.username}"

class AgentApplication(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_application')
    status           = models.CharField(max_length=10, choices=AGENT_APP_STATUS_CHOICES, default='pending')

    phone            = models.CharField(max_length=20)
    bio              = models.TextField(blank=True)
    experience       = models.TextField(blank=True, help_text="How long have you been in real estate and in which areas?")
    areas_of_focus   = models.JSONField(default=list, blank=True, help_text="Which cities do they primarily operate in")

    reviewed_at      = models.DateTimeField(null=True, blank=True)
    reviewed_by      = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_agent_applications'
    )
    rejection_reason = models.TextField(blank=True)

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Application'
        verbose_name_plural = 'Agent Applications'

    def __str__(self):
        return f"{self.user.username} — {self.get_status_display()}"

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    # image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to="property_images/")
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['property'])
        ]
