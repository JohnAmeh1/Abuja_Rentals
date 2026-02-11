from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
import os
from dateutil.relativedelta import relativedelta
from django.db import transaction


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('tenant', 'Tenant/Looking to Rent'),
        ('agent', 'Real Estate Agent'),
        ('student', 'Student'),
        # ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, blank=True, default='tenant')
    phone_number = models.CharField(max_length=15, blank=True)
    whatsapp_link = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet - ₦{self.balance}"
    
    def deposit(self, amount):
        self.balance += amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            transaction_type='deposit',
            amount=amount,
            description='Deposit to wallet'
        )
    
    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            Transaction.objects.create(
                wallet=self,
                transaction_type='withdrawal',
                amount=amount,
                description='Withdrawal from wallet'
            )
            return True
        return False


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
        ('commercial', 'Commercial Building'),
    ]
    
    PURPOSE_CHOICES = [
        ('rent', 'For Rent'),
        ('sale', 'For Sale'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('sold', 'Sold/Rented'),
        ('draft', 'Draft'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    
    # Location
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, default='Abuja')
    state = models.CharField(max_length=100, default='FCT')
    zip_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Property Details
    bedrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    bathrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Financial Details
    price = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Rent duration field
    rent_duration_months = models.PositiveIntegerField(default=12, blank=True, null=True)
    
    # Amenities
    amenities = models.TextField(blank=True)
    
    # Images
    main_image = models.ImageField(upload_to='properties/main/')
    image_1 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_5 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_6 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_7 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_8 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_9 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    
    # Metadata
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    # Sale/Rental tracking
    sold_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_properties')
    rented_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rented_properties')
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sold_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate platform fee (5% of price)
        self.platform_fee = self.price * Decimal('0.05')
        
        # Calculate net amount (price minus platform fee)
        self.net_amount = self.price - self.platform_fee
        
        # Set default rent duration for rental properties
        if self.purpose == 'rent' and not self.rent_duration_months:
            self.rent_duration_months = 12
        
        # If property is being published for the first time
        if self.status == 'available' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_amenities_list(self):
        if self.amenities:
            return [amenity.strip() for amenity in self.amenities.split(',')]
        return []
    
    def set_amenities(self, amenities_list):
        self.amenities = ','.join(amenities_list)
    
    def get_additional_images(self):
        images = []
        for field_name in ['image_1', 'image_2', 'image_3', 'image_4', 'image_5', 'image_6', 'image_7', 'image_8', 'image_9']:
            image_field = getattr(self, field_name)
            if image_field:
                images.append(image_field)
        return images
    
    def check_and_expire_rental(self):
        """
        Check if this property has any expired rentals and update status to available.
        Returns True if property was made available, False otherwise.
        """
        if self.purpose != 'rent' or self.status != 'sold':
            return False
        
        # Get active rentals for this property
        active_rentals = self.rentals.filter(is_active=True)
        
        # Check if any are expired
        today = timezone.now().date()
        all_expired = True
        
        for rental in active_rentals:
            if rental.check_and_update_status():
                # Rental was expired and marked inactive
                pass
            else:
                # At least one rental is still active
                all_expired = False
        
        # If all rentals are expired/inactive, make property available again
        if all_expired and active_rentals.exists():
            self.status = 'available'
            self.rented_to = None
            self.save(update_fields=['status', 'rented_to'])
            return True
        
        return False
    
    def __str__(self):
        return f"{self.title} - {self.get_property_type_display()} ({self.get_purpose_display()})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('property_sale', 'Property Sale'),
        ('property_purchase', 'Property Purchase'),
        ('rental_payment', 'Rental Payment'),
        ('platform_fee', 'Platform Fee'),
        ('refund', 'Refund'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # Optional property reference for tracking property-related transactions
    related_property_id = models.IntegerField(null=True, blank=True)
    related_property_title = models.CharField(max_length=200, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.reference:
            import uuid
            self.reference = f"TRX-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - ₦{self.amount}"

        
@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        # Use get_or_create but don't overwrite existing profile
        profile, created_profile = UserProfile.objects.get_or_create(
            user=instance,
            defaults={'user_type': 'tenant'}  # Default only if creating new
        )
        # If profile already exists (created by form), don't overwrite it
        Wallet.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
    
    if not hasattr(instance, 'wallet'):
        Wallet.objects.create(user=instance)
    else:
        instance.wallet.save()


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


class PropertyInquiry(models.Model):
    """Model to track property inquiries/contact messages"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_inquiries')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Property Inquiries'
    
    def __str__(self):
        return f"{self.name} - {self.property.title}"


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


class PropertyOwnership(models.Model):
    """Model to track property ownership after purchase"""
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='ownership')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_properties')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)
    ownership_document = models.FileField(upload_to='ownership_docs/', null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Property Ownerships'
    
    def __str__(self):
        return f"{self.owner.username} owns {self.property.title}"


class PropertyRental(models.Model):
    """Model to track property rentals"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rentals')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_rentals')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    deposit = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.username} rents {self.property.title}"

    def check_and_update_status(self):
        """
        Check if rental has expired and update is_active accordingly.
        Also triggers property status update if needed.
        Returns True if rental was expired, False otherwise.
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.is_active and self.end_date and self.end_date < today:
            self.is_active = False
            self.save(update_fields=['is_active'])
            
            # Trigger property status check
            if self.property:
                self.property.check_and_expire_rental()
            
            return True
        return False

    def is_expired(self):
        from django.utils import timezone
        return bool(self.end_date and self.end_date < timezone.now().date())

    def days_left(self):
        """Return number of days left until end_date (int) or None if end_date missing."""
        from django.utils import timezone
        if not self.start_date or not self.end_date:
            return None
        today = timezone.now().date()
        try:
            total = (self.end_date - self.start_date).days
            passed = (today - self.start_date).days
            # If today is before start_date, days left is full term plus days until start
            if passed < 0:
                return int(total + abs(passed))
            return int(total - passed)
        except Exception:
            return None

    def total_days(self):
        """Return total number of days for this rental period (end_date - start_date) or None."""
        if not self.start_date or not self.end_date:
            return None
        try:
            # Inclusive term: include the end date as part of the rental term
            return int((self.end_date - self.start_date).days) + 1
        except Exception:
            return None

    def renewal_allowed(self, grace_days=2):
        """Return True if renewal is allowed within `grace_days` before expiry (including same-day)."""
        days = self.days_left()
        if days is None:
            return False
        return 0 <= days <= int(grace_days)

    def renew(self, months=None, charge_amount=None):
        """Extend the rental by `months` (defaults to property's rent_duration_months).

        This method does NOT charge wallets; it only updates dates and totals.
        Returns the new end_date.
        """
        if months is None:
            months = int(self.property.rent_duration_months or 0)
        if months <= 0:
            return self.end_date

        # Use relativedelta for calendar-accurate addition
        new_end = self.end_date + relativedelta(months=months)
        self.end_date = new_end
        self.is_active = True
        
        # Update property status back to sold/rented if it was made available
        if self.property.status == 'available':
            self.property.status = 'sold'
            self.property.rented_to = self.tenant
            self.property.save(update_fields=['status', 'rented_to'])
        
        self.save(update_fields=['end_date', 'is_active'])
        return self.end_date

    def term_info(self, today=None):
        """Return a dict with term-related info:
        - total_days: inclusive days between start and end
        - starts_in: days until start (if in future)
        - days_passed: days since start (0 if not started)
        - days_until_end: days until end_date (0 if end date is today, negative if expired)
        - days_remaining: same as days_until_end for display (None if unknown)
        - expired_days: positive int if expired, else 0
        - renewal_allowed: True if on or after end date (days_until_end <= 0)
        - status: one of 'upcoming', 'active', 'expired', 'unknown'
        """
        from django.utils import timezone
        if today is None:
            today = timezone.now().date()

        info = {
            'total_days': None,
            'starts_in': None,
            'days_passed': None,
            'days_until_end': None,
            'days_remaining': None,
            'expired_days': None,
            'renewal_allowed': False,
            'status': 'unknown',
        }

        if not self.start_date or not self.end_date:
            return info

        try:
            total_days = (self.end_date - self.start_date).days + 1
            days_until_start = (self.start_date - today).days
            days_passed = (today - self.start_date).days if today >= self.start_date else 0
            days_until_end = (self.end_date - today).days

            info['total_days'] = int(total_days)
            info['days_passed'] = int(days_passed)
            info['days_until_end'] = int(days_until_end)

            if today < self.start_date:
                info['status'] = 'upcoming'
                info['starts_in'] = int(days_until_start)
                info['days_remaining'] = int(total_days)
                info['expired_days'] = 0
                info['renewal_allowed'] = False
            elif self.start_date <= today <= self.end_date:
                info['status'] = 'active'
                info['starts_in'] = 0
                info['days_remaining'] = int(days_until_end)
                info['expired_days'] = 0
                # Allow renewal on end date (days_until_end == 0) or after
                info['renewal_allowed'] = (days_until_end <= 0)
            else:
                # today > end_date
                info['status'] = 'expired'
                expired = (today - self.end_date).days
                info['expired_days'] = int(expired)
                info['days_remaining'] = -int(expired)
                info['renewal_allowed'] = True

            return info
        except Exception:
            return info


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class StudentProperty(models.Model):
    # Property Type Choices
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('self_contain', 'Self Contain'),
        
    ]
    
    UNIVERSITY_CHOICES = [
        ('university_of_abuja', 'University of Abuja'),
        ('nigerian_defence_academy', 'Nigerian Defence Academy'),
        
        ('other', 'Other'),
    ]
    # Purpose Choices
    PURPOSE_CHOICES = [
        ('rent', 'For Rent'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('available', 'Available'),      # When admin approves
        ('rented', 'Rented'),
    ]
    
    # Rent Duration Choices (in months)
    RENT_DURATION_CHOICES = [
        (1, '1 Month'),
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '1 Year'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Location Information
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    
    university = models.CharField(
        max_length=50, 
        choices=UNIVERSITY_CHOICES,
        blank=True, 
        null=True,
        help_text="Nearest property to the university."
    )
    
    # Property Details
    bedrooms = models.IntegerField(blank=True, null=True)
    bathrooms = models.IntegerField(blank=True, null=True)
    area_sqft = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Financial Information
    price = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Rent Information
    rent_duration_months = models.IntegerField(choices=RENT_DURATION_CHOICES, blank=True, null=True)
    
    # Amenities (stored as comma-separated string or use ManyToMany if separate table)
    amenities = models.TextField(blank=True, null=True)  # Could use JSONField if using PostgreSQL
    
    # Images
    main_image = models.ImageField(upload_to='properties/main/')
    image_1 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_5 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_6 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_7 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_8 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    image_9 = models.ImageField(upload_to='properties/additional/', blank=True, null=True)
    
    # Flags and Counters
    is_featured = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    sold_at = models.DateTimeField(blank=True, null=True)
    
    # Relationships
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_properties_created')
    rented_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='student_rented_properties')
    
    class Meta:
        db_table = 'student_property'  # Explicit table name
        ordering = ['-created_at']
        verbose_name = 'Student Property'
        verbose_name_plural = 'Student Properties'
        
    def __str__(self):
        uni_display = f" near {self.get_university_display()}" if self.university else ""
        return f"{self.title}{uni_display} - {self.get_property_type_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate platform fee (5%) and net amount before saving
        if self.price and self.platform_fee == 0:
            self.platform_fee = self.price * 0.05
            self.net_amount = self.price * 0.95
        
        # Set published_at if status changes to active
        if self.status == 'active' and not self.published_at:
            self.published_at = timezone.now()

        # Set sold_at if status changes to rented
        if self.status == 'rented' and not self.sold_at:
            self.sold_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_amenities_list(self):
        """Convert amenities string to list"""
        if self.amenities:
            # Assuming amenities are stored as comma-separated values
            return [amenity.strip() for amenity in self.amenities.split(',')]
        return []
    
    def set_amenities(self, amenities_list):
        """Convert amenities list to string"""
        self.amenities = ','.join(amenities_list) if amenities_list else ''
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('student_property_detail', args=[str(self.id)])
    
    def get_formatted_price(self):
        """Return formatted price with Naira symbol"""
        return f"₦{self.price:,.2f}"
    
    def get_formatted_net_amount(self):
        """Return formatted net amount with Naira symbol"""
        return f"₦{self.net_amount:,.2f}"
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def mark_as_featured(self):
        """Mark property as featured"""
        self.is_featured = True
        self.save(update_fields=['is_featured'])
    
    def mark_as_sold(self, sale_price=None):
        """Mark property as sold"""
        self.status = 'sold'
        if sale_price:
            self.sale_price = sale_price
        self.sold_at = timezone.now()
        self.save()
    
    def mark_as_rented(self, user):
        """Mark property as rented to a specific user"""
        self.status = 'rented'
        self.rented_to = user
        self.save()
        
        
# Add this to your models.py after the StudentProperty model

class StudentPropertyRental(models.Model):
    """Model to track student property rentals"""
    property = models.ForeignKey(StudentProperty, on_delete=models.CASCADE, related_name='student_rentals')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_tenant_rentals')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Property Rental'
        verbose_name_plural = 'Student Property Rentals'
    
    def __str__(self):
        return f"{self.tenant.username} rents {self.property.title}"

    def check_and_update_status(self):
        """Check if rental has expired and update is_active accordingly."""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.is_active and self.end_date and self.end_date < today:
            self.is_active = False
            self.save(update_fields=['is_active'])
            
            # Trigger property status check
            if self.property:
                self.property.check_and_expire_rental()
            
            return True
        return False

    def is_expired(self):
        from django.utils import timezone
        return bool(self.end_date and self.end_date < timezone.now().date())

    def days_left(self):
        """Return number of days left until end_date (int) or None if end_date missing."""
        from django.utils import timezone
        if not self.start_date or not self.end_date:
            return None
        today = timezone.now().date()
        try:
            total = (self.end_date - self.start_date).days
            passed = (today - self.start_date).days
            if passed < 0:
                return int(total + abs(passed))
            return int(total - passed)
        except Exception:
            return None

    def total_days(self):
        """Return total number of days for this rental period."""
        if not self.start_date or not self.end_date:
            return None
        try:
            return int((self.end_date - self.start_date).days) + 1
        except Exception:
            return None

    def renewal_allowed(self, grace_days=2):
        """Return True if renewal is allowed within grace_days before expiry."""
        days = self.days_left()
        if days is None:
            return False
        return 0 <= days <= int(grace_days)

    def renew(self, months=None):
        """Extend the rental by months (defaults to property's rent_duration_months)."""
        if months is None:
            months = int(self.property.rent_duration_months or 0)
        if months <= 0:
            return self.end_date

        from dateutil.relativedelta import relativedelta
        new_end = self.end_date + relativedelta(months=months)
        self.end_date = new_end
        self.is_active = True
        
        # Update property status back to rented if it was made available
        if self.property.status == 'available':
            self.property.status = 'rented'
            self.property.rented_to = self.tenant
            self.property.save(update_fields=['status', 'rented_to'])
        
        self.save(update_fields=['end_date', 'is_active'])
        return self.end_date

    def term_info(self, today=None):
        """Return a dict with term-related info."""
        from django.utils import timezone
        if today is None:
            today = timezone.now().date()

        info = {
            'total_days': None,
            'starts_in': None,
            'days_passed': None,
            'days_until_end': None,
            'days_remaining': None,
            'expired_days': None,
            'renewal_allowed': False,
            'status': 'unknown',
        }

        if not self.start_date or not self.end_date:
            return info

        try:
            total_days = (self.end_date - self.start_date).days + 1
            days_until_start = (self.start_date - today).days
            days_passed = (today - self.start_date).days if today >= self.start_date else 0
            days_until_end = (self.end_date - today).days

            info['total_days'] = int(total_days)
            info['days_passed'] = int(days_passed)
            info['days_until_end'] = int(days_until_end)

            if today < self.start_date:
                info['status'] = 'upcoming'
                info['starts_in'] = int(days_until_start)
                info['days_remaining'] = int(total_days)
                info['expired_days'] = 0
                info['renewal_allowed'] = False
            elif self.start_date <= today <= self.end_date:
                info['status'] = 'active'
                info['starts_in'] = 0
                info['days_remaining'] = int(days_until_end)
                info['expired_days'] = 0
                info['renewal_allowed'] = (days_until_end <= 0)
            else:
                info['status'] = 'expired'
                expired = (today - self.end_date).days
                info['expired_days'] = int(expired)
                info['days_remaining'] = -int(expired)
                info['renewal_allowed'] = True

            return info
        except Exception:
            return info


# Also add this method to StudentProperty model
def check_and_expire_rental(self):
    """Check if this student property has any expired rentals and update status."""
    if self.purpose != 'rent' or self.status != 'rented':
        return False
    
    # Get active rentals for this property
    active_rentals = self.student_rentals.filter(is_active=True)
    
    # Check if any are expired
    from django.utils import timezone
    today = timezone.now().date()
    all_expired = True
    
    for rental in active_rentals:
        if rental.check_and_update_status():
            pass
        else:
            all_expired = False
    
    # If all rentals are expired/inactive, make property available again
    if all_expired and active_rentals.exists():
        self.status = 'available'
        self.rented_to = None
        self.save(update_fields=['status', 'rented_to'])
        return True
    
    return False

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
        ('payment_issue', 'Payment / Refund Issue'),
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