from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
# from .models import UserProfile, Property
from django.core.exceptions import ValidationError
from .models import UserProfile, Property
from .models import Report
from dateutil.relativedelta import relativedelta
import json
from django.utils import timezone

from decimal import Decimal

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Email address'
    }))
    
    USER_TYPE_CHOICES = [
        ('tenant', 'Tenant/Looking to Rent'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'space-y-2'}),
        required=True,
        initial='tenant'
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Phone number'
        })
    )
    
    # Add additional fields for profile
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Address (optional)'
        })
    )
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Tell us about yourself...',
            'rows': 3
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'address', 'bio', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'first_name', 'last_name']:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': self.fields[field_name].label
            })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Password'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm Password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        user_type = self.cleaned_data.get('user_type', 'tenant')
        print(f"DEBUG Form Save: user_type = {user_type}")
        
        if commit:
            user.save()
            
            UserProfile.objects.filter(user=user).delete()
            
            user_profile = UserProfile.objects.create(
                user=user,
                user_type=user_type,
                phone_number=self.cleaned_data.get('phone_number', ''),
                address=self.cleaned_data.get('address', ''),
                bio=self.cleaned_data.get('bio', '')
            )
            
            
        return user

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Password'
    }))
    
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
    }))

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Email Address'
        })
    )

    whatsapp_link = forms.CharField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'WhatsApp link (https://...)'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['user_type', 'phone_number', 'whatsapp_link', 'address', 'bio']
        widgets = {
            'user_type': forms.RadioSelect(attrs={'class': 'space-y-2'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Phone Number'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Full Address'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Tell us about yourself...',
                'rows': 4
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            # Pre-fill whatsapp link if available
            try:
                self.fields['whatsapp_link'].initial = self.user.userprofile.whatsapp_link
            except Exception:
                pass
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.save()
        
        if commit:
            profile.save()
        
        return profile
    

class PropertyForm(forms.ModelForm):
    # Custom field for amenities as checkboxes
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
    
    amenities = forms.MultipleChoiceField(
        choices=AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'}),
        required=False
    )
    
    rent_duration_display = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 cursor-not-allowed',
            'readonly': 'readonly',
            'id': 'rent-duration-display'
        }),
        label='Rent Duration'
    )
    # Hidden numeric field to store months for the backend
    rent_duration_months = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'rent-duration-input'})
    )
    
    images = forms.CharField(
    required=False,
    widget=forms.Textarea(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
        'placeholder': 'Enter one image URL per line'
        })
    )

    
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'purpose',
            'city', 'state', 'zip_code', 'latitude', 'longitude',
            'bedrooms', 'bathrooms', 'area_sqft', 'price',
            'rent_duration_display',  # Add this field
            'rent_duration_months',
            'main_image', 'images',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'e.g., Luxury 3-Bedroom Apartment in Maitama'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Describe your property in detail...',
                'rows': 4
            }),
            'property_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent property-type-select',
                'id': 'property-type-select'
            }),
            'purpose': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Full address'
            }),
            'city': forms.Select(choices=[
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
            ], attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'value': 'FCT'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Postal code'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Latitude (optional)',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Longitude (optional)',
                'step': 'any'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent bedrooms-input',
                'id': 'bedrooms-input',
                'min': '0'
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'min': '0'
            }),
            'area_sqft': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
                'placeholder': 'Area in square feet',
                'step': '0.01'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent price-input',
                'id': 'price-input',
                'placeholder': 'e.g., 500000',
                'step': '0.01'
            }),
            'main_image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make bedrooms, bathrooms, and area_sqft optional
        self.fields['bedrooms'].required = False
        self.fields['bathrooms'].required = False
        self.fields['area_sqft'].required = False
        
        if self.instance and self.instance.amenities:
            self.fields['amenities'].initial = self.instance.get_amenities_list()
        
        # Set initial value for rent_duration_display based on purpose
        if self.initial.get('purpose') == 'rent':
            self.fields['rent_duration_display'].initial = '1 Year (Standard)'
            self.fields['rent_duration_display'].widget.attrs['value'] = '1 Year (Standard)'
            # default months
            if 'rent_duration_months' in self.fields:
                self.fields['rent_duration_months'].initial = 12

        # If instance exists, prefill rent_duration_months
        if self.instance and getattr(self.instance, 'rent_duration_months', None):
            if 'rent_duration_months' in self.fields:
                self.fields['rent_duration_months'].initial = self.instance.rent_duration_months
    
    def clean(self):
        cleaned_data = super().clean()
        purpose = cleaned_data.get('purpose')
        
        # Auto-set rent duration display based on purpose
        if purpose == 'rent':
            cleaned_data['rent_duration_display'] = '1 Year (Standard)'
        
        return cleaned_data
    
    def save(self, commit=True):
        property_obj = super().save(commit=False)
        
        # Handle amenities
        if 'amenities' in self.cleaned_data:
            property_obj.set_amenities(self.cleaned_data['amenities'])
        
        # Save rent duration months if provided
        months = self.cleaned_data.get('rent_duration_months')
        if months:
            try:
                property_obj.rent_duration_months = int(months)
            except Exception:
                pass

        if commit:
            property_obj.save()
        
        return property_obj


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'message']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'rows': 4,
                'placeholder': 'Describe the issue in detail (optional)'
            })
        }

class PropertySearchForm(forms.Form):
    property_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Property.PROPERTY_TYPE_CHOICES,
        required=False,
    )
    
    purpose = forms.ChoiceField(
        choices=[('', 'All Purposes')] + Property.PURPOSE_CHOICES,
        required=False,
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Property.STATUS_CHOICES,
        required=False,
    )
    city = forms.ChoiceField(
        choices=[('', 'All Locations')] + [
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
        ],
        required=False,
    )
    
    search = forms.CharField(
        required=False,
    )
    
    amenities = forms.MultipleChoiceField(
        choices=PropertyForm.AMENITY_CHOICES,
        required=False
    )




class AdminMessageForm(forms.Form):
    """Form for creating admin messages (using Form instead of ModelForm)"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Message Title'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Enter your message here...',
            'rows': 5
        })
    )
    
    MESSAGE_TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('alert', 'Alert'),
        ('maintenance', 'Maintenance'),
    ]
    
    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    start_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'type': 'datetime-local'
        })
    )
    
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'type': 'datetime-local'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    show_to_all = forms.BooleanField(
        required=False,
        initial=True,
        label="Show to all non-admin users",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    show_to_owners = forms.BooleanField(
        required=False,
        initial=True,
        label="Show to property owners",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    show_to_tenants = forms.BooleanField(
        required=False,
        initial=True,
        label="Show to tenants",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value for start_date to current time if not provided
        if not self.initial.get('start_date'):
            current_time = timezone.now()
            # Format for datetime-local input
            formatted_time = current_time.strftime('%Y-%m-%dT%H:%M')
            self.fields['start_date'].initial = formatted_time
