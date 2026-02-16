from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
# from .models import UserProfile, Property
from django.core.exceptions import ValidationError
from .models import UserProfile, Property
from .models import Report, StudentProperty
from dateutil.relativedelta import relativedelta
import json
from decimal import Decimal

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Email address'
    }))
    
    USER_TYPE_CHOICES = [
        ('tenant', 'Tenant/Looking to Rent'),
        ('owner', 'Property Owner/Landlord'),
        ('student', 'Student'),
        # ('agent', 'Real Estate Agent'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'space-y-2'}),
        required=True,
        initial='tenant'  # Set default initial value
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
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
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
    

class StudentPropertyForm(forms.ModelForm):
    # Additional image fields (these should match your model)
    image_1 = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        'accept': 'image/*'
    }))
    image_2 = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        'accept': 'image/*'
    }))
    image_3 = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        'accept': 'image/*'
    }))
    image_4 = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        'accept': 'image/*'
    }))
    image_5 = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        'accept': 'image/*'
    }))
    
    # Amenities as checkboxes - UPDATE THIS
    AMENITY_CHOICES = [
        ('wifi', 'WiFi'),
        ('parking', 'Parking'),
        ('pool', 'Swimming Pool'),
        ('gym', 'Gym'),
        ('air_conditioning', 'Air Conditioning'),
        ('heating', 'Heating'),
        ('laundry', 'Laundry'),
        ('security', '24/7 Security'),
        ('furnished', 'Furnished'),
        ('balcony', 'Balcony'),
        ('water', 'Constant Water'),
        ('electricity', '24/7 Electricity'),
        ('generator', 'Generator'),
        ('cctv', 'CCTV'),
        ('study_room', 'Study Room'),
        ('kitchen', 'Kitchen'),
    ]
    
    
    
    university = forms.ChoiceField(
        choices=StudentProperty.UNIVERSITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        help_text="Select the nearest university"
    )
    custom_university = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mt-2 hidden',
            'placeholder': 'Enter university name'
        })
    )
    amenities = forms.MultipleChoiceField(
        choices=AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'mr-2'
        }),
        required=False
    )
    
    class Meta:
        model = StudentProperty
        fields = [
            'title', 'description', 'property_type', 'purpose',
            'city', 'state', 'zip_code', 'university',
            'bedrooms', 'bathrooms', 'area_sqft', 'price', 
            'platform_fee', 'net_amount', 'rent_duration_months', 
            'amenities', 'main_image', 'image_1', 'image_2', 
            'image_3', 'image_4', 'image_5', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Spacious 3-Bedroom Apartment'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Describe the property, location, features, etc.'
            }),
            'property_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'purpose': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Abuja'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., FCT'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., 900001'
            }),
            'university': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'id': 'university_select'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': 0,
                'placeholder': '0'
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': 0,
                'placeholder': '0'
            }),
            'area_sqft': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': 0,
                'placeholder': 'e.g., 1200'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': 0,
                'step': '0.01',
                'placeholder': 'Enter amount in Naira'
            }),
            'platform_fee': forms.HiddenInput(),
            'net_amount': forms.HiddenInput(),
            'rent_duration_months': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'main_image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600 rounded focus:ring-blue-500'
            }),
            # 'status': forms.HiddenInput(),
            
        }
    
    def __init__(self, *args, **kwargs):
        # Pop user from kwargs before calling super
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make platform_fee and net_amount hidden (auto-calculated)
        # Add these fields if they don't exist
        self.fields['platform_fee'] = forms.DecimalField(
            widget=forms.HiddenInput(), 
            required=False,
            initial=0
        )
        self.fields['net_amount'] = forms.DecimalField(
            widget=forms.HiddenInput(), 
            required=False,
            initial=0
        )
        
        # Set initial amenities from instance
        if self.instance and self.instance.amenities:
            self.fields['amenities'].initial = self.instance.get_amenities_list()
        
        # Set initial university value
        if self.instance and self.instance.university:
            if self.instance.university.startswith('custom_'):
                self.initial['university'] = 'other'
                self.initial['custom_university'] = self.instance.university.replace('custom_', '')
            else:
                self.initial['university'] = self.instance.university
        
        # Set default purpose to 'rent' for student properties
        if not self.instance.pk:  # Only for new properties
            self.initial['purpose'] = 'rent'
            
        # Set default rent duration
        if not self.instance.pk:
            self.initial['rent_duration_months'] = 12

    def clean(self):
        cleaned_data = super().clean()
        university = cleaned_data.get('university')
        custom_university = cleaned_data.get('custom_university')
        
        # Handle "Other" university option
        if university == 'other' and custom_university:
            cleaned_data['university'] = f"custom_{custom_university}"
        elif university == 'other' and not custom_university:
            self.add_error('custom_university', 'Please enter the university name')
        
        # Calculate platform fee (2%) and net amount
        price = cleaned_data.get('price')
        if price:
            from decimal import Decimal
            if not isinstance(price, Decimal):
                try:
                    price = Decimal(str(price))
                except:
                    self.add_error('price', 'Please enter a valid price')
                    return cleaned_data
            
            cleaned_data['platform_fee'] = price * Decimal('0.02')
            cleaned_data['net_amount'] = price * Decimal('0.98')
        
        # Convert amenities list to comma-separated string
        amenities_list = cleaned_data.get('amenities', [])
        if amenities_list and isinstance(amenities_list, list):
            cleaned_data['amenities'] = ','.join(amenities_list)
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle university field
        university = self.cleaned_data.get('university')
        if university:
            instance.university = university
        
        # Set amenities if not already set in clean()
        if 'amenities' in self.cleaned_data:
            amenities = self.cleaned_data['amenities']
            if isinstance(amenities, list):
                instance.set_amenities(amenities)
            elif isinstance(amenities, str) and amenities:
                # If it's already a string from clean(), just assign it
                instance.amenities = amenities
        
        if commit:
            instance.save()
        
        return instance
    

class StudentPropertySearchForm(forms.Form):
    # Universities dropdown - will be populated from StudentProperty.UNIVERSITY_CHOICES
    university = forms.ChoiceField(
        choices=[('', 'All Universities')] + list(StudentProperty.UNIVERSITY_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    property_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(StudentProperty.PROPERTY_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    purpose = forms.ChoiceField(
        choices=[('', 'All Purposes')] + list(StudentProperty.PURPOSE_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    city = forms.ChoiceField(
        choices=[('', 'All Cities')],  # Will be populated in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Search by title, location, or university...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically populate cities from existing student properties
        try:
            cities = StudentProperty.objects.values_list('city', flat=True).distinct().order_by('city')
            city_choices = [('', 'All Cities')] + [(city, city.title()) for city in cities if city]
            self.fields['city'].choices = city_choices
        except Exception:
            # If database table doesn't exist yet or other error
            self.fields['city'].choices = [('', 'All Cities')]

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
    
    # def save(self, commit=True):
    #     property_obj = super().save(commit=False)
    #     property_obj.set_amenities(self.cleaned_data['amenities'])
        
    #     if commit:
    #         property_obj.save()
        
    #     return property_obj
    
    # In forms.py, update the save method in PropertyForm
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
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    purpose = forms.ChoiceField(
        choices=[('', 'All Purposes')] + Property.PURPOSE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Property.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
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
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent',
            'placeholder': 'Search by title or address...'
        })
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
            from django.utils import timezone
            current_time = timezone.now()
            # Format for datetime-local input
            formatted_time = current_time.strftime('%Y-%m-%dT%H:%M')
            self.fields['start_date'].initial = formatted_time
