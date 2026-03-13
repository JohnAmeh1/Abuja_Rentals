from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Property
from .models import Report
from django.utils import timezone
from django.core.exceptions import ValidationError




class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
        'placeholder': 'Email address'
    }))

    
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Phone number'
        })
    )
    
    
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
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'bio', 'password1', 'password2')
        
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
        
        if commit:
            user.save()
            
            UserProfile.objects.filter(user=user).delete()
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
    
    remember_me = forms.BooleanField(required=False , widget=forms.CheckboxInput(attrs={
        'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500',
        'checked': True
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
        fields = ['phone_number', 'whatsapp_link', 'address', 'bio']
        widgets = {
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

    class Meta:
        model = Property
        fields = [
            "title",
            "description",
            "property_type",
            "purpose",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "price",
            "rent_duration_months",
            "furnished",
            "shared",
            "serviced",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input"}),

            "property_type": forms.Select(attrs={"class": "input"}),
            "purpose": forms.Select(attrs={"class": "input"}),

            "bedrooms": forms.NumberInput(attrs={"class": "input"}),
            "bathrooms": forms.NumberInput(attrs={"class": "input"}),

            "area_sqft": forms.NumberInput(attrs={"class": "input"}),
            "price": forms.NumberInput(attrs={"class": "input"}),

            "rent_duration_months": forms.NumberInput(attrs={"class": "input"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['bedrooms'].required = False
        self.fields['bathrooms'].required = False
        self.fields['area_sqft'].required = False
        
        if self.initial.get('purpose') == 'rent':
            self.fields['rent_duration_display'].initial = '1 Year (Standard)'
            self.fields['rent_duration_display'].widget.attrs['value'] = '1 Year (Standard)'
            if 'rent_duration_months' in self.fields:
                self.fields['rent_duration_months'].initial = 12

        if self.instance and getattr(self.instance, 'rent_duration_months', None):
            if 'rent_duration_months' in self.fields:
                self.fields['rent_duration_months'].initial = self.instance.rent_duration_months
    
    def clean(self):
        cleaned_data = super().clean()
        purpose = cleaned_data.get('purpose')
        
        if purpose == 'rent':
            cleaned_data['rent_duration_display'] = '1 Year (Standard)'
        
        return cleaned_data
    
    def save(self, commit=True):
        property_obj = super().save(commit=False)

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
    
    show_to_agents = forms.BooleanField(
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


class OTPVerificationForm(forms.Form):
    """Form for OTP verification"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-2xl tracking-widest',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'maxlength': '6',
            'autocomplete': 'one-time-code'
        }),
        label='Enter OTP Code'
    )
    
    def clean_otp_code(self):
        """Validate that the OTP code contains only digits"""
        otp_code = self.cleaned_data.get('otp_code', '').strip()
        if not otp_code.isdigit():
            raise ValidationError('OTP code must contain only digits.')
        return otp_code


class ForgotPasswordForm(forms.Form):
    """Form for forgot password email submission"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        label='Email Address'
    )
    
    def clean_email(self):
        """Validate that the user with this email exists"""
        email = self.cleaned_data.get('email')
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError('No account found with this email address.')
        return email


class ForgotPasswordOTPForm(forms.Form):
    """Form for verifying OTP during forgot password"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-2xl tracking-widest',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'maxlength': '6',
            'autocomplete': 'one-time-code'
        }),
        label='Enter OTP Code'
    )
    
    def clean_otp_code(self):
        """Validate that the OTP code contains only digits"""
        otp_code = self.cleaned_data.get('otp_code', '').strip()
        if not otp_code.isdigit():
            raise ValidationError('OTP code must contain only digits.')
        return otp_code


class ResetPasswordForm(forms.Form):
    """Form for resetting password after OTP verification"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        }),
        label='New Password',
        help_text='Password must be at least 8 characters long and contain uppercase, lowercase, and numbers.'
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-8 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        }),
        label='Confirm Password'
    )
    
    def clean(self):
        """Validate password and confirmation match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
            
            # Add Django's password validators
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
        
        return cleaned_data