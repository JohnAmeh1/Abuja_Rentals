from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField


from .services.helper import (PURPOSE_CHOICES, PROPERTY_STATUS_CHOICES, USER_TYPE_CHOICES,
                                REASON_CHOICES, REPORT_STATUS_CHOICES, VISIT_STATUS_CHOICES,
                                MESSAGE_TYPE_CHOICES, AGENT_APP_STATUS_CHOICES,
                                NOTIFICATION_MESSAGE_TYPE_CHOICES, NOTIFICATION_MODE_CHOICES)
from .services.admin_message_service import AdminMessageService
from .services.inquiry_service import InquiryService
from .services.notification_service import NotificationService
from .services.otp_service import OTPService
from .services.property_service import PropertyService
from .services.user_service import UserProfileService

class OTP(OTPService, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp')
    code = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()


class UserProfile(UserProfileService, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, blank=True, default='tenant')
    phone_number = models.CharField(max_length=15, blank=True)
    whatsapp_number = models.CharField(max_length=255, blank=True)
    profile_picture = CloudinaryField('image', resource_type="image", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Country(models.Model):
    name = models.CharField(max_length=100)


class State(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name.capitalize()


class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.name.capitalize()


class Area(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name.capitalize()


class Location(models.Model):
    address = models.CharField(max_length=255, blank=True, default='')
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, related_name="locations")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    # point = gis_models.PointField()

    def __str__(self):
        if self.area:
            return f"{self.address}, {self.area.name}"
        return self.address


class School(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=200)
    next_resumption_start = models.DateField(blank=True, null=True)
    next_resumption_end = models.DateField(blank=True, null=True)
    semester_end = models.DateField(blank=True, null=True)

    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="schools", null=True)

    class Meta:
        indexes = [
            models.Index(fields=["short_name"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name + " (" + self.short_name + ")"

class PropertyCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

class PropertyType(models.Model):
    category = models.ForeignKey(
        PropertyCategory,
        on_delete=models.CASCADE,
        related_name="types"
    )

    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, null=True, unique=False)
    display_name = models.CharField(max_length=100)
    
    image = models.CharField(blank=True)
    
    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    verified = models.BooleanField(default=False)
    name = models.CharField(default="", max_length=50, null=True)

    preferred_purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    has_seen_welcome = models.BooleanField(default=False)
    has_shared_profile = models.BooleanField(default=False)

    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.CharField(max_length=200, blank=True)
    other_phones = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = CloudinaryField('image', resource_type="image", blank=True, null=True)
    logo  = CloudinaryField('image', resource_type="image", blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)

    def get_inquiry_queryset(self):
        qs = Inquiry.objects.filter(closed=False).exclude(
            user=self.user
        )
        qs = qs.select_related('user', 'school').order_by('-created_at')
        return qs

    def __str__(self):
        return f"Agent: {self.user.get_full_name() or self.user.username}"

class Property(PropertyService, models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    status = models.CharField(max_length=10, choices=PROPERTY_STATUS_CHOICES, default='draft')

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name="properties", null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="properties", null=True)

    bedrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    bathrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    rent_duration_months = models.PositiveIntegerField(default=12, blank=True, null=True)

    furnished = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    serviced = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)

    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
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
        ]
        
    def is_saved(self, user_id):
        return SavedProperty.objects.filter(property=self, user_id=user_id).exists()

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
        unique_together = ['visitor', 'property', 'visit_date']

    def __str__(self):
        return f"{self.visitor.username} - {self.property.title} on {self.visit_date}"


class Inquiry(InquiryService, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquires')
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True, related_name='inquires')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='inquires', null=True, blank=True)

    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, blank=True, null=True)
    budget_min = models.PositiveIntegerField(null=True, blank=True)
    budget_max = models.PositiveIntegerField(null=True, blank=True)
    bedrooms_min = models.PositiveSmallIntegerField(null=True, blank=True)
    bedrooms_max = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms_min = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms_max = models.PositiveSmallIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)

    furnished = models.BooleanField(default=False)
    shared = models.BooleanField(default=False)
    serviced = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inquiry'
        verbose_name_plural = 'Inquiries'
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        if self.property_type:
            return str(self.property_type)
        

class InquiryResponse(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="inquires_responses")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="inquires_responses")
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="inquires_responses")
    created_at = models.DateTimeField(auto_now_add=True)
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
            models.Index(fields=["property"]),
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.property.title}"


class AdminMessage(AdminMessageService, models.Model):
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

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.property and self.property.agent.user != self.reported_user:
            raise ValidationError("The reported property does not belong to the reported user.")

class Amenity(models.Model):
    name = models.CharField(max_length=20)
    display_name = models.CharField(max_length=30)
    icon = models.CharField(max_length=50, null=True, blank=True)

class PropertyAmenity(models.Model):
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="property_amenities")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="property_amenities")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['amenity', 'property'],
                name='unique_property_amenity'
            ),
        ]

    def __str__(self):
        return f"{self.amenity.display_name} — {self.property.title}"

class InquiryAmenity(models.Model):
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="inquiry_amenities")
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="inquiry_amenities")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['amenity', 'inquiry'],
                name='unique_inquiry_amenity'
            ),
        ]

    def __str__(self):
        return f"{self.amenity.display_name} — Inquiry #{self.inquiry.id}"

class InquiryCity(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='inquiries_city')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='inquiries_city')

    def __str__(self):
        return self.city.name.capitalize()


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image', resource_type="image", null=True, blank=True)
    order = models.IntegerField(default=0)
    test_url = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['property'])
        ]
        
class PropertyVideo(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='videos')
    video = CloudinaryField('video', resource_type="video", null=True, blank=True)
    youtube_link = models.URLField(null=True, blank=True)
    other_link = models.CharField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['property'])
        ]

class AgentAssignedSchools(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="assigned_schools")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="assigned_schools")

class AgentPreferredTypes(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="preferred_types")
    type = models.ForeignKey(PropertyType, on_delete=models.CASCADE, related_name="preferred_types")

class AgentAssignedCities(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="assigned_cities")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="assigned_cities")

class AgentApplication(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_application')
    status = models.CharField(max_length=10, choices=AGENT_APP_STATUS_CHOICES, default='pending')

    phone = models.CharField(max_length=20)
    bio = models.TextField(blank=True)
    experience = models.TextField(blank=True, help_text="How long have you been in real estate and in which areas?")
    areas_of_focus = models.JSONField(default=list, blank=True, help_text="Which cities do they primarily operate in")

    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_agent_applications'
    )
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Agent Application'
        verbose_name_plural = 'Agent Applications'

    def approve(self, reviewed_by):
        """Approve the application, elevate the user, create AgentProfile."""
        self.status = 'approved'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

        profile = self.user.userprofile
        profile.user_type = 'agent'
        profile.save(update_fields=['user_type'])

        agent_profile, created = AgentProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'bio': self.bio,
                'phone': self.phone,
            }
        )

        if created and self.areas_of_focus:
            cities = City.objects.filter(name__in=self.areas_of_focus)
            AgentAssignedCities.objects.bulk_create([
                AgentAssignedCities(agent=agent_profile, city=city)
                for city in cities
            ])
        return agent_profile

    def reject(self, reviewed_by, reason=''):
        """Reject the application."""
        self.status = 'rejected'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

    def __str__(self):
        return f"{self.user.username} — {self.get_status_display()}"

class Notification(NotificationService, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(choices=NOTIFICATION_MESSAGE_TYPE_CHOICES)
    mode = models.CharField(choices=NOTIFICATION_MODE_CHOICES, default='email')
    message = models.TextField()
    related_id = models.CharField(null=True, blank=True)
    sent = models.BooleanField(default=False)

    